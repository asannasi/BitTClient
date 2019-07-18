# This function decodes a bencoded array of bytes
def binary_decoder(data: bytes):

    # This function is used to decode byte strings encoded as 
    # "<string length in ascii><string in ascii>"
    # Example data format: "5:hello"
    # Returns the translated bytestring and the index the translation stopped at
    def _bytestring(data, i):

        # Concatenates the ascii chars into a length int until the delimiter b":"
        length = ''
        byte = data[i:i+1]
        while byte != b':':
            char = chr(int.from_bytes(byte, byteorder="big"))
            assert(char in '0123456789')
            length = length + char
            i += 1
            byte = data[i:i+1]
        length = int(length)

        i += 1 # skip ':' to go to the encoded string

        # Concatenates "length" number of ascii chars
        string = ''
        for j in range(0, length):
            string = string + chr(int.from_bytes(data[i:i+1], byteorder="big"))
            i += 1

        return string, i

    # This function is used to decode integers encoded as "i<integer in ascii>e"
    # Example data format: "i35e"
    # Returns the translated integer and the index the translation stopped at
    def _integer(data, i):
        assert(data[i: i+1] == b'i')
        i += 1 #skip the starting "i"

        # Concatenates the ascii chars to form a int
        integer = ''
        byte = data[i:i+1]
        while byte != b'e':
            char = chr(int.from_bytes(byte, byteorder="big"))
            assert(char in '0123456789')
            integer = integer + char
            i += 1
            byte = data[i:i+1]

        i += 1 #skip the "e"

        return integer, i
    
    # This function is used to decode lists encoded as "l<list elements>e"
    # Example data format: "l3:bye5:helloe"
    # Returns the translated list with its translated elements 
    # and the index the translation stopped at
    def _list(data, i):
        assert(data[i: i+1] == b'l')
        i += 1 #skip "l"

        # Translates each element in the list until the list ends
        # An element can be an integer, a bytestring, a list, or a dict
        # Every translated element is added to the list "vals"
        vals = []
        byte = data[i:i+1]
        while byte != b'e':
            if(byte == b'i'):
                element, i = _integer(data, i)
            elif(byte == b'l'):
                element, i = _list(data, i)
            elif(byte == b'd'):
                element, i = _dict(data, i)
            else:
                element, i = _bytestring(data, i)
            vals.append(element)
            byte = data[i:i+1]

        i += 1 #skip "e"

        return vals, i

    # This function is used to decode dictionaries encoded "d<dict elements>e"
    # Example data format: "d3:bye5:helloe" - bye is the key, hello the value
    # Returns the translated dictionary with its translated keys and values 
    # as well as the index the translation stopped at
    # The key is always a bytestring in a well-formed file
    def _dict(data, i):
        assert(data[i: i+1] == b'd')
        i += 1 #skip 'd'

        vals = {}
        byte = data[i:i+1]
        while byte != b'e':
            # translate the key
            key, i = _bytestring(data, i)
            byte = data[i:i+1]

            # translate the value for the key
            if(byte == b'i'):
                element, i = _integer(data, i)
            elif(byte == b'l'):
                element, i = _list(data, i)
            elif(byte == b'd'):
                element, i = _dict(data, i)
            else:
                element, i = _bytestring(data, i)

            vals[key] = element # add the key-value pair
            byte = data[i:i+1]

        i += 1 #skip 'e'

        return vals, i
    
    # This dictionary is used to change which function is used based on the
    # byte found without a long if statement.
    options = {
        b'i' : _integer,
        b'l' : _list,
        b'd' : _dict
    }

    # Main part where the translation is begun
    i = 0
    while i < len(data):
        byte = data[i : i+1]
        if byte in options:
            translation, i = options[byte](data, i)
        else:
            translation, i = _bytestring(data, i)
    return translation