from collections import namedtuple
from fcntl import ioctl
from pprint import pprint
import struct
from termios import TIOCGWINSZ


WindowSize = namedtuple('WindowSize', 'row, col, xpixel, ypixel')


def get_winsize():
    fmt = 'HHHH'
    buf = bytearray(struct.calcsize(fmt))
    with open('/dev/tty') as tty:
        ioctl(tty.fileno(), TIOCGWINSZ, buf)
    return WindowSize(*struct.unpack(fmt, buf))


def pp(*poargs, **kwargs):
    pprint(*poargs, width=get_winsize().col, **kwargs)
