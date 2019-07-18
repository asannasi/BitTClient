import os
from binary_decoder import binary_decoder
import asyncio
from tracker import ask_for_peers

async def get_peers(all_peers):
    MAX_PEER_CONNECTIONS = 2
    for i in range(MAX_PEER_CONNECTIONS):
        yield all_peers[i]

async def main():
    dir_path = os.getcwd() #getcwd() returns the current working directory where the program is running in
    torrent_file = dir_path + "/"+"ubuntu-19.04-desktop-amd64.iso.torrent"
    peers = await ask_for_peers(torrent_file)
    async for peer in get_peers(peers):
        print(peer)

if __name__ == '__main__':       
    loop = asyncio.new_event_loop()
    #asyncio.set_event_loop(loop)
    #result = loop.run_until_complete(main())
    task = loop.create_task(main())
    result = loop.run_until_complete(task)
