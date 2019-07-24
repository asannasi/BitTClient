import os
from binary_decoder import binary_decoder
import asyncio
from tracker import ask_for_peers, ClientTrackerInfo
import messages
import struct
from downloader import Downloader

async def communicate(reader, writer, trk_info, initial_buffer, downloader, num):
    buffer = initial_buffer
    CHUNK_SIZE = 10*1024
    isDownloading = True
    # list of states
    isChoked = True
    isSending = False
    isWaiting = False
    current_piece = None
    bitfield = None
    while isDownloading:
        try:
            try:
                data = await asyncio.wait_for(reader.read(CHUNK_SIZE), timeout=30)
                #data = await reader.read(CHUNK_SIZE)
            except asyncio.TimeoutError:
                print(num, "Peer Timed Out")
                if current_piece == None:
                    downloader.notify_error(current_piece)
                return


            buffer += data
            
            # parse header
            HEADER_LENGTH = 4
            if len(buffer) > HEADER_LENGTH:
                # > is big-endian, I is signed integer
                message_length = struct.unpack('>I', buffer[0:HEADER_LENGTH])[0]

                if message_length == 0:
                    buffer = buffer[HEADER_LENGTH:]
                # parse message id and message
                elif len(buffer) >= message_length + HEADER_LENGTH:
                    buffer = buffer[HEADER_LENGTH:]
                    # > is big-endian, b is unsighed char
                    message_id = struct.unpack('>b', buffer[0:1])[0]
                    message = buffer[1:message_length+1]
                    #print("message",message)
                    buffer = buffer[message_length:]

                    message_length -= 1 # remove id
                    #print("MI:", message_id)

                    CHOKE_ID = 0
                    UNCHOKE_ID = 1
                    BITFIELD_ID = 5
                    PAYLOAD_ID = 7
                    if message_id == BITFIELD_ID:
                        if(len(message) != message_length):
                            print(len(message), message_length)
                            if current_piece != None:
                                downloader.notify_error(current_piece)
                            return
                        bitfield = await messages.parse_bitfield(message, 
                            message_length)
                        isSending = True
                    elif message_id == CHOKE_ID:
                        isChoked = True
                        print(num, "is choked")
                        if current_piece != None:
                            downloader.notify_error(current_piece)
                            return
                    elif message_id == UNCHOKE_ID:
                        isChoked = False
                        print(num, "is unchoked")
                    elif message_id == PAYLOAD_ID:
                        index, offset, data = await messages.parse_payload(message, message_length)
                        isComplete = downloader.update(current_piece, offset, data)
                        if isComplete:
                            current_piece = None

                        isWaiting = False
                        isSending = True

                    if not isChoked and isSending:
                        piece_index, offset = downloader.inform(bitfield)
                        if piece_index == None:
                            print("no piece index found", piece_index, downloader.is_downloaded())
                            return
                        if piece_index != current_piece:
                            current_piece = piece_index
                            print(num, "is downloading", current_piece)
                        request = await messages.make_request(piece_index, offset)
                        await messages.send_request(reader, writer, request)
                        current_piece = piece_index
                        isWaiting = True
                        isSending = False
                    
        except Exception as e:
            print(e)
            if current_piece:
                downloader.notify_error(current_piece)
            return
        isDownloading = not downloader.is_downloaded()
    print("closing connection")

async def get_peers(all_peers, downloader, torrent_file):
    MAX_PEER_CONNECTIONS = len(all_peers)

    while not downloader.is_downloaded():
        for i in range(MAX_PEER_CONNECTIONS):
            if not downloader.is_downloaded():
                yield all_peers[i]
            await asyncio.sleep(1)
        await asyncio.sleep(60)
        if not downloader.is_downloaded():
            trk_info = await ask_for_peers(torrent_file)
            all_peers = trk_info.peer_list
            MAX_PEER_CONNECTIONS = len(all_peers)
            print("updating peers")
            if downloader.is_waiting():
                print("fixing jam")
                downloader.fix_jam()

async def handle_peer(num, peer, trk_info, downloader):
    assert(len(peer) == 2) # peer should have ip and port
    try:
        reader, writer = await asyncio.open_connection(peer[0], peer[1])
    except Exception:
        print("Connection failed with peer")
        return
    try:
        reply, buffer = await asyncio.wait_for(messages.send_handshake(reader, 
                    writer, trk_info), timeout=20)
        print(num, reply)
    except asyncio.TimeoutError:
        print("Handshake with peer", peer, "timed out")
        return
    peer_info_hash = reply[2]
    peer_id = reply[3]
    try:
        await asyncio.wait_for(messages.send_interested(
            reader, writer,trk_info), timeout=20)
    except asyncio.TimeoutError:
        print("Handshake with peer", peer, "timed out")
    await communicate(reader, writer, trk_info, buffer, downloader, num)
    print("done communicating")


async def main():
    #getcwd() returns the current working directory where the program is running in
    dir_path = os.getcwd() 
    torrent_file = dir_path + "/"+"ubuntu-19.04-desktop-amd64.iso.torrent"
    #torrent_file = dir_path + "/" + "test.torrent"

    # get list of peers from tracker and torrent info
    trk_info = await ask_for_peers(torrent_file)
    assert(type(trk_info) == ClientTrackerInfo)

    # initialize the central downloader
    downloader = Downloader(trk_info)

    # start the peer connections
    tasks = []
    async for peer in get_peers(trk_info.peer_list, downloader, torrent_file):
        if not downloader.is_downloaded():
            task_num = len(tasks)
            print(task_num)
            task = asyncio.get_event_loop().create_task(
                handle_peer(task_num, peer, trk_info, downloader))
            tasks.append(task)
    result = await asyncio.gather(*tasks, return_exceptions=True)
    downloader.write_to_disk()
    print("main is over")

if __name__ == '__main__':       
    loop = asyncio.new_event_loop()
    #asyncio.set_event_loop(loop)
    #result = loop.run_until_complete(main())
    task = loop.create_task(main())
    result = loop.run_until_complete(task)
    print("task complete")