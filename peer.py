import asyncio
import messages
from downloader import BLOCK_SIZE

TIMEOUT = 30 # timeout for read operation when reading bytes
CHUNK_SIZE = 10*1024 # max threshold for bytes to read at a time


# This class represents the communication between the client and the peer.
# It follows the bittorrent protocol.
class ClientPeerComm:
    # intialize this connection's attributes
    def __init__(self, num, ip_addr, port, client_id, info_hash, downloader):
        self.num = num # client's id for this peer

        # network info for this peer
        self.ip = ip_addr 
        self.port = port

        # client data
        self.client_id = client_id
        self.info_hash = info_hash

        # reference to central downloader
        self.downloader = downloader

        # Fields set during operation
        self.reader = None      # receiving stream
        self.writer = None      # sending stream
        self.buffer = b''       # buffer to store received bytes
        self.bitfield = None    # bitfield of which pieces peer has
        self.index = None       # current piece index downloading
        self.offset = None      # current offset of piece thats downloading

        # states
        self.is_unchoked = True     # whether this connection is choked
        self.is_downloading = False # if the peer is still getting the piece

    # This function connects to the peer to get a reader and writer stream
    async def connect(self):
        try:
            self.reader, self.writer = await asyncio.open_connection(self.ip, self.port)
            return True
        except Exception:
            print("Failed to open a connection with peer", 
                self.num, self.ip, self.port)
        return False

    # This function reads bytes from the given reader. Bytes must be received
    # in a certain amount of time.
    async def read(self):
        recv_bytes = None # initialize to None for error condition
        task = None
        try:
            task = asyncio.create_task(self.reader.read(CHUNK_SIZE))
            recv_bytes = await asyncio.wait_for(task, timeout = TIMEOUT)
        except asyncio.TimeoutError:
            print("Peer", self.num, "timed out receiving messages.")
            task.cancel()
            return None
        except Exception:
            task.cancel()
            return None
        return recv_bytes

    # This function reads from the buffer until the specified length is 
    # achieved or a timeout happens
    async def read_until(self, length):
        while len(self.buffer) < length:
            data = await self.read()
            if data is not None:
                self.buffer += data
            else:
                return False
        return True

    # This function sends the given message to the given writer stream
    async def send(self, message):
        self.writer.write(message)
        await self.writer.drain()

    # This function removes the message from the peer's buffer and returns
    # the removed message
    def remove_message(self, index):
        assert index <= len(self.buffer)
        message = self.buffer[:index]
        self.buffer = self.buffer[index:]
        return message

    # This function "handshakes" with a peer. It sends a handshake 
    # and parses the response
    async def handshake(self):
        try:
            # make the handshake message
            message = messages.make_handshake(self.client_id, self.info_hash)
            # send the handshake message
            await self.send(message)
            # get handshake reply
            assert len(self.buffer) == 0
            if not await self.read_until(messages.HANDSHAKE_LEN):
                return False
            # parse handshake message
            handshake = self.remove_message(messages.HANDSHAKE_LEN)
            handshake = messages.parse_handshake(handshake)
            # check if the handshake's hash matches torrent file hash
            peer_hash = handshake[messages.HANDSHAKE_HASH_INDEX]
            if peer_hash != self.info_hash:
                print("Peer", self.num, "handshake hash did not match.")
                return False
        except:
            return False
        return True

    # This function receives and parses a single message
    async def receive(self):
        try:
            # receive header and parse it for the message length
            if not await self.read_until(messages.HEADER_LEN):
                return False
            header = self.remove_message(messages.HEADER_LEN)
            message_length = messages.parse_header(header)

            # Make sure the message is not a KeepAlive message
            if message_length == 0:
                print("Peer", self.num, "received KeepAlive message")
                return await self.receive()
            # Read the message and parse its ID
            await self.read_until(message_length)
            message_id = messages.parse_id(self.remove_message(messages.ID_LEN))

            # get the message
            message_length -= 1
            message = self.remove_message(message_length)

            # set bitfield
            if message_id == messages.BITFIELD_ID:
                self.bitfield = messages.parse_bitfield(message, message_length)
            # set state to choked (no more requests can be made)
            elif message_id == messages.CHOKE_ID:
                print("Peer", self.num, "is choked")
                self.is_unchoked = False
            # set state to unchoked (requests can be made)
            elif message_id == messages.UNCHOKE_ID:
                self.is_unchoked = True
            elif message_id == messages.HAVE_ID:
                print("Peer", self.num, "received Have message")
            # parse the data and pass it to the downloader
            elif message_id == messages.PAYLOAD_ID:
                index, offset, data = messages.parse_payload(message
                    , message_length)
                self.is_downloading = not self.downloader.update(self.index,offset,
                    data, self.num)
            else:
                print("Peer", self.num, """received unknown message after 
                    with id""", message_id)
                return False
        except:
            return False

        return True

    # This function will send an interested message to the peer, signalling
    # that the client wants to download
    async def send_interested(self):
        message = messages.make_interested()
        await self.send(message)

    # This function receives messages until there are no more messages to 
    # be received
    async def receive_all(self):
        # receive choked, unchoked messages and data
        if not await self.receive():
            return False
        if not self.is_unchoked:
            return False

        # check for remaining messages
        while len(self.buffer) > 0:
            if not await self.receive():
                return False
            if not self.is_unchoked:
                return False
        return True

    # This function creates the connection to the peer according to the
    # bittorrent protocol and downloads pieces specified by the downloader
    async def download(self):
        # connect to peer and get a reader and writer stream
        if not await self.connect():
            return False
        print("Connected to", self.num)

        # perform handshake with peer by sending and receiving
        # handshake messages
        if not await self.handshake():
            return False
        print("Handshaked with", self.num)
            
        # see if there's a bitfield message and parse it
        await self.receive()
        #assert len(self.buffer) == 0

        # send interested message
        await self.send_interested()
        print("Sent interest to", self.num)

        # start downloading according to downloader
        while self.is_unchoked and self.downloader.is_downloading:
            if not await self.receive_all():
                print("Peer", self.num, "had a read error")
                # tell downloader that an error occured when downloading
                if self.is_downloading:
                    self.downloader.notify_error(self.index, self.num)
                return False

            # get the next piece index to request from the downloader
            if not self.is_downloading:
                self.index, self.offset = await self.downloader.inform(self.num, self.bitfield)
                #if no piece is found by downloader, stop
                if self.index is None or self.offset is None:
                    print("Peer", self.num, "could not find a piece")
                    return False

                self.is_downloading = True
                print("Peer", self.num, "downloading piece", self.index)
            else:
                # update the offset if piece is not finished
                self.offset += BLOCK_SIZE

            # send request to the peer
            request = messages.make_request(self.index, self.offset)
            await self.send(request)

        return True