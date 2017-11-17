"""Debug helpers."""

# TODO: Refactor out of jirax.

from collections import namedtuple
from fcntl import ioctl
from pprint import pprint
import struct
from termios import TIOCGWINSZ


WindowSize = namedtuple('WindowSize', 'row, col, xpixel, ypixel')
"""Detected window size."""


def get_winsize():
    """Get window size of the current tty.

    :return: the window size.
    :rtype: `WindowSize`
    """
    fmt = 'HHHH'
    buf = bytearray(struct.calcsize(fmt))
    with open('/dev/tty') as tty:
        ioctl(tty.fileno(), TIOCGWINSZ, buf)
    return WindowSize(*struct.unpack(fmt, buf))


def pp(*poargs, **kwargs):
    """Pretty-print to the width of the tty.

    Accept same arguments as the `~pprint.pprint()` function.
    """
    pprint(*poargs, width=get_winsize().col, **kwargs)
