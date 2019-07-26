import bitstring
from hashlib import sha1
import os
import asyncio

# remember each block is 2^14 bytes at most
BLOCK_SIZE = 2**14
JAM_TIMEOUT = 10

# This class represents a piece of the file to be downloaded
class Piece:
    def __init__(self, blocks_per_piece, hash):
        self.block_size = BLOCK_SIZE
        self.max_length = blocks_per_piece * self.block_size
        self.data = b''
        self.hash = hash
        self.peer = None

    # set the peer that is allowed to write to this peer
    def set_peer(self, peer):
        self.peer = peer

    # checks if this piece is complete or not
    def is_complete(self):
        return (len(self.data) <= self.max_length and 
            len(self.data) > (self.max_length-self.block_size))

    # gets the offset where the piece data is at
    def get_offset(self):
        return len(self.data)

    # writes the data at the piece's offset if the peer num
    # is allowed to
    def write(self, offset, data, peer_num):
        if peer_num == self.peer:   
            self.data += bytearray(data)
            
            # check hash to see if piece is correct
            if self.is_complete():
                if (sha1(self.data).digest() == self.hash):
                    pass
                else:
                    print("Corrupted piece found")
                    self.data = b''
        else:
            print(peer_num, "tried to write to ", self.peer, "'s piece")

# This class controls which pieces are downloaded by each peer connection
class Downloader:
    def __init__(self, trk):
        # make a list of lists of blocks for pieces of the file
        self.pieces = [Piece(trk.blocks_per_piece, 
            trk.piece_hashes[i]) for i in range(trk.num_pieces)]
        self.untouched = list(range(0, trk.num_pieces))
        self.pending = []

        # make the downloaded file
        try:
            os.remove(trk.file_name)
        except:
            pass
        self.output_file = open(trk.file_name, "ab")

        self.is_downloading = True # state for whether still downloading file

    # This function checks if the download has finished or not
    def _is_downloading(self):
        counter = 0
        for i in range(len(self.pieces)-1, -1, -1):
            if self.pieces[i].is_complete():
                counter += 1
            else:
                return True
        if counter == len(self.pieces):
            return False
        return True

    # This function allows a peer connection to tell the downloader
    # that it is ready to download. This function will return the 
    # piece index and offset the peer connection should request
    async def inform(self, peer_num, bitfield):
        # There might be a jam, so reset pending pieces
        if self.is_downloading and len(self.untouched) == 0:
            await asyncio.sleep(JAM_TIMEOUT)
            if self.is_downloading and len(self.untouched) == 0:
                print("Peer", peer_num, "detected jam")
                if len(self.pending) > 1:
                    index = self.pending.pop(0)
                    self.pieces[index].set_peer(peer_num)
                    return index, self.pieces[index].get_offset()

        has_bitfield = bitfield is not None
        index = None
        offset = None
        # check for untouched pieces for the peer to download
        for i in self.untouched:
            if has_bitfield and bitfield[i]:
                self.pending.append(i)
                self.pieces[i].set_peer(peer_num)
                index = i
                break
        if index is not None:
            self.untouched.remove(index)
            return index, self.pieces[index].get_offset()

        # No pieces found for peer
        return index, offset

    # This function updates the piece with the given data and returns
    # if the piece is completed or not
    def update(self, index, offset, data, peer_num):
        piece = self.pieces[index]
        piece.write(offset, data, peer_num)
        if piece.is_complete():
            if piece.peer == peer_num:
                if index in self.pending:
                    self.pending.remove(index)
                self.is_downloading = self._is_downloading()
                print("Peer" ,peer_num, "finished piece", index)
                if self.is_downloading == False:
                    print("All pieces downloaded. Writing to disk.")
                    self.write_to_disk()
            return True
        return False

    # This function tells the downloader that the piece index must be
    # taken by a new peer
    def notify_error(self, index, peer_num):
        if self.pieces[index].peer == peer_num:
            #self.pieces[index].data = b''
            if index in self.pending:
                self.pending.remove(index)
            self.untouched.append(index)
            self.pieces[index].set_peer(None)

    # This function writes the downloaded data to the output file
    def write_to_disk(self):
        for p in self.pieces:
            self.output_file.write(p.data) 
