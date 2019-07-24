import struct
import asyncio
import bitstring

async def parse_payload(message, length):
    parts = struct.unpack('II' + str(length - 8) + 's', message)
    index = parts[0]
    offset = parts[1]
    data = parts[2]
    return index, offset, data

async def send_request(reader, writer, message):
    writer.write(message)
    await writer.drain()

async def make_request(piece_index, offset):
    REQUEST_SIZE = 2**14
    REQUEST_LENGTH = 13
    REQUEST_ID = 6
    # > is big endian, I is unsigned integer, b is byte
    #print("piece index", piece_index, "offset", offset, REQUEST_SIZE)
    return struct.pack('>IbIII', REQUEST_LENGTH, REQUEST_ID, 
        piece_index, offset, REQUEST_SIZE)

async def parse_bitfield(message, length):
    data = b''
    try:
        # > is big endian, <number>s means string array of length <number>
        data = struct.unpack('>' + str(length) + 's', message)[0]
    except Exception as e:
        print("exception", e)
    bitfield = bitstring.BitArray(data)
    return bitfield

async def make_interested():
    INTERESTED_ID = 2
    # > is big endian, I is integer, b is signed char
    return struct.pack('>Ib', 1, INTERESTED_ID)

async def send_interested(reader, writer, trk_info):
    message = await make_interested()
    writer.write(message)
    await writer.drain()

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
            buffer = await asyncio.wait_for(
                reader.read(CHUNK_SIZE), timeout = 20)
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
    buffer = buffer[HANDSHAKE_LENGTH:] #remove message and return leftover bytes
    return reply, buffer