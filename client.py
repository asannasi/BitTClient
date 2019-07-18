import os
from binary_decoder import binary_decoder
import aiohttp
from hashlib import sha1
import random
import asyncio
from urllib.parse import urlencode

def find_info_hash(meta_data:bytes) -> bytes:
    editable_data = bytearray(meta_data)
    info_string = b'4:info'
    index = editable_data.index(info_string)
    # skip the 4:info part and just hash the dict, 
    # while making sure to not include the last 'e'
    info = b''.join([editable_data[index+len(info_string):len(editable_data)-1]])
    info_hash = sha1(info).digest()
    return info_hash

def make_peer_id():
    peer_id = ['-PC0001-']
    for _ in range(12):
        peer_id.append(str(random.randint(0,9)))
    peer_id = ''.join(peer_id)
    return peer_id

async def connect(torrent, params, first, client):
    if(first):
        params['event'] = 'started'
    url = torrent['announce'] + '?' + urlencode(params)
    print(url)
    async with client.get(url) as response:
        if response.status != 200:
            raise ConnectionError('Unable to connect to tracker!')
        data = await response.read()
        if b'failure' in data:
            raise ConnectionError("""Requested download is not authorized 
                for use with this tracker""")
        return data


async def main():
    dir_path = os.getcwd() #getcwd() returns the current working directory where the program is running in
    torrent_file = dir_path + "/"+"ubuntu-19.04-desktop-amd64.iso.torrent"

    #open the torrent file as a read only binary file
    with open(torrent_file, 'rb') as f:
        meta_data = f.read()
        torrent = binary_decoder(meta_data)

        # Get params for tracker request
        #print(torrent['info'])
        info_hash = find_info_hash(meta_data)
        peer_id = make_peer_id()
        port = 1025
        size = torrent["info"]["length"]

        params = {
            'info_hash': info_hash,
            'peer_id' : peer_id,
            'port': port,
            'uploaded' : 0,
            'downloaded' : 0,
            'left': size,
            'compact': 1,
        }

        # create an event loop to call an async function from a sync one
        #loop = asyncio.new_event_loop()
        #asyncio.set_event_loop(loop)
        async with aiohttp.ClientSession() as client:
            response = await connect(torrent, params, True, client)
            dec_response = binary_decoder(response)
            print(dec_response)

if __name__ == '__main__':       
    loop = asyncio.new_event_loop()
    #asyncio.set_event_loop(loop)
    #result = loop.run_until_complete(main())
    task = loop.create_task(main())
    result = loop.run_until_complete(task)
