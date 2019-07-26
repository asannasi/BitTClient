import os
import asyncio
import struct

from binary_decoder import binary_decoder
import messages
from downloader import Downloader
from peer import ClientPeerComm
from tracker import ClientTrackerComm

MAX_PEER_CONNECTIONS = 30 # num of connections to open before updating peer list
UPDATE_TIMER = 180 # timer for how long to wait until updating peer list
GEN_TIMER = 10 # timer for how long to wait to generate next peer

# This is a generator that creates peer objects using peer data
async def generate_peers(trk, downloader):
    # get more peers if needed
    while downloader.is_downloading and len(downloader.untouched) > 0:
        # get list of peers with IP addresses and ports
        peer_list = await trk.get_peer_list()
        print("Updated peer list")

        # make sure connections is less than how many peers are available
        num_peers = MAX_PEER_CONNECTIONS
        if MAX_PEER_CONNECTIONS > len(peer_list):
            num_peers = len(peer_list)

        # generate peers
        for i in range(num_peers):
            yield peer_list[i]
            await asyncio.sleep(GEN_TIMER)

        await asyncio.sleep(UPDATE_TIMER) # wait to get ping tracker

# This function parses the torrent file, gets info from the tracker,
# connects to peers, and downloads the requested torrent
async def download_torrent(torrent_file):
    # initialize the client tracker communication
    trk = ClientTrackerComm(torrent_file)

    # initialize the central downloader
    downloader = Downloader(trk)

    # start the peer connections
    # for each peer in the peer list, up to MAX_CONNECTIONS, 
    # connect and download
    #while downloader.is_downloading:
    tasks = []
    async for peer_info in generate_peers(trk, downloader):
        if len(downloader.untouched) > 0:
            # make peer
            peer_num = len(tasks)
            assert(len(peer_info) == 2) # peer should have ip and port
            print("Starting Peer", peer_num)
            peer = ClientPeerComm(peer_num, peer_info[0], peer_info[1], 
                trk.peer_id, trk.info_hash, downloader)

            # start peer connection
            task = asyncio.get_event_loop().create_task(peer.download())
            tasks.append(task)

    # start async tasks
    try:
        result = await asyncio.gather(*tasks)#, return_exceptions= True)
    except Exception as e:
        print("Exception", e)

    if not downloader.is_downloading:
        print("Success")
    else:
        print("File was not downloaded")

# For the main method, create the asynchronous event loop and start
# downloading all torrent files given
if __name__ == '__main__':
    # create the event loop
    loop = asyncio.new_event_loop()

    # make tasks for each torrent file to download
    torrent_file = os.getcwd() + "/"+"ubuntu-19.04-desktop-amd64.iso.torrent"
    task = loop.create_task(download_torrent(torrent_file))

    # start the event loop and download torrents
    result = loop.run_until_complete(task)
    print("Torrent downloading complete.")