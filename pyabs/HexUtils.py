# -*- coding: utf-8-unix -*-
# Copyright (c) 2014 Pierre-François Gomez <pef.gomez@gmail.com>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import itertools


class HexUtilsError(Exception):
    """Base class for HexUtils errors"""
    pass


class HexUtilsInputSizeError(HexUtilsError):
    """Raised when an input is not the expected size."""
    pass


class HexUtilsParamError(HexUtilsError):
    """Raised when a parameter has a forbidden value."""
    pass


def hex_str_to_u8(hex_str):
    """Converts an hexadecimal string into a list of the corresponding bytes (8 bits).

Usage :

>>> hex_str_to_u8('') == []
True

>>> hex_str_to_u8('CA') == [0xca]
True

>>> hex_str_to_u8('CAFE') == [0xca, 0xfe]
True

>>> hex_str_to_u8('C')
Traceback (most recent call last):
...
HexUtilsInputSizeError

>>> hex_str_to_u8('CAF')
Traceback (most recent call last):
...
HexUtilsInputSizeError
    """
    if len(hex_str) % 2 != 0:
        raise HexUtilsInputSizeError
    else:
        return [int(hex_str[i:i + 2], 16)
                for i in range(0, len(hex_str), 2)]


def hex_str_to_u16(hex_str):
    """Converts an hexadecimal string into a list of the corresponding 16-bits words.

Usage :

>>> hex_str_to_u16('') == []
True

>>> hex_str_to_u16('CAFE') == [0xcafe]
True

>>> hex_str_to_u16('CAFEDECA') == [0xcafe, 0xdeca]
True

>>> hex_str_to_u16('CAF')
Traceback (most recent call last):
...
HexUtilsInputSizeError

>>> hex_str_to_u16('CAFEDE')
Traceback (most recent call last):
...
HexUtilsInputSizeError
    """
    if len(hex_str) % 4 != 0:
        raise HexUtilsInputSizeError
    else:
        return [int(hex_str[i:i + 4], 16)
                for i in range(0, len(hex_str), 4)]


def hex_str_to_u32(hex_str):
    """Converts an hexadecimal string into a list of the corresponding 32-bits integers.

Usage :

>>> hex_str_to_u32('') == []
True

>>> hex_str_to_u32('CAFEDECA') == [0xcafedeca]
True

>>> hex_str_to_u32('CAFEDECADEADBEEF') == [0xcafedeca, 0xdeadbeef]
True

>>> hex_str_to_u32('CAFEDEC')
Traceback (most recent call last):
...
HexUtilsInputSizeError

>>> hex_str_to_u32('CAFEDECADEAD')
Traceback (most recent call last):
...
HexUtilsInputSizeError
    """
    if len(hex_str) % 8 != 0:
        raise HexUtilsInputSizeError
    else:
        return [int(hex_str[i:i + 8], 16)
                for i in range(0, len(hex_str), 8)]


def hex_str_to_u64(hex_str):
    """Converts an hexadecimal string into a list of the corresponding 64-bits integers.

Usage :

>>> hex_str_to_u64('') == []
True

>>> hex_str_to_u64('CAFEDECADEADBEEF') == [0xcafedecadeadbeef]
True

>>> hex_str_to_u64('CAFEDECADEADBEEF123456789ABCDEF0') == [0xcafedecadeadbeef, 0x123456789abcdef0]
True

>>> hex_str_to_u64('CAFEDECADEADBEE')
Traceback (most recent call last):
...
HexUtilsInputSizeError

>>> hex_str_to_u64('CAFEDECADEADBEEF12345678')
Traceback (most recent call last):
...
HexUtilsInputSizeError
    """
    if len(hex_str) % 16 != 0:
        raise HexUtilsInputSizeError
    else:
        return [int(hex_str[i:i + 16], 16)
                for i in range(0, len(hex_str), 16)]

