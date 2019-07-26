import struct
import asyncio
import bitstring

from downloader import BLOCK_SIZE

HEADER_LEN = 4
ID_LEN = 1
REQUEST_LEN = 13

HANDSHAKE_LEN = 68
HANDSHAKE_HASH_INDEX = 2
HANDSHAKE_PEER_ID_INDEX = 3

CHOKE_ID = 0
UNCHOKE_ID = 1
INTERESTED_ID = 2
HAVE_ID = 4
BITFIELD_ID = 5
REQUEST_ID = 6
PAYLOAD_ID = 7

def parse_payload(message, length):
    parts = struct.unpack('II' + str(length - 8) + 's', message)
    index = parts[0]
    offset = parts[1]
    data = parts[2]
    return index, offset, data

def make_request(piece_index, offset):
    # > is big endian, I is unsigned integer, b is byte
    return struct.pack('>IbIII', REQUEST_LEN, REQUEST_ID, 
        piece_index, offset, BLOCK_SIZE)

def parse_bitfield(message, length):
    data = b''
    try:
        # > is big endian, <number>s means string array of length <number>
        data = struct.unpack('>' + str(length) + 's', message)[0]
    except Exception as e:
        print("exception12545", e)
    bitfield = bitstring.BitArray(data)
    return bitfield

def parse_id(message):
    assert len(message) == 1
    # > is big-endian, b is unsighed char
    message_id = struct.unpack('>b', message[0:1])[0]
    return message_id

def parse_header(header):
    assert len(header) == HEADER_LEN
    # > is big-endian, I is signed integer
    message_length = struct.unpack('>I', header[:HEADER_LEN])[0]
    return message_length

def make_interested():
    # > is big endian, I is integer, b is signed char
    length = 1
    return struct.pack('>Ib', length, INTERESTED_ID)

def make_handshake(client_id, info_hash):
    # > is big endian, B is byte, 19 chars, 8 pad bytes, 20 chars, 20 chars
    return struct.pack('>B19s8x20s20s', 19, b'BitTorrent protocol', 
        info_hash, client_id)

def parse_handshake(message):
    # > is big endian, B is unsigned char, 19 chars, 
    # 8 pad bytes, 20 chars, 20 chars
    assert len(message) == HANDSHAKE_LEN
    reply = struct.unpack('>B19s8x20s20s', message)
    return reply