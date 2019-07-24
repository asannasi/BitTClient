import bitstring
from hashlib import sha1
import os

# remember each block is 2^14 bytes at most

class Piece:
    def __init__(self, blocks_per_piece, hash):
        self.block_size = 2**14
        self.max_length = blocks_per_piece * self.block_size
        self.data = b''
        self.hash = hash

    def isComplete(self):
        return (len(self.data) <= self.max_length and 
            len(self.data) > (self.max_length-self.block_size))

    def getOffset(self):
        return len(self.data)

    def write(self, offset, data):
        self.data += bytearray(data)
        if self.isComplete():
            if (sha1(self.data).digest() == self.hash):
                print("this piece is completed")
            else:
                print("corrupted piece")
                self.data = b''

class Downloader:
    def __init__(self, trk_info):
        # make a list of lists of blocks for pieces of the file
        self.pieces = [Piece(trk_info.blocks_per_piece, trk_info.piece_hashes[i]) for i in range(trk_info.num_pieces)]
        #self.pieces = [Piece(trk_info.blocks_per_piece, trk_info.piece_hashes[i]) for i in range(0,100)]
        self.pending = []

        try:
            os.remove(trk_info.file_name)
        except:
            pass
        self.output_file = open(trk_info.file_name, "ab")

    def inform(self, bitfield):
        #assert (len(bitfield) == len(self.pieces))
        for piece_index in range(0, len(self.pieces)):
            piece = self.pieces[piece_index]
            if ((not piece.isComplete()) and (bitfield[piece_index])
                and (piece_index not in self.pending)):
                offset = piece.getOffset()
                self.pending.append(piece_index)
                return piece_index, offset
        '''
        if self.is_downloaded() == False:
            for piece_index in range(0, len(self.pieces)):
                piece = self.pieces[piece_index]
                if ((not piece.isComplete()) and (bitfield)[piece_index]):
                    offset = piece.getOffset()
                    if piece_index in self.pending:
                        self.pending.remove(piece_index)
                        piece.data = b''
                    self.pending.append(piece_index)
                    return piece_index, offset
        '''
        print("no piece found", self.is_downloaded())
        counter = 0
        for p in range(0, len(self.pieces)):
            piece = self.pieces[p]
            if piece.isComplete():
                counter += 1
            else:
                print("piece missing", p)
        print("counter", counter)
        return None, None

    def notify_error(self, index):
        self.pieces[index].data = b''
        self.pending.remove(index)

    def write_to_disk(self):
        for p in self.pieces:
            self.output_file.write(p.data)
        print("written to disk")

    def is_downloaded(self):
        counter = 0
        for p in self.pieces:
            if p.isComplete():
                counter += 1
        if counter == len(self.pieces):
            print("downloaded")
            return True
        return False

    def update(self, index, offset, data):
        self.pieces[index].write(offset, data)
        self.pending.remove(index)
        self.is_downloaded()
        return self.pieces[index].isComplete()

    def is_waiting(self):
        counter = 0
        for p in self.pieces:
            if p.isComplete():
                counter += 1
        return len(self.pieces) - counter == len(self.pending) 

    def fix_jam(self):
        self.pending = []