# TODO: to_byte_addr renamed to_bitwise_addr
def to_bitwise_addr(offset):
    """Converts an offset into a ''bitwise address''.

The HexUtils package makes use of the notions of a ''bitwise address'' vs an ''offset''.

Consider a given binary data input : it can be considered as a string of bits, or more
conventionally as a list of bytes.

The ''offset'' 0 corresponds to the most significant bit (bit 0) of the first byte (byte 0)
=> the corresponding ''bitwise address'' is (0, 0) :
>>> to_bitwise_addr(0)
(0, 0)

The ''offset'' 7 corresponds to the least significant bit (bit 7) of the first byte (byte 0)
=> the corresponding ''bitwise address'' is (0, 7)
>>> to_bitwise_addr(7)
(0, 7)

The ''offset'' 8 corresponds to the most significant bit (bit 0) of the second byte (byte 1)
=> the corresponding ''bitwise address'' is (1, 0)
>>> to_bitwise_addr(8)
(1, 0)

The ''offset'' 23 corresponds to the least significant bit (bit 7) of the second byte (byte 1)
=> the corresponding ''bitwise address'' is (1, 7)
>>> to_bitwise_addr(15)
(1, 7)

etc...
    """
    return offset // 8, offset % 8


# TODO: to_bitwise_addr renamed to_offset
def to_offset(byte_addr, byte_offset):
    """Converts a ''bitwise address'' into an offset.

The HexUtils package makes use of the notions of a ''bitwise address'' vs an ''offset''.

Consider a given binary data input : it can be considered as a string of bits, or more
conventionally as a list of bytes.

The ''offset'' 0 corresponds to the most significant bit (bit 0) of the first byte (byte 0)
=> the corresponding ''bitwise address'' is (0, 0) :
>>> to_offset(0, 0)
0

The ''offset'' 7 corresponds to the least significant bit (bit 7) of the first byte (byte 0)
=> the corresponding ''bitwise address'' is (0, 7)
>>> to_offset(0, 7)
7

The ''offset'' 8 corresponds to the most significant bit (bit 0) of the second byte (byte 1)
=> the corresponding ''bitwise address'' is (1, 0)
>>> to_offset(1, 0)
8

The ''offset'' 15 corresponds to the least significant bit (bit 7) of the second byte (byte 1)
=> the corresponding ''bitwise address'' is (1, 7)
>>> to_offset(1, 7)
15

etc...
    """
    return byte_addr * 8 + byte_offset


def to_u16(u8_0, u8_1):
    """Converts the two given bytes into a 16-bits word.
>>> to_u16(0xca, 0xfe) == 0xcafe
True
    """
    return sum([(u8_0 << 8),
                u8_1])


def to_u32(u8_0, u8_1, u8_2, u8_3):
    """Converts the four given bytes into a 32-bits integer.
>>> to_u32(0xca, 0xfe, 0xde, 0xca) == 0xcafedeca
True
    """
    return sum([(u8_0 << 24),
                (u8_1 << 16),
                (u8_2 << 8),
                u8_3])


def to_u64(u8_0, u8_1, u8_2, u8_3, u8_4, u8_5, u8_6, u8_7):
    """Converts the height given bytes into a 64-bits integer.
>>> to_u64(0xca, 0xfe, 0xde, 0xca, 0xde, 0xad, 0xbe, 0xef) == 0xcafedecadeadbeef
True
    """
    return sum([(u8_0 << 56),
                (u8_1 << 48),
                (u8_2 << 40),
                (u8_3 << 32),
                (u8_4 << 24),
                (u8_5 << 16),
                (u8_6 << 8),
                u8_7])


def left_shift_64(u64, shift):
    """Left-Shift a 64-bits integer and returns both the discarded and retained bits as a couple.

Usage :

>>> left_shift_64(0xFFFFFFFFFFFFFFFF, 0) == (0x0000000000000000, 0xFFFFFFFFFFFFFFFF)
True

>>> left_shift_64(0xFFFFFFFFFFFFFFFF, 1) == (0x0000000000000001, 0xFFFFFFFFFFFFFFFE)
True

>>> left_shift_64(0xFFFFFFFFFFFFFFFF, 2) == (0x0000000000000003, 0xFFFFFFFFFFFFFFFC)
True

>>> left_shift_64(0xFFFFFFFFFFFFFFFF, 3) == (0x0000000000000007, 0xFFFFFFFFFFFFFFF8)
True

>>> left_shift_64(0xFFFFFFFFFFFFFFFF, 4) == (0x000000000000000F, 0xFFFFFFFFFFFFFFF0)
True

>>> left_shift_64(0xFFFFFFFFFFFFFFFF, 60) == (0x0FFFFFFFFFFFFFFF, 0xF000000000000000)
True

>>> left_shift_64(0xFFFFFFFFFFFFFFFF, 61) == (0x1FFFFFFFFFFFFFFF, 0xE000000000000000)
True

>>> left_shift_64(0xFFFFFFFFFFFFFFFF, 62) == (0x3FFFFFFFFFFFFFFF, 0xC000000000000000)
True

>>> left_shift_64(0xFFFFFFFFFFFFFFFF, 63) == (0x7FFFFFFFFFFFFFFF, 0x8000000000000000)
True

>>> left_shift_64(0xFFFFFFFFFFFFFFFF, 64) == (0xFFFFFFFFFFFFFFFF, 0x0000000000000000)
True

>>> left_shift_64(0xFFFFFFFFFFFFFFFF, 65) == (0xFFFFFFFFFFFFFFFF, 0x0000000000000000)
Traceback (most recent call last):
...
HexUtilsParamError
    """
    if 0 <= shift <= 64:
        l_discarded_mask = (0xFFFFFFFFFFFFFFFF << (64 - shift)) & 0xFFFFFFFFFFFFFFFF
        l_discarded = (u64 & l_discarded_mask) >> (64 - shift)
        l_retained = (u64 << shift) & 0xFFFFFFFFFFFFFFFF
        return l_discarded, l_retained
    else:
        raise HexUtilsParamError


def cross_byte_left_shift(data, shift):
    """Left-shift a whole list of bytes.
    Each discarded MSB of a byte ends up as the MSB of the previous byte in the list.
    Each discarded MSB of the first byte is lost.

Example :
>>> l_tests = [('',                                   0, ''),
...            ('',                                   1, ''),
...            ('C3',                                 1, '86'),
...            ('C3C3',                               1, '8786'),
...            ('C3C3C3',                             1, '878786'),
...            ('C3C3C3C3',                           1, '87878786'),
...            ('C3C3C3C3C3',                         1, '8787878786'),
...            ('C3C3C3C3C3C3C3',                     1, '87878787878786'),
...            ('C3C3C3C3C3C3C3C3',                   1, '8787878787878786'),
...            ('C3C3C3C3C3C3C3C3C3',                 1, '878787878787878786'),
...            ('C3C3C3C3C3C3C3C3C3C3C3C3C3C3C3',     1, '878787878787878787878787878786'),
...            ('C3C3C3C3C3C3C3C3C3C3C3C3C3C3C3C3',   1, '87878787878787878787878787878786'),
...            ('C3C3C3C3C3C3C3C3C3C3C3C3C3C3C3C3C3', 1, '8787878787878787878787878787878786'),
...            ]
>>> [cross_byte_left_shift(hex_str_to_u8(l_data), l_shift) == hex_str_to_u8(l_result)
...  for (l_data, l_shift, l_result) in l_tests]
[True, True, True, True, True, True, True, True, True, True, True, True, True]
    """
    # IMPLEMENTATION NOTE :
    # I assumed it's faster to shift the bytes by grouping them in u64 (less shift operations).
    # However, I have to first group them, then split them back after the shift.
    # This might just be over-optimization : just shifting each byte would simplify the
    # implementation, and might not be that much slower => to be benchmarked.

    # First turn the data into a list of u64, right-padding the last one if necessary
    l_length = len(data)
    l_nb_u64s = (l_length + 7) // 8
    l_u64s = [to_u64(*[data[l_u64_idx + i] if (l_u64_idx + i) < l_length else 0x00
                       for i in range(8)])
              for l_u64_idx in [8 * j for j in range(l_nb_u64s)]]

    # Left-shift each of the u64, collecting the (discarded, retained) tuples
    l_shifted_tuples = [left_shift_64(l_u64, shift) for l_u64 in l_u64s]

    # Add an extra (0, 0) tuple to simplify the next step
    l_shifted_tuples.append((0, 0))

    # Binary-OR each "retained" with its right-most "discarded" (or with 0 for the last one,
    # see previous step)
    l_shifted_u64s = [(d | r) for (d, r) in zip([t[0] for t in l_shifted_tuples[1:]],
                                                [t[1] for t in l_shifted_tuples])]

    # Split the data back into a list of u8
    l_shifted_data_u8 = list(itertools.chain.from_iterable(
        [[(l_u64 & (0xFF << (8 * (8 - 1 - i)))) >> (8 * (8 - 1 - i))
          for i in range(8)]
         for l_u64 in l_shifted_u64s]
    ))

    # Finally, remove the extra bytes we may have added when right-padding (see first step)
    l_result = l_shifted_data_u8[:l_length]
    return l_result


