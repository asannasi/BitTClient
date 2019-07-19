import os
from binary_decoder import binary_decoder
import asyncio
from tracker import ask_for_peers, TrackerInfo
import struct

async def make_handshake(trk_info):
    # > is big endian, B is byte, 19 chars, 8 pad bytes, 20 chars, 20 chars
    return struct.pack('>B19s8x20s20s', 19, b'BitTorrent protocol', 
        trk_info.info_hash, trk_info.my_peer_id)

async def send_handshake(reader, writer, trk_info):
    message = await make_handshake(trk_info)
    writer.write(message)
    await writer.drain()
    HANDSHAKE_LENGTH = 68
    buffer = b''
    while len(buffer) < HANDSHAKE_LENGTH:
        CHUNK_SIZE = 10*1024 # not sure why this constant has this value
        buffer = await reader.read(CHUNK_SIZE)
    # > is big endian, B is byte, 19 chars, 8 pad bytes, 20 chars, 20 chars
    reply = struct.unpack('>B19s8x20s20s', buffer[:HANDSHAKE_LENGTH])
    return reply

async def get_peers(all_peers):
    MAX_PEER_CONNECTIONS = 2
    for i in range(MAX_PEER_CONNECTIONS):
        yield all_peers[i]

async def main():
    dir_path = os.getcwd() #getcwd() returns the current working directory where the program is running in
    torrent_file = dir_path + "/"+"ubuntu-19.04-desktop-amd64.iso.torrent"
    trk_info = await ask_for_peers(torrent_file)
    assert(type(trk_info) == TrackerInfo)
    counter = 0
    async for peer in get_peers(trk_info.peer_list):
        counter += 1
        assert(len(peer) == 2) # peer should have ip and port
        reader, writer = await asyncio.open_connection(peer[0], peer[1]) #this should be in try catch block
        try:
            reply = await asyncio.wait_for(send_handshake(reader, 
                        writer, trk_info), timeout=100)
            print(counter, reply)
        except asyncio.TimeoutError:
            print("Handshake with peer", peer, "timed out")
        #check if reply is valid
        peer_info_hash = reply[2]
        peer_id = reply[3]
        if peer_info_hash != trk_info.info_hash:
            raise ConnectionError('Handshake info hash does not match with peer')
        

if __name__ == '__main__':       
    loop = asyncio.new_event_loop()
    #asyncio.set_event_loop(loop)
    #result = loop.run_until_complete(main())
    task = loop.create_task(main())
    result = loop.run_until_complete(task)
