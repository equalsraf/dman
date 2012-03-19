# coding: utf-8

"""A netstring handler module
http://cr.yp.to/proto/netstrings.txt
[len]":"[string]","

This modules provides two methods for simple encoding and
decoding netstrings

>>> encode('hello')
'5:hello,'
>>> decode('5:hello,')
'hello'
>>> decode('96:http://1.bp.blogspot.com/-1qAfAl__h58/TXoZ_-4ZiMI/AAAAAAAAAOs/jsPA-xb3Yvs/s1600/luxury-car-6.jpg,')
'http://1.bp.blogspot.com/-1qAfAl__h58/TXoZ_-4ZiMI/AAAAAAAAAOs/jsPA-xb3Yvs/s1600/luxury-car-6.jpg'
"""

from __future__ import print_function, unicode_literals
from __future__ import absolute_import, division

ASCII_ZERO = int('0')


def enum(*args, **kwargs):
    """Sweet trick for enums in python
    
    ex:
        >> enum('NORTH', 'SOUTH', 'EAST', 'WEST')
        >> enum(NORTH=1, SOUTH=2, EAST=3, WEST=4)

    Make no assumptions about the value of the enumerate
    as it will most likely be an object()
    """

    enums = dict(zip(args, args ), **kwargs)
    return type(str('Enum'), (), enums)

STATE = enum('READ_FIRST_DIGIT', 'READ_LENGTH_DIGIT', 
            'READ_BYTES', 'READ_COMMA', 'READ_COLON', 'FINISHED', 'ERROR')


class NetStringError(Exception):
    "Base Netstring error exception"
    pass
class InvalidLengthField(NetStringError):
    "There is invalid input in the lenght field"
    pass
class InvalidTerminatingCharacter(NetStringError):
    "Instead of the string terminating character we got something else"
    pass
class InvalidLenghtTerminator(NetStringError):
    "Instead of the lenght terminating character we got something else"
    pass


class NetStringReader:
    """
    A class to read netstrings from a socket-like object
    """

    def __init__(self):
        """A Netstring reader

        * sock: is a file like object, i.e. it has a read() method
        """
        self.bytes_left = 0
        self.__buffer = b''
        self.state = STATE.READ_FIRST_DIGIT

    def reset(self):
        "Reset the reader to its initial state"
        self.bytes_left = 0
        self.__buffer = b''
        self.state = STATE.READ_FIRST_DIGIT

    def __read_first_digit(self, data):
        """Handle READ_FIRST_DIGIT state
        
        This method reads _only_ the first input byte
        - If the byte is '0' the next state is READ_COLON
        - If the byte an ascii digit 1..9 the next state is READ_LENGTH_DIGIT
        - Any other case is an error

        The return value is 1(the number of consumed bytes) or 0 if data is empty
        """
        if not data:
            return 0

        if data[0] >= '1' and data[0] <= '9':
            self.bytes_left = int(data[0]) - ASCII_ZERO
        elif data[0] == '0':
            self.bytes_left = 0
            self.state = STATE.READ_COLON
            return 1
        else:
            self.state = STATE.ERROR
            raise InvalidLengthField(data[0])

        self.state = STATE.READ_LENGTH_DIGIT
        return 1

    def __read_length_digit(self, data):
        """Handle READ_LENGTH_DIGIT state
        
        Returns the number of bytes consumed
        """
        if not data:
            return 0

        if data[0] == ':':
            self.state = STATE.READ_BYTES
            self.__buffer = b''
            return 1
        if data[0] < '0' or data[0] > '9':
            self.state = STATE.ERROR
            raise InvalidLengthField(data[0])

        self.bytes_left = self.bytes_left*10 + (int(data[0]) -ASCII_ZERO )
        return 1

    def __read_bytes(self, data):
        """Handle the READ_BYTES state"""
        if not data:
            return 0

        read_bytes = data[:self.bytes_left]
        self.bytes_left -= len(read_bytes)
        self.__buffer += read_bytes

        if self.bytes_left == 0:
            self.state = STATE.READ_COMMA
        return len(read_bytes)

    def __read_comma(self, data):
        """Handle the READ_COMMA state"""
        if not data:
            return 0

        if data[0] != ',':
            self.state = STATE.ERROR
            raise InvalidTerminatingCharacter(data[0])
        self.state = STATE.FINISHED
        return 1

    def __read_colon(self, data):
        """Handle the READ_COLON state"""
        if not data:
            return 0

        if data[0] != ':':
            self.state = STATE.ERROR
            raise InvalidLenghtTerminator(data[0])
        self.state = STATE.READ_COMMA
        return 1

    def __feed_cycle(self, data):
        """Parse the given data and if
        needed, transition state

        * Returns the amount of bytes consumed from the given buffer
        """
        if self.state == STATE.READ_FIRST_DIGIT:
            return self.__read_first_digit(data)
        elif self.state == STATE.READ_LENGTH_DIGIT:
            return self.__read_length_digit(data)
        elif self.state == STATE.READ_BYTES:
            return self.__read_bytes(data)
        elif self.state == STATE.READ_COMMA:
            return self.__read_comma(data)
        elif self.state == STATE.READ_COLON:
            return self.__read_colon(data)

    def feedUntilDone(self, data):
        """Feed the given data into the netstring parser

        The method consumes all bytes UNTIL a netstring can be parsed
        successfully.
        
        Returns the ammount of bytes consumed"""

        if not isinstance(data, str):
            data = bytes(data)

        done = 0
        while done < len(data) and self.state != STATE.FINISHED:
            done += self.__feed_cycle(data[done:])

        return done

    def feed(self, data):
        """Feed data to the parser
        
        see stringReceived()"""

        if not isinstance(data, str):
            data = bytes(data)

        done = 0

        while done < len(data):
            done += self.feedUntilDone(data[done:])
            if self.state == STATE.FINISHED:
                self.stringReceived(self.__buffer)
                self.reset()

    def stringReceived(self, string):
        "Override this function to handle new strings"
        print(string)

    @staticmethod
    def decode(data):
        """Parse a single netstring and return the enclosed string
        
        >>> NetStringReader.decode(b'5:hello,')
        'hello'
        >>> NetStringReader.decode(b'0:,')
        ''
        """
        reader = NetStringReader()

        done = reader.feedUntilDone(data)
        if reader.state != STATE.FINISHED or done != len(data):
            raise NetStringError('Unable to decode netstring')

        result = reader.__buffer
        return result


decode = NetStringReader.decode

def encode(string, encoding='utf-8'):
    """Encode string s as a netstring
    
    * The given string is not converted, the bytes are inserted
      into the netstring and the binary output will be identicall
    * If the given string is a unicode object then
      it will be converted using the given encoding.

    >>> encode(b'outstanding')
    '11:outstanding,'
    >>> encode(b'')
    '0:,'
    """

    if len(string) == 0:
        return b'0:,'
        
    if isinstance(string, unicode):
        string = string.encode(encoding)

    length = len(string)

    result = str(length) + b':' + string + b','

    return result

if __name__ == '__main__':
    import doctest
    doctest.testmod()


