import struct
import asyncio
import bitstring

from downloader import BLOCK_SIZE

# This class is for methods that deal with the messages
# being sent with the protocol

# message info
HEADER_LEN = 4
ID_LEN = 1
REQUEST_LEN = 13

# handshake message info
HANDSHAKE_LEN = 68
HANDSHAKE_HASH_INDEX = 2
HANDSHAKE_PEER_ID_INDEX = 3

PAYLOAD_OFFSET = 8
PAYLOAD_INDEX_INDEX = 0
PAYLOAD_OFFSET_INDEX = 1
PAYLOAD_DATA_INDEX = 2

# message id's
CHOKE_ID = 0
UNCHOKE_ID = 1
INTERESTED_ID = 2
HAVE_ID = 4
BITFIELD_ID = 5
REQUEST_ID = 6
PAYLOAD_ID = 7

# This function parses the payload for the index of the piece,
# the offset for the data, and the data itself
def parse_payload(message, length):
    parts = struct.unpack('II' + str(length-PAYLOAD_OFFSET) + 's', message)
    index = parts[PAYLOAD_INDEX_INDEX]
    offset = parts[PAYLOAD_OFFSET_INDEX]
    data = parts[PAYLOAD_DATA_INDEX]
    return index, offset, data

# This function makes a request message
def make_request(piece_index, offset):
    # > is big endian, I is unsigned integer, b is byte
    return struct.pack('>IbIII', REQUEST_LEN, REQUEST_ID, 
        piece_index, offset, BLOCK_SIZE)

# This function parses the bitfield message to get the bitfield
def parse_bitfield(message, length):
    # > is big endian, <number>s means string array of length <number>
    data = struct.unpack('>' + str(length) + 's', message)[0]
    bitfield = bitstring.BitArray(data)
    return bitfield

# This function gets the id of the message
def parse_id(message):
    assert len(message) == 1
    # > is big-endian, b is unsighed char
    message_id = struct.unpack('>b', message[0:1])[0]
    return message_id

# This function parses the header of a message for the length
def parse_header(header):
    assert len(header) == HEADER_LEN
    # > is big-endian, I is signed integer
    message_length = struct.unpack('>I', header[:HEADER_LEN])[0]
    return message_length

# This function makes an interested message
def make_interested():
    # > is big endian, I is integer, b is signed char
    length = 1
    return struct.pack('>Ib', length, INTERESTED_ID)

# This function makes a handshake message
def make_handshake(client_id, info_hash):
    # > is big endian, B is byte, 19 chars, 8 pad bytes, 20 chars, 20 chars
    return struct.pack('>B19s8x20s20s', 19, b'BitTorrent protocol', 
        info_hash, client_id)

# This function parses a handshake as an array
def parse_handshake(message):
    # > is big endian, B is unsigned char, 19 chars, 
    # 8 pad bytes, 20 chars, 20 chars
    assert len(message) == HANDSHAKE_LEN
    reply = struct.unpack('>B19s8x20s20s', message)
    return reply