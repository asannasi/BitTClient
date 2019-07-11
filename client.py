import os
from binary_decoder import binary_decoder

dir_path = os.getcwd() #getcwd() returns the current working directory where the program is running in
torrent_file = dir_path + "/"+"ubuntu-19.04-desktop-amd64.iso.torrent"

#open the torrent file as a read only binary file
with open(torrent_file, 'rb') as f:
    meta = f.read()
    binary_decoder(meta)
    #print(meta)