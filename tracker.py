import aiohttp # for making an async client session
from hashlib import sha1 # for making the info hash for which file you want
from random import randint # for generating this client's peer id
from urllib.parse import urlencode # for encoding params into a url
from socket import inet_ntoa # to get ip address from bytes
from struct import unpack # to get port number from bytes
from binary_decoder import binary_decoder # to decode binary file

class ClientTrackerInfo():
    def __init__(self, info_hash, my_peer_id, peer_list):
        self.info_hash = info_hash
        self.my_peer_id = my_peer_id
        self.peer_list = peer_list

# This function finds the info data in bytes given in the torrent file and
# hashes it
def find_info_hash(meta_data:bytes) -> bytes:
    editable_data = bytearray(meta_data)
    info_string = b'4:info'
    assert(info_string in meta_data)
    index = editable_data.index(info_string)
    # skip the 4:info part and just hash the dict, 
    # while making sure to not include the last 'e'
    info=b''.join([editable_data[index+len(info_string):len(editable_data)-1]])
    info_hash = sha1(info).digest()
    return info_hash

# This function generates a random peer id as a bytestring
def make_peer_id() -> str:
    peer_id = [b'-PC0001-']
    for _ in range(12):
        peer_id.append(bytes(str(randint(0,9)), encoding = 'utf-8'))
    peer_id = b''.join(peer_id)
    return peer_id

# This function connects to the tracker with the url given in the
# torrent file and sends given params. The response is returned or
# an error is thrown.
# torrent is the decoded data, params is the params to be sent to the tracker,
# first is whether this is the first time connecting to the tracker, and
# the client is the aiohttp client session.
async def connect(torrent, params, first, client) -> bytes:
    # first represents if this is the first time connecting to the tracker
    if(first):
        params['event'] = 'started'

    url = str(torrent[b'announce'], 'utf-8') + '?' + urlencode(params)
    async with client.get(url) as response:
        if response.status != 200:
            raise ConnectionError('Unable to connect to tracker!')

        data = await response.read()

        if b'failure' in data:
            raise ConnectionError("""Requested download is not authorized 
                for use with this tracker""")

        return data

# This function gets the peers as bytes such that every 6 bytes has the 
# IP address in the first 4 bytes and the port number in the last 2 bytes.
# These bytes are parsed and then returned as a list of peers.
# The param response is the decoded response from the tracker
def find_peers_addr(response) -> list:
    peers = bytearray(response[b'peers'])
    assert(len(peers) % 6 == 0)
    
    peer_list = []
    for i in range(0, len(peers), 6):
        ntwk_info = peers[i:i+6]
        #https://linux.die.net/man/3/inet_ntoa
        ip_addr = inet_ntoa(ntwk_info[:4])
        # This function parses the C-string from the network
        # >H means big-endian unsigned short
        # https://docs.python.org/2/library/struct.html
        port = unpack(">H", ntwk_info[4:])[0]
        peer_list.append((ip_addr, port))
    return peer_list

# This function will parse the torrent binary file to find
# out how to connect to the tracker and then will send a message
# indicating that the client wants to download.
# The tracker's response will then be parsed to find what peers 
# it wants us to download from.
async def ask_for_peers(torrent_file):
    #open the torrent file as a read only binary file
    with open(torrent_file, 'rb') as f:
        meta_data = f.read()
        torrent = binary_decoder(meta_data)

        # Get params for tracker request
        info_hash = find_info_hash(meta_data)
        peer_id = make_peer_id()
        port = 1025
        size = torrent[b"info"][b"length"]  
        params = {
            'info_hash': info_hash,
            'peer_id' : peer_id,
            'port': port,
            'uploaded' : 0,
            'downloaded' : 0,
            'left': size,
            'compact': 1,
        }

        #start the client session
        async with aiohttp.ClientSession() as client:
            # connect to tracker and get response
            response = await connect(torrent, params, True, client)
            # parse response to get peers
            decoded_response = binary_decoder(response)
            peer_list = find_peers_addr(decoded_response)
            resp = ClientTrackerInfo(info_hash, peer_id, peer_list)
            return resp