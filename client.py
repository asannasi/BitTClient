import os

def binary_decoder(data:bytes):
    #example data format "5:hello"
    def _bytestring(data, i):
        length = ''
        print("i",i)
        print("b", data[i:i+1])
        while data[i:i+1] != b':':
            length = length + chr(int.from_bytes(data[i:i+1], byteorder="big"))
            i += 1
        length = int(length)
        i += 1 # skip ':' to go to string data
        string = ''
        for j in range(0, length):
            string = string + chr(int.from_bytes(data[i:i+1], byteorder="big"))
            i += 1
        #print(string)
        print("length",length)
        return string, i

    #example data format "i35e"
    def _integer(data, i):
        i += 1 #skip the "i"
        integer = ''
        while data[i:i+1] != b'e':
            integer = integer + chr(int.from_bytes(data[i:i+1], byteorder="big"))
            i += 1
        i += 1 #skip the "e"
        print(integer)
        return integer, i
    
    #in format "l<values>e"
    def _list(data, i):
        print("list")
        i += 1 #skip "l"
        vals = []
        while data[i:i+1] != b'e':
            byte = data[i:i+1]
            if(byte == b'i'):
                element, i = _integer(data, i)
            elif(byte == b'l'):
                element, i = _list(data, i)
            elif(byte == b'd'):
                element, i = _dict(data, i)
            else:
                element, i = _bytestring(data, i)
            vals.append(element)
        i += 1 #skip e
        print(vals)
        return vals, i

    def _dict(data, i):
        print("dict")
        vals = {}
        i += 1 #skip 'd'
        while data[i:i+1] != b'e':
            key, i = _bytestring(data, i)
            byte = data[i:i+1]
            if(byte == b'i'):
                element, i = _integer(data, i)
            elif(byte == b'l'):
                element, i = _list(data, i)
            elif(byte == b'd'):
                element, i = _dict(data, i)
            else:
                element, i = _bytestring(data, i)
            vals[key] = element
            byte = data[i:i+1]
        i += 1 #skip 'e'
        return vals, i
    options = {
        b'i' : _integer,
        b'l' : _list,
        b'd' : _dict
    }
    translations = []
    i = 0
    while i < len(data):
        byte = data[i : i+1]
        print("i2", i)
        if byte in options:
            translation, i = options[byte](data, i)
        else:
            translation, i = _bytestring(data, i)
        translations.append(translation)
        print(translation)
    print(translations)
     

dir_path = os.getcwd() #getcwd() returns the current working directory where the program is running in
torrent_file = dir_path + "/"+"ubuntu-19.04-desktop-amd64.iso.torrent"

#open the torrent file as a read only binary file
with open(torrent_file, 'rb') as f:
    meta = f.read()
    binary_decoder(meta)
    #print(meta)