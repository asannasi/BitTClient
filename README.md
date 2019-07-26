# BitTClient
This is a client that uses the BitTorrent protocol.

I am testing it on Ubuntu downloads. 

Run this program by running client.py

The binary decoder works for well-formed files, and has some assert 
statements for sanity checks, but
it is definitely not the most robust thing. Error checking reminds me 
of parentheses parsers and html parsers. 

I want to also try out making the binary decoder use python decoraters.

This project gave me experience with understanding the existing codebase
since not everything is explained in the tutorial.

The client can successfully get the list of peers from the tracker and then
parse this list to find the peers' IP addresses and port numbers.

The client can now successfully connect to multiple peers and download 
the ubuntu file. It may hang at the end because of a rogue peer, 
but the program will print whether
the file is done downloading and the file is written to disk. The program can 
then be exited safely.

Possible Extensions: add multi-file support. Test with other torrent files.

The client does not support seeding.

Citations:
https://markuseliasson.se/article/bittorrent-in-python/
https://markuseliasson.se/article/introduction-to-asyncio/
https://snarky.ca/how-the-heck-does-async-await-work-in-python-3-5/ 
https://wiki.theory.org/index.php/BitTorrentSpecification