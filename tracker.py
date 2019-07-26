import aiohttp # for making an async client session
from hashlib import sha1 # for making the info hash for which file you want
from random import randint # for generating this client's peer id
from urllib.parse import urlencode # for encoding params into a url
from socket import inet_ntoa # to get ip address from bytes
from struct import unpack # to get port number from bytes
import math # to find out how many pieces there are 

from binary_decoder import binary_decoder # to decode binary file
from downloader import BLOCK_SIZE

PORT = 1025
HASH_LENGTH = 20

class ClientTrackerComm:
    def __init__(self, torrent_file):
        self._parse_torrent_file(torrent_file)
        self.num_pieces = math.ceil(self.length/self.piece_length)
        self.blocks_per_piece = math.ceil(self.piece_length/BLOCK_SIZE)

        # Get this connection's details
        self.peer_id = ClientTrackerComm.make_peer_id()
        self.port = PORT

    # This function finds the info data in bytes given in the torrent file and
    # hashes it
    @staticmethod
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
    @staticmethod
    def make_peer_id() -> str:
        peer_id = [b'-PC0001-']
        for _ in range(12):
            peer_id.append(bytes(str(randint(0,9)), encoding = 'utf-8'))
        peer_id = b''.join(peer_id)
        return peer_id

    # This function parses the torrent file and populates the class fields
    def _parse_torrent_file(self, torrent_file):
        #open the torrent file as a read only binary file
        with open(torrent_file, 'rb') as f:
            meta_data = f.read()
            self.torrent = binary_decoder(meta_data)

            # get values from torrent dict
            self.info_hash = ClientTrackerComm.find_info_hash(meta_data)
            self.piece_length = int(self.torrent[b'info'][b'piece length'])
            self.length = int(self.torrent[b'info'][b'length'])
            self.file_name = self.torrent[b'info'][b'name']

            # Hashes are stored in 20 byte chunks in the torrent file
            # and must be parsed from binary format
            hashes = self.torrent[b'info'][b'pieces']
            self.piece_hashes = []
            for i in range(0, len(hashes), HASH_LENGTH):
                self.piece_hashes.append(hashes[i:i+HASH_LENGTH])

    # Messages to tracker has parameters which this function creates
    # as a dict
    def make_params(self):
        # Get params for tracker request
        params = {
            'info_hash': self.info_hash,
            'peer_id' : self.peer_id,
            'port': self.port,
            'uploaded' : 0,
            'downloaded' : 0,
            'left': self.length,
            'compact': 1,
        }
        return params

    # This function connects to the tracker with the url given in the
    # torrent file and sends given params. The response is returned or
    # an error is thrown.
    # torrent is the decoded data, params is the params to be sent to the tracker,
    # first is whether this is the first time connecting to the tracker, and
    # the client is the aiohttp client session.
    async def send(self, first) -> bytes:
        #start the client session
        async with aiohttp.ClientSession() as client:
            # connect to tracker and get response
            params = self.make_params()
            # first represents if this is the first time connecting to the tracker
            if(first):
                params['event'] = 'started'

            url = str(self.torrent[b'announce'], 'utf-8') + '?' + urlencode(params)
            print("Connecting to", url)
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
    @staticmethod
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

    # This function returns a list of peers given by the tracker with IP
    # address and port
    async def get_peer_list(self):
        response = await self.send(True)
        # parse response to get peers
        decoded_response = binary_decoder(response)
        peer_list = ClientTrackerComm.find_peers_addr(decoded_response)
        return peer_list

