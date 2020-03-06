# BitTClient

This is a client Python program that uses the BitTorrent protocol to download
files.

When given a torrent file, in the client.py main method, it will connect
to the tracker and get a list of peers to download from. Then peer connections
will open to a subset of peers in that list and start downloading the file in
chunks. It may hang at the end because of a rogue peer, 
but the program will print whether
the file is done downloading and the file is written to disk. The program can 
then be exited safely.

## client.py

This is the main callable script. It will use the hard-coded torrent file to
connect to the tracker. The tracker keeps track of which peers are seeding
the file. This connection is represented as the class ClientTrackerComm in the
tracker.py file. The file information returned by the tracker will be given to
the Downloader class in downloader.py to figure out how many pieces and blocks need
to be downloaded. Then an async for loop will create ClientPeerComm's which are
connections to peers defined in peer.py. The async for loop uses peers yielded by 
the generator generate_peers(). Downloads will start for each peer connection
and async loop will wait until all pieces are downloaded.

## tracker.py

Connects to the tracker after decoding the torrent binary file
and gets a list of peer IP and ports.

## downloader.py

The Downloader class is a centralized coordinator for the async tasks that
connect to peers. It tells which connection to download which piece of the file 
so that all connections are utilized efficiently. The downloader class also
verifies if the downloaded piece's hash matches the hash given by the tracker.

## binary_decoder.py
The binary decoder works for well-formed files, and has some assert 
statements for sanity checks. It decodes binary files in the Bittorrent spec.

## messages.py
Anytime a message needs to be sent or received, their structure is defined
in this file.

## Possible Extensions
1. add multi-file support
1. Test with other torrent files.
1. Seeding

## Citations
1. https://markuseliasson.se/article/bittorrent-in-python/
1. https://markuseliasson.se/article/introduction-to-asyncio/
1. https://snarky.ca/how-the-heck-does-async-await-work-in-python-3-5/ 
1. https://wiki.theory.org/index.php/BitTorrentSpecification
