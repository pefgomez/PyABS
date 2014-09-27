PyABS - Python Advanced Binary Structure
========================================

This is a library to easily decode any kind of binary data.

The early version had originally been written for python 3, but due to real-world constraints,
I had to backport the code to python 2.7

It shouldn't be too hard to make it work in both versions, but it's not planned yet.

======================
1. Quick Walk-through
======================
Consider the following data : 0xDA4341464544454341. You know how it's structured and you need to
decode it.

In this example, you know that it's a packed structure composed of :
- a field 'my-int-1' on the first 3 bits
- a field 'my-int-2' on the next 5 bits
- a field 'my-str', an ASCII string of 8 characters

Granted, it would be trivial to write a function to decode this simple example data. But for more
complex data (often encountered in network communication), the code can quickly become a lot more
involved.

PyABS provides you with a simple and natural way of decoding your data, and even a better way of
formatting the output :

>>> l_abs = AdvancedBinaryStructure('DA4341464544454341', [
...     ('my-int-1', 3),
...     ('my-int-2', 4),
...     ('my-flag', 1),
...     ('my-str', 64, AbsFieldAscii)
... ])
>>> l_abs.pprint()
{'my-int-1': 6 (0x6),
 'my-int-2': 13 (0xD),
 'my-flag': False,
 'my-str': CAFEDECA (0x4341464544454341)}

You can get more information with the verbose version :

>>> l_abs.pprint(verbose=True)
{'data': 'DA4341464544454341',
 'decoded_data': {'my-int-1': 6 (0x6),
                  'my-int-2': 13 (0xD),
                  'my-flag': False,
                  'my-str': CAFEDECA (0x4341464544454341)},
 'remaining_data': '',
 'statistics': {'decoded': '9 bytes + 0 bits',
                'remaining': '0 bytes + 0 bits'}}

An AdvancedBinaryStructure is a nested tree of OrderedDicts and lists, and you can access the
various nested trees just like with any other dicts :
>>> l_abs['decoded_data']['my-int-1']
6 (0x6)

This is just the a representation of the field, but each field has the following properties :

>>> l_abs['decoded_data']['my-int-1'].id()
'my-int-1'
>>> l_abs['decoded_data']['my-int-1'].bit_width()
3
>>> l_abs['decoded_data']['my-int-1'].value()
6
>>> l_abs['decoded_data']['my-int-1'].is_tagged()
False
>>> l_abs['decoded_data']['my-int-1'].raw_data(as_hex=True)
'C0'

See the (massive) top-level docstring in AdvancedBinaryStructure for a more in-depth guide to the
library, and for more complex field specifications.