def extract(data, offset, width):
    """Extract WIDTH bits of DATA (a list of bytes), starting at OFFSET.
    Returns a list of bytes containing only the corresponding bits.
    The bit at OFFSET ends up as the first bit of the returned list of bytes.
    If WIDTH was not a multiple of 8, then the last byte of the returned list will be right-padded
    with enough 0-bits to fill it.

Example :
>>> l_data = [0xCA, 0xFE, 0xDE, 0xCA] # 11001010111111101101111011001010
>>> l_tests = [(0, 8), # [0xCA] 1100 1010
...            (3, 8), # [0x57] 0101 0111
...            (8, 8), # [0xFE] 1111 1110
...            (10, 8), # [0xFB] 1111 1011
...            (0, 13), # [0xCA, 0xF8] 1100 1010 1111 1000
...            (3, 13), # [0x57, 0xF0] 0101 0111 1111 0000
...            (8, 13), # [0xFE, 0xD8] 1111 1110 1101 1000
...            (10, 13), # [0xFB, 0x78] 1111 1011 0111 1000
...            ]
>>> [[hex(b)
...   for b in extract(l_data, l_offset, l_width)]
...  for (l_offset, l_width) in l_tests]
[['0xca'], ['0x57'], ['0xfe'], ['0xfb'], ['0xca', '0xf8'], ['0x57', '0xf0'], ['0xfe', '0xd8'], ['0xfb', '0x78']]
    """
    # First compute the range so as to narrow the data down to what's useful
    (l_start_byte, l_start_offset) = to_bitwise_addr(offset)
    l_end_byte = to_bitwise_addr(offset + width - 1)[0]

    # If there is enough data, left-shift the required subset
    if l_end_byte < len(data):
        l_shifted_data = cross_byte_left_shift(data[l_start_byte:l_end_byte + 1], l_start_offset)
    else:
        raise HexUtilsInputSizeError

    # Get rid of the useless last bytes, if any
    (l_last_byte, l_last_bit) = to_bitwise_addr(width - 1)
    l_shifted_data[l_last_byte] &= (~(0xFF >> (l_last_bit + 1)) & 0xFF)

    return bytearray(l_shifted_data[0:l_last_byte+1])


if __name__ == "__main__":
    import doctest
    doctest.testmod(verbose=True, report=True, optionflags=doctest.REPORT_NDIFF,
                    exclude_empty=True)
