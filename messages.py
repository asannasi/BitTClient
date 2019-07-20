import struct
import asyncio

async def send_interested(reader, writer, trk_info):
    message = await make_interested()
    writer.write(message)
    await writer.drain()

async def make_interested():
    INTERESTED_ID = 2
    # > is big endian, I is integer, b is signed char
    return struct.pack('>Ib', 1, INTERESTED_ID)

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
        try:
            buffer = await asyncio.wait_for(reader.read(CHUNK_SIZE), timeout = 20)
        except asyncio.TimeoutError:
            print("Timeout")
    # > is big endian, B is unsigned char, 19 chars, 
    # 8 pad bytes, 20 chars, 20 chars
    reply = struct.unpack('>B19s8x20s20s', buffer[:HANDSHAKE_LENGTH])
    
    #check if reply is valid
    peer_info_hash = reply[2]
    peer_id = reply[3]
    if peer_info_hash != trk_info.info_hash:
        raise ConnectionError('Handshake info hash doesnt match with', peer_id)
    return reply