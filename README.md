# BitTClient
This is a client that uses the BitTorrent protocol.

I am testing it on ubuntu downloads. 

Currently the binary decoder works, so the torrent file is succesfully 
converted to a python data structure.

The binary decoder works for well-formed files, and has some assert 
statements for sanity checks, but
it is definitely not the most robust thing. Error checking reminds me 
of parentheses parsers and html parsers. 

I want to also try out making the binary decoder use python decoraters.

The binary decoder does not currently output binary strings.

Citations:
https://markuseliasson.se/article/bittorrent-in-python/
https://markuseliasson.se/article/introduction-to-asyncio/
https://snarky.ca/how-the-heck-does-async-await-work-in-python-3-5/ 
https://wiki.theory.org/index.php/BitTorrentSpecification