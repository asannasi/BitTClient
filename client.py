import os
from binary_decoder import binary_decoder
import asyncio
from tracker import ask_for_peers, ClientTrackerInfo
import messages
import struct

async def communicate(reader, writer, trk_info):
    buffer = b''
    communicating = True
    while communicating:
        try:
            data = await asyncio.wait_for(reader.read(), timeout=200)
        except asyncio.TimeoutError:
            print("Peer Timed Out")
            return
        # not sure why this constant has this value
        # also referenced in messages.py
        CHUNK_SIZE = 10*1024
        buffer += data
        header_length = 4
        if len(buffer) > header_length:
            # > is big-endian, I is signed integer
            message_length = struct.unpack('>I', buffer[0:header_length])[0]
            if len(buffer) >= message_length:
                # > is big-endian, b is unsighed char
                message_id = struct.unpack('>b', buffer[4:5])[0]
                print(message_id)
                BITFIELD_ID = 5
                if message_id == BITFIELD_ID:
                    print(buffer[:header_length+message_length])
                buffer = buffer[header_length + message_length:]

async def get_peers(all_peers):
    MAX_PEER_CONNECTIONS = 2
    for i in range(MAX_PEER_CONNECTIONS):
        yield all_peers[i]
        await asyncio.sleep(1)

async def peer_stuff(num, peer, trk_info):
    assert(len(peer) == 2) # peer should have ip and port
    try:
        reader, writer = await asyncio.open_connection(peer[0], peer[1])
    except Exception:
        print("Connection failed with peer")
        return
    try:
        reply = await asyncio.wait_for(messages.send_handshake(reader, 
                    writer, trk_info), timeout=20)
        print(num, reply)
    except asyncio.TimeoutError:
        print("Handshake with peer", peer, "timed out")
        return
    peer_info_hash = reply[2]
    peer_id = reply[3]
    try:
        await asyncio.wait_for(messages.send_interested(reader, writer,
                                trk_info), timeout=20)
    except asyncio.TimeoutError:
        print("Handshake with peer", peer, "timed out")
    await communicate(reader, writer, trk_info)


async def main():
    #getcwd() returns the current working directory where the program is running in
    dir_path = os.getcwd() 
    torrent_file = dir_path + "/"+"ubuntu-19.04-desktop-amd64.iso.torrent"
    trk_info = await ask_for_peers(torrent_file)
    assert(type(trk_info) == ClientTrackerInfo)
    tasks = []
    async for peer in get_peers(trk_info.peer_list):
        print(len(tasks))
        task = asyncio.get_event_loop().create_task(peer_stuff(len(tasks), peer, trk_info))
        tasks.append(task)

    result = await asyncio.gather(*tasks, return_exceptions=True)

if __name__ == '__main__':       
    loop = asyncio.new_event_loop()
    #asyncio.set_event_loop(loop)
    #result = loop.run_until_complete(main())
    task = loop.create_task(main())
    result = loop.run_until_complete(task)