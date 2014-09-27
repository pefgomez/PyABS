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
"""
PyABS - Python Advanced Binary Structure

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

Read on for a more in-depth guide to the library, and for more complex field specifications.

========================
2. Field specifications
========================

PyABS supports a number of generic types of fields, which act as building blocks for representing
any kind of complex binary data structure.

There are seven kinds of "Field Specs" :
- Integer fields
- Boolean fields
- Placeholder fields
- Helper Class fields
  - builtin : ASCII fields
  - builtin : RAW DATA fields
- Struct fields
- Switch fields
- Dynamic Arrays fields

-------------------
2.1 Integer fields
-------------------

By default, a field is decoded as an integer, spanning the provided number of bits.
The syntax for an integer field spec is simply :

  ('field id', bit_width)

Ignore the brackets in the following examples for now, it will all become clear when reading about
the Struct field specs.

>>> AdvancedBinaryStructure('CA', [
...     ('my-int', 3),
... ]).pprint()
{'my-int': 6 (0x6)}

The maximum supported integer width is 64 bits :

>>> AdvancedBinaryStructure('CAFEDECADEADBEEF01', [
...     ('my-int', 64),
... ]).pprint()
{'my-int': 14627373602646638319 (0xCAFEDECADEADBEEF)}

For fields with a larger bit width, you will need an helper class (more on this shortly),
otherwise an AbsFieldSpecError exception is raised :

>>> AdvancedBinaryStructure('CAFEDECADEADBEEF01', [
...     ('my-int', 64 + 1),
... ]).pprint()
Traceback (most recent call last):
...
AbsFieldSpecError

--------------------------------
2.2 Boolean fields (or 'flags')
--------------------------------

If the bit width is 1, then the field will automatically be decoded as a boolean :

>>> AdvancedBinaryStructure('01', [
...     ('my-bool', 1),
... ]).pprint()
{'my-bool': False}

>>> AdvancedBinaryStructure('80', [
...     ('my-bool', 1),
... ]).pprint()
{'my-bool': True}

-----------------------
2.3 Placeholder fields
-----------------------

If the bit width is absent or 0, then the field will be decoded as an empty field and will not
consume any bit of the input data. This might sound useless, but I assure you there is a use for
such placeholders (more on that when talking about Switch fields) !

The preferred form is simply 'my-placeholder'...

>>> AdvancedBinaryStructure('01', [
...     'my-placeholder',
... ]).pprint()
{'my-placeholder': (None)}

... but the following ones are also accepted.

>>> AdvancedBinaryStructure('01', [
...     ('my-placeholder'),
... ]).pprint()
{'my-placeholder': (None)}

>>> AdvancedBinaryStructure('01', [
...     ('my-placeholder', ),
... ]).pprint()
{'my-placeholder': (None)}

>>> AdvancedBinaryStructure('01', [
...     ('my-placeholder', 0),
... ]).pprint()
{'my-placeholder': (None)}

------------------------
2.4 Helper class fields
------------------------

Often, your field needs to be formatted in a peculiar way. Maybe you're not statisfied with just
True/False for your flag ? Maybe your integer field is an enumerate, and you want to display the
name corresponding to its value ?

You can define helper classes to help decode and display your field in any way you want. All the
details about defining your own helper classes are explained in "3. Defining helper classes".

PyABS has two built-in ones, namely AbsFieldAscii and AbsFieldRawData. The syntax is the same as
for the basic field specs, except you add the name of your helper class as the third item :

>>> AdvancedBinaryStructure('434146454445434142454546', [
...     ('my-str', 96, AbsFieldAscii),
... ]).pprint()
{'my-str': CAFEDECABEEF (0x434146454445434142454546)}

>>> AdvancedBinaryStructure('434146454445434142454546', [
...     ('my-rawdata', 96, AbsFieldRawData),
... ]).pprint()
{'my-rawdata': 0x434146454445434142454546}

Each helper class can define its own behavior : AbsFieldAscii, for instance, needs the bit width
to be a multiple of 8 (1 character == 1 byte), otherwise it raises an AbsFieldSpecError exception :

>>> AdvancedBinaryStructure('434146454445434142454546', [
...     ('my-str', 94, AbsFieldAscii),
... ]).pprint()
Traceback (most recent call last):
...
AbsFieldSpecError

On the other hand, AbsFieldRawData will happily accept it. But in order to print the hexadecimal
representation it will pad with 0 bits (note the 44=01000100 instead of 46=01000110). The actual
bit width is still 94 as requested, however :

>>> l_abs = AdvancedBinaryStructure('434146454445434142454546', [
...     ('my-rawdata', 94, AbsFieldRawData),
... ])
>>> l_abs.pprint()
{'my-rawdata': 0x434146454445434142454544}
>>> l_abs['decoded_data']['my-rawdata'].bit_width()
94

------------------
2.5 Struct fields
------------------

Although I haven't said anything, you've already seen it in action in every single example I gave
you ! :)

A struct field is simply an ordered list of fields, and the corresponding field spec makes use of a
simple python list :

  ('my-struct', [ ... ])

Remember the very first example ?

>>> AdvancedBinaryStructure('DA4341464544454341', [
...     ('my-int-1', 3),
...     ('my-int-2', 4),
...     ('my-flag', 1),
...     ('my-str', 64, AbsFieldAscii)
... ]).pprint()
{'my-int-1': 6 (0x6),
 'my-int-2': 13 (0xD),
 'my-flag': False,
 'my-str': CAFEDECA (0x4341464544454341)}

Now you can see that the enclosing brackets actually specify the top-level struct field.

The only peculiarity of the top-level struct field is that we don't give it a name : actually,
it does have one but it's only implementation details, you don't have to worry about this.

One thing to note, however, is that struct fields can be nested. This can be very useful to
group several fields together, as it's made clear in the output :

>>> AdvancedBinaryStructure('DA4341464544454341', [
...     ('my-int-1', 3),
...     ('my-struct', [
...        ('my-int-2', 4),
...        ('my-flag', 1),
...      ]),
...     ('my-str', 64, AbsFieldAscii)
... ]).pprint()
{'my-int-1': 6 (0x6),
 'my-struct': {'my-int-2': 13 (0xD),
               'my-flag': False},
 'my-str': CAFEDECA (0x4341464544454341)}

------------------
2.6 Switch fields
------------------

So far, we've only seen the most basic fields : they are the building blocks to decode any kind of
data... at least when you know exactly which layout it will have.

But what if the very presence of a field depends on the value of a flag ? What if the remaining
data must be decoded in one way if a previous field has a value A, but in a totally different way
if that same field has value B, and yet another way for value C ?

You get the idea : we need more dynamic kinds of fields.

The first one is a switch-like field, and its field spec is in the form :

  [SWITCH, 'tagged field id', { val1: field_spec_1, val2: field_spec_2, ... }]

Obviously, a Switch field needs another field to decide which alternative to choose : in order
for this to work, you first need to tag one of the previous fields with TAGGED, and give its name to
the Switch field.

Only the Integer, Boolean and Helper Class fields can be tagged by adding TAGGED. They will be
marked as such in the output :

>>> AdvancedBinaryStructure('CA', [
...     ('my-int', 3, TAGGED),
... ]).pprint()
{'my-int': 6 (0x6) <TAGGED>}

>>> AdvancedBinaryStructure('01', [
...     ('my-bool', 1, TAGGED),
... ]).pprint()
{'my-bool': False <TAGGED>}

>>> AdvancedBinaryStructure('434146454445434142454546', [
...     ('my-str', 96, AbsFieldAscii, TAGGED),
... ]).pprint()
{'my-str': CAFEDECABEEF (0x434146454445434142454546) <TAGGED>}

Now that we now how to tag a field, here is how the output evolves according to the value of the
tagged field :

>>> AdvancedBinaryStructure('F04341464544454341', [
...     ('my-int-1', 6),
...     ('my-tagged-field', 2, TAGGED),
...     [SWITCH, 'my-tagged-field', {
...        0: ('my-field-as-int', 16),
...        1: ('my-field-as-str', 16, AbsFieldAscii),
...        2: ('my-field-as-struct', [
...              ('my-int-1', 3),
...              ('my-int-2', 5),
...              ('my-int-3', 8)
...            ])
...      }],
...     ('my-str', 48, AbsFieldAscii)
... ]).pprint()
{'my-int-1': 60 (0x3C),
 'my-tagged-field': 0 (0x0) <TAGGED>,
 'my-field-as-int': 17217 (0x4341),
 'my-str': FEDECA (0x464544454341)}

>>> AdvancedBinaryStructure('F14341464544454341', [
...     ('my-int-1', 6),
...     ('my-tagged-field', 2, TAGGED),
...     [SWITCH, 'my-tagged-field', {
...        0: ('my-field-as-int', 16),
...        1: ('my-field-as-str', 16, AbsFieldAscii),
...        2: ('my-field-as-struct', [
...              ('my-int-1', 3),
...              ('my-int-2', 5),
...              ('my-int-3', 8)
...            ])
...      }],
...     ('my-str', 48, AbsFieldAscii)
... ]).pprint()
{'my-int-1': 60 (0x3C),
 'my-tagged-field': 1 (0x1) <TAGGED>,
 'my-field-as-str': CA (0x4341),
 'my-str': FEDECA (0x464544454341)}

>>> AdvancedBinaryStructure('F24341464544454341', [
...     ('my-int-1', 6),
...     ('my-tagged-field', 2, TAGGED),
...     [SWITCH, 'my-tagged-field', {
...        0: ('my-field-as-int', 16),
...        1: ('my-field-as-str', 16, AbsFieldAscii),
...        2: ('my-field-as-struct', [
...              ('my-int-1', 3),
...              ('my-int-2', 5),
...              ('my-int-3', 8)
...            ])
...      }],
...     ('my-str', 48, AbsFieldAscii)
... ]).pprint()
{'my-int-1': 60 (0x3C),
 'my-tagged-field': 2 (0x2) <TAGGED>,
 'my-field-as-struct': {'my-int-1': 2 (0x2),
                        'my-int-2': 3 (0x03),
                        'my-int-3': 65 (0x41)},
 'my-str': FEDECA (0x464544454341)}

Placeholder fields have a nice use case here. Suppose a whole section must only be decoded when a
flag is true. If the flag is false, it can be nice to explicitly show that the section was empty :

>>> AdvancedBinaryStructure('F14341464544454341', [
...     ('my-int-1', 7),
...     ('my-flag', 1, TAGGED),
...     [SWITCH, 'my-flag', {
...        False: 'my-optional-section',
...        True: ('my-optional-section', [
...                 ('my-int-1', 3),
...                 ('my-int-2', 5),
...                 ('my-int-3', 8)
...               ])
...      }],
...     ('my-str', 48, AbsFieldAscii)
... ]).pprint()
{'my-int-1': 120 (0x78),
 'my-flag': True <TAGGED>,
 'my-optional-section': {'my-int-1': 2 (0x2),
                         'my-int-2': 3 (0x03),
                         'my-int-3': 65 (0x41)},
 'my-str': FEDECA (0x464544454341)}

>>> AdvancedBinaryStructure('F04341464544454341', [
...     ('my-int-1', 7),
...     ('my-flag', 1, TAGGED),
...     [SWITCH, 'my-flag', {
...        False: 'my-optional-section',
...        True: ('my-optional-section', [
...                 ('my-int-1', 3),
...                 ('my-int-2', 5),
...                 ('my-int-3', 8)
...               ])
...      }],
...     ('my-str', 48, AbsFieldAscii)
... ]).pprint()
{'my-int-1': 120 (0x78),
 'my-flag': False <TAGGED>,
 'my-optional-section': (None),
 'my-str': CAFEDE (0x434146454445)}

Please note that there is no 'default' case for the Switch field : it there is an unauthorized
value in the tagged field, then an AbsDecodingError exception is raised :

>>> AdvancedBinaryStructure('FF4341464544454341', [
...     ('my-int-1', 6),
...     ('my-tagged-field', 2, TAGGED),
...     [SWITCH, 'my-tagged-field', {
...        0: ('my-field-as-int', 16),
...        1: ('my-field-as-str', 16, AbsFieldAscii),
...        2: ('my-field-as-struct', [
...              ('my-int-1', 3),
...              ('my-int-2', 5),
...              ('my-int-3', 8)
...            ])
...      }],
...     ('my-str', 48, AbsFieldAscii)
... ]).pprint()
Traceback (most recent call last):
...
AbsDecodingError

Similarly, if the tagged field cannot be found (or has not yet been decoded, which is just bad
design of the data format), then an AbsDecodingError exception is raised :

>>> AdvancedBinaryStructure('FF4341464544454341', [
...     ('my-int-1', 6),
...     ('my-tagged-field', 2, TAGGED),
...     [SWITCH, 'my-NOT_FOUND_tagged-field', {
...        0: ('my-field-as-int', 16),
...        1: ('my-field-as-str', 16, AbsFieldAscii),
...        2: ('my-field-as-struct', [
...              ('my-int-1', 3),
...              ('my-int-2', 5),
...              ('my-int-3', 8)
...            ])
...      }],
...     ('my-str', 48, AbsFieldAscii)
... ]).pprint()
Traceback (most recent call last):
...
AbsDecodingError

--------------------------
2.7 Dynamic Arrays fields
--------------------------

The second type of dynamic field is the Dynamic Array field spec.

Binary data often have a field containing a length, immediately followed by an array of as much
elements as indicated in the length field (Pascal-style arrays).

This is the NB_ELTS variant :
  [ DYN_ARRAY, 'dyn-array-id', <NB_ELTS>, size_of_each_element, <opt_nested_spec> ]

Sometimes, the first field is not a number of elements but a size. The unit of this size can change
(size in bytes, or in 16-bits words, ...). Sometimes the length of this field is included in the
indicated size, sometimes it is excluded and only describes the following data.

This is the SIZE_EXCL/SIZE_INCL variant :
  [ DYN_ARRAY, 'dyn-array-id', <SIZE_EXCL|SIZE_INCL>, unit_of_length_field, <opt_nested_spec> ]

One limitation : the size of the length field is always equal to the size of each element.

In both variants, you can optionally add a nested field spec (without the field id, which makes
no sense) to further decode each element of the array.

You can find below a list of each possible variant of the Dynamic Arrays field :

>>> AdvancedBinaryStructure('1043414645444543414445414442454546', [
...     [DYN_ARRAY, 'my-dyn-array', SIZE_EXCL, 8]
... ]).pprint()
{'my-dyn-array': {'size': 16 bytes, header excluded (0x10),
                  'data': [67 (0x43),
                           65 (0x41),
                           70 (0x46),
                           69 (0x45),
                           68 (0x44),
                           69 (0x45),
                           67 (0x43),
                           65 (0x41),
                           68 (0x44),
                           69 (0x45),
                           65 (0x41),
                           68 (0x44),
                           66 (0x42),
                           69 (0x45),
                           69 (0x45),
                           70 (0x46)]}}

>>> AdvancedBinaryStructure('000843414645444543414445414442454546', [
...     [DYN_ARRAY, 'my-dyn-array', SIZE_EXCL, 16]
... ]).pprint()
{'my-dyn-array': {'size': 8 word16, header excluded (0x0008),
                  'data': [17217 (0x4341),
                           17989 (0x4645),
                           17477 (0x4445),
                           17217 (0x4341),
                           17477 (0x4445),
                           16708 (0x4144),
                           16965 (0x4245),
                           17734 (0x4546)]}}

>>> AdvancedBinaryStructure('0000000443414645444543414445414442454546', [
...     [DYN_ARRAY, 'my-dyn-array', SIZE_EXCL, 32]
... ]).pprint()
{'my-dyn-array': {'size': 4 word32, header excluded (0x00000004),
                  'data': [1128351301 (0x43414645),
                           1145389889 (0x44454341),
                           1145389380 (0x44454144),
                           1111835974 (0x42454546)]}}

>>> AdvancedBinaryStructure('000000000000000243414645444543414445414442454546', [
...     [DYN_ARRAY, 'my-dyn-array', SIZE_EXCL, 64]
... ]).pprint()
{'my-dyn-array': {'size': 2 word64, header excluded (0x0000000000000002),
                  'data': [4846231937339441985 (0x4341464544454341),
                           4919409929397552454 (0x4445414442454546)]}}

>>> AdvancedBinaryStructure('1143414645444543414445414442454546', [
...     [DYN_ARRAY, 'my-dyn-array', SIZE_INCL, 8]
... ]).pprint()
{'my-dyn-array': {'size': 17 bytes, including header (0x11),
                  'data': [67 (0x43),
                           65 (0x41),
                           70 (0x46),
                           69 (0x45),
                           68 (0x44),
                           69 (0x45),
                           67 (0x43),
                           65 (0x41),
                           68 (0x44),
                           69 (0x45),
                           65 (0x41),
                           68 (0x44),
                           66 (0x42),
                           69 (0x45),
                           69 (0x45),
                           70 (0x46)]}}

>>> AdvancedBinaryStructure('000943414645444543414445414442454546', [
...     [DYN_ARRAY, 'my-dyn-array', SIZE_INCL, 16]
... ]).pprint()
{'my-dyn-array': {'size': 9 word16, including header (0x0009),
                  'data': [17217 (0x4341),
                           17989 (0x4645),
                           17477 (0x4445),
                           17217 (0x4341),
                           17477 (0x4445),
                           16708 (0x4144),
                           16965 (0x4245),
                           17734 (0x4546)]}}

>>> AdvancedBinaryStructure('0000000543414645444543414445414442454546', [
...     [DYN_ARRAY, 'my-dyn-array', SIZE_INCL, 32]
... ]).pprint()
{'my-dyn-array': {'size': 5 word32, including header (0x00000005),
                  'data': [1128351301 (0x43414645),
                           1145389889 (0x44454341),
                           1145389380 (0x44454144),
                           1111835974 (0x42454546)]}}

>>> AdvancedBinaryStructure('000000000000000343414645444543414445414442454546', [
...     [DYN_ARRAY, 'my-dyn-array', SIZE_INCL, 64]
... ]).pprint()
{'my-dyn-array': {'size': 3 word64, including header (0x0000000000000003),
                  'data': [4846231937339441985 (0x4341464544454341),
                           4919409929397552454 (0x4445414442454546)]}}

>>> AdvancedBinaryStructure('1043414645444543414445414442454546', [
...     [DYN_ARRAY, 'my-dyn-array', NB_ELTS, 8]
... ]).pprint()
{'my-dyn-array': {'length': 16 elements (0x10),
                  'data': [67 (0x43),
                           65 (0x41),
                           70 (0x46),
                           69 (0x45),
                           68 (0x44),
                           69 (0x45),
                           67 (0x43),
                           65 (0x41),
                           68 (0x44),
                           69 (0x45),
                           65 (0x41),
                           68 (0x44),
                           66 (0x42),
                           69 (0x45),
                           69 (0x45),
                           70 (0x46)]}}

>>> AdvancedBinaryStructure('000843414645444543414445414442454546', [
...     [DYN_ARRAY, 'my-dyn-array', NB_ELTS, 16]
... ]).pprint()
{'my-dyn-array': {'length': 8 elements (0x0008),
                  'data': [17217 (0x4341),
                           17989 (0x4645),
                           17477 (0x4445),
                           17217 (0x4341),
                           17477 (0x4445),
                           16708 (0x4144),
                           16965 (0x4245),
                           17734 (0x4546)]}}

>>> AdvancedBinaryStructure('0000000443414645444543414445414442454546', [
...     [DYN_ARRAY, 'my-dyn-array', NB_ELTS, 32]
... ]).pprint()
{'my-dyn-array': {'length': 4 elements (0x00000004),
                  'data': [1128351301 (0x43414645),
                           1145389889 (0x44454341),
                           1145389380 (0x44454144),
                           1111835974 (0x42454546)]}}

>>> AdvancedBinaryStructure('000000000000000243414645444543414445414442454546', [
...     [DYN_ARRAY, 'my-dyn-array', NB_ELTS, 64]
... ]).pprint()
{'my-dyn-array': {'length': 2 elements (0x0000000000000002),
                  'data': [4846231937339441985 (0x4341464544454341),
                           4919409929397552454 (0x4445414442454546)]}}

>>> AdvancedBinaryStructure('0000000543414645444543414445414442454546', [
...     [DYN_ARRAY, 'my-dyn-array', SIZE_INCL, 32, AbsFieldAscii]
... ]).pprint()
{'my-dyn-array': {'size': 5 word32, including header (0x00000005),
                  'data': [CAFE (0x43414645),
                           DECA (0x44454341),
                           DEAD (0x44454144),
                           BEEF (0x42454546)]}}

>>> AdvancedBinaryStructure('000943414645444543414445414442454546', [
...   [DYN_ARRAY, 'my-dyn-array', SIZE_INCL, 16, [
...     ('my-int', 7),
...     ('my-bool', 1),
...     ('my-char', 8, AbsFieldAscii)
...   ]]
... ]).pprint()
{'my-dyn-array': {'size': 9 word16, including header (0x0009),
                  'data': [{'my-int': 33 (0x21),
                            'my-bool': True,
                            'my-char': A (0x41)},
                           {'my-int': 35 (0x23),
                            'my-bool': False,
                            'my-char': E (0x45)},
                           {'my-int': 34 (0x22),
                            'my-bool': False,
                            'my-char': E (0x45)},
                           {'my-int': 33 (0x21),
                            'my-bool': True,
                            'my-char': A (0x41)},
                           {'my-int': 34 (0x22),
                            'my-bool': False,
                            'my-char': E (0x45)},
                           {'my-int': 32 (0x20),
                            'my-bool': True,
                            'my-char': D (0x44)},
                           {'my-int': 33 (0x21),
                            'my-bool': False,
                            'my-char': E (0x45)},
                           {'my-int': 34 (0x22),
                            'my-bool': True,
                            'my-char': F (0x46)}]}}

>>> AdvancedBinaryStructure('000943414645444543414445414442454546', [
...   [DYN_ARRAY, 'my-dyn-array', SIZE_INCL, 16, [
...     ('my-int', 7),
...     ('my-bool', 1),
...     ('my-str', 24, AbsFieldAscii)
...   ]]
... ]).pprint()
{'my-dyn-array': {'size': 9 word16, including header (0x0009),
                  'data': [{'my-int': 33 (0x21),
                            'my-bool': True,
                            'my-str': AFE (0x414645)},
                           {'my-int': 34 (0x22),
                            'my-bool': False,
                            'my-str': ECA (0x454341)},
                           {'my-int': 34 (0x22),
                            'my-bool': False,
                            'my-str': EAD (0x454144)},
                           {'my-int': 33 (0x21),
                            'my-bool': False,
                            'my-str': EEF (0x454546)}]}}

===========================
3. Defining helper classes
===========================

Defining your own helper class can be as simple as deriving from one of the base classes
AbsFieldInteger, AbsFieldBoolean, AbsFieldAscii or AbsFieldRawData :

>>> class MyEnumerate(AbsFieldInteger):
...     def __repr__(self):
...         if self._value == 0:
...             return "TODO (0)"
...         elif self._value == 1:
...             return "In Progress (1)"
...         elif self._value == 2:
...             return "Delegated (2)"
...         elif self._value == 3:
...             return "Done (3)"
...         else:
...             raise AbsOutOfRangeError
>>> AdvancedBinaryStructure('1F', [
...     ('my-enum', 3, MyEnumerate),
... ]).pprint()
{'my-enum': TODO (0)}
>>> AdvancedBinaryStructure('3F', [
...     ('my-enum', 3, MyEnumerate),
... ]).pprint()
{'my-enum': In Progress (1)}
>>> AdvancedBinaryStructure('5F', [
...     ('my-enum', 3, MyEnumerate),
... ]).pprint()
{'my-enum': Delegated (2)}
>>> AdvancedBinaryStructure('7F', [
...     ('my-enum', 3, MyEnumerate),
... ]).pprint()
{'my-enum': Done (3)}
>>> AdvancedBinaryStructure('9F', [
...     ('my-enum', 3, MyEnumerate),
... ]).pprint()
Traceback (most recent call last):
...
AbsOutOfRangeError

To define more complex helper classes, an AbsFieldMixin mixin superclass is provided.

AbsFieldMixin provides the necessary underlying mechanisms for the helper class to work with
the field spec and to decode the data, but it doesn't do much on its own.

It provides :
- a default implementation of _parse_args(spec, data, offset, context) which does some
  basic checks and takes care of building the _raw_data attributes after having called
  the _decode method.

- accessors for _id, _bit_width, _value, _is_tagged and _raw_data

Subclasses should override at least the following methods in order to do anything useful :
- __init__ => must call _parse_args
- __repr__
- _decode_spec
- _decode_data

More indepth explanations to come but in the mean time, have a look at AbsFieldMixin and at the base
classes to understand how it all fits together.

=====================
4. Future evolutions
=====================
- Switch fields : remove the necessity of tagging a field
- Switch fields : introduce a default case
- Dynamic Array fields : add the possibility to specify a different length for the length field.
- HexUtils : extract function : add an option to stop the left shift of the extracted data at the
                                beginning of the first byte (overwriting the first few bits with 0s
                                if necessary).
                                => can make it easier to recognise in the input data
- Exceptions : add more informations in the exception :
               - what has been decoded so far
               - what remains to be decoded
             : intercept them, complete them and reemit them at various levels in the factory (
             make_xxx functions)
             : at the top-level of the decoding tree (in the AdvancedBinaryStructure
             constructor), intercept them and add fields to show when the exception occurred in
             the pretty print output.
- Make it work on both python 2.7 and python 3

============================
5. Robustness doctest cases
============================

Not very digest, but as good a place as any to put them.

"""
import collections

from backports import pprint33_backport_to_27 as pprint
import HexUtils

####################################################################################################
#
# INTERNAL
#
####################################################################################################

PARAM_MAX_INTEGER_BIT_WIDTH = 64

TAGGED = 'TAGGED'
SWITCH = 'SWITCH'
DYN_ARRAY = 'DYN_ARRAY'

SIZE_EXCL = 'SIZE_EXCL'
SIZE_INCL = 'SIZE_INCL'
NB_ELTS = 'NB_ELTS'

SPEC_PLACEHOLDER = 'SPEC_PLACEHOLDER'
SPEC_BOOLEAN = 'SPEC_BOOLEAN'
SPEC_INTEGER = 'SPEC_INTEGER'
SPEC_HELPER_CLASS = 'SPEC_HELPER_CLASS'
SPEC_STRUCT = 'SPEC_STRUCT'
SPEC_SWITCH = 'SPEC_SWITCH'
SPEC_DYN_ARRAY = 'SPEC_DYN_ARRAY'


class AdvancedBinaryStructure(collections.OrderedDict):
    def __init__(self, hex_str, spec):
        super(AdvancedBinaryStructure, self).__init__()

        # Initiate a recursive decoding (turn the top-level field specs into a root binary struct)
        self['data'] = hex_str
        self['decoded_data'] = AbsFactory.make(('root', list(spec)), hex_str)

        l_decoded_bits = self['decoded_data'].bit_width()
        l_not_decoded_bits = len(hex_str) * 4 - l_decoded_bits

        self['remaining_data'] = hex_str[l_decoded_bits // 8 * 2:]

        self['statistics'] = {
            'decoded': "%d bytes + %d bits" % HexUtils.to_bitwise_addr(l_decoded_bits),
            'remaining': "%d bytes + %d bits" % HexUtils.to_bitwise_addr(l_not_decoded_bits)
        }

    def pprint(self, verbose=False):
        if verbose:
            pprint.pprint(self)
        else:
            pprint.pprint(self['decoded_data'])


class AbsFactory(object):
    @staticmethod
    def spec_type(spec):
        """Return the type of field corresponding to the given field SPEC argument.

>>> AbsFactory.spec_type('my-placeholder')
'SPEC_PLACEHOLDER'

>>> AbsFactory.spec_type(('my-placeholder'))
'SPEC_PLACEHOLDER'

>>> AbsFactory.spec_type(('my-placeholder',))
'SPEC_PLACEHOLDER'

>>> AbsFactory.spec_type(('my-placeholder', 0))
'SPEC_PLACEHOLDER'

>>> AbsFactory.spec_type(('my-bool', 1))
'SPEC_BOOLEAN'

>>> AbsFactory.spec_type(('my-int', 2))
'SPEC_INTEGER'

>>> AbsFactory.spec_type(('my-int', PARAM_MAX_INTEGER_BIT_WIDTH))
'SPEC_INTEGER'

>>> AbsFactory.spec_type(('my-int', PARAM_MAX_INTEGER_BIT_WIDTH + 1))
Traceback (most recent call last):
...
AbsFieldSpecError

>>> AbsFactory.spec_type(('my-int', 2, TAGGED))
'SPEC_INTEGER'

>>> AbsFactory.spec_type(('my-str', 94, AbsFieldAscii))
Traceback (most recent call last):
...
AbsFieldSpecError

>>> AbsFactory.spec_type(('my-str', 96, AbsFieldAscii))
'SPEC_HELPER_CLASS'

>>> AbsFactory.spec_type(('my-str', 95, AbsFieldAscii))
Traceback (most recent call last):
...
AbsFieldSpecError

>>> AbsFactory.spec_type(('my-str', 96, AbsFieldAscii, TAGGED))
'SPEC_HELPER_CLASS'

>>> AbsFactory.spec_type(('my-struct', [
...     ('my-int-1', 3),
...     ('my-int-2', 5),
...     ('my-str', 16, AbsFieldAscii)
... ]))
'SPEC_STRUCT'

>>> AbsFactory.spec_type([SWITCH, 'my-tagged-field', {
...    0: ('my-field-as-int', 8),
...    1: ('my-field-as-str', 16, AbsFieldAscii),
...    2: ('my-field-as-struct', [
...            ('my-int-1', 3),
...            ('my-int-2', 5)
...        ])
... }])
'SPEC_SWITCH'

>>> AbsFactory.spec_type([DYN_ARRAY, 'my-dyn-array', SIZE_EXCL, 8])
'SPEC_DYN_ARRAY'

>>> AbsFactory.spec_type([DYN_ARRAY, 'my-dyn-array', SIZE_EXCL, 16])
'SPEC_DYN_ARRAY'

>>> AbsFactory.spec_type([DYN_ARRAY, 'my-dyn-array', SIZE_EXCL, 32])
'SPEC_DYN_ARRAY'

>>> AbsFactory.spec_type([DYN_ARRAY, 'my-dyn-array', SIZE_EXCL, 64])
'SPEC_DYN_ARRAY'


>>> AbsFactory.spec_type([DYN_ARRAY, 'my-dyn-array', SIZE_INCL, 8])
'SPEC_DYN_ARRAY'

>>> AbsFactory.spec_type([DYN_ARRAY, 'my-dyn-array', SIZE_INCL, 16])
'SPEC_DYN_ARRAY'

>>> AbsFactory.spec_type([DYN_ARRAY, 'my-dyn-array', SIZE_INCL, 32])
'SPEC_DYN_ARRAY'

>>> AbsFactory.spec_type([DYN_ARRAY, 'my-dyn-array', SIZE_INCL, 64])
'SPEC_DYN_ARRAY'


>>> AbsFactory.spec_type([DYN_ARRAY, 'my-dyn-array', NB_ELTS, 8])
'SPEC_DYN_ARRAY'

>>> AbsFactory.spec_type([DYN_ARRAY, 'my-dyn-array', NB_ELTS, 16])
'SPEC_DYN_ARRAY'

>>> AbsFactory.spec_type([DYN_ARRAY, 'my-dyn-array', NB_ELTS, 32])
'SPEC_DYN_ARRAY'

>>> AbsFactory.spec_type([DYN_ARRAY, 'my-dyn-array', NB_ELTS, 64])
'SPEC_DYN_ARRAY'


>>> AbsFactory.spec_type([DYN_ARRAY, 'my-dyn-array', SIZE_INCL, 16, AbsFieldAscii])
'SPEC_DYN_ARRAY'


>>> AbsFactory.spec_type([DYN_ARRAY, 'my-dyn-array', SIZE_INCL, 16, [
...     ('my-int-1', 3),
...     ('my-int-2', 5),
...     ('my-char', 8, AbsFieldAscii)
... ]])
'SPEC_DYN_ARRAY'
        """
        if type(spec) == str:
            return SPEC_PLACEHOLDER

        elif type(spec) == tuple:
            if type(spec[0]) == str:
                if len(spec) == 1:
                    return SPEC_PLACEHOLDER

                elif len(spec) == 2:
                    if type(spec[1]) == int:
                        if spec[1] == 0:
                            return SPEC_PLACEHOLDER
                        elif spec[1] == 1:
                            return SPEC_BOOLEAN
                        elif (spec[1] > 1) and (spec[1] <= PARAM_MAX_INTEGER_BIT_WIDTH):
                            return SPEC_INTEGER
                        else:
                            raise AbsFieldSpecError

                    elif type(spec[1]) == list:
                        if all([AbsFactory.is_valid_spec(s) for s in spec[1]]):
                            return SPEC_STRUCT
                        else:
                            raise AbsFieldSpecError
                    else:
                        raise AbsFieldSpecError

                elif len(spec) == 3:
                    if type(spec[1]) == int:
                        if spec[1] == 1:
                            if spec[2] == TAGGED:
                                return SPEC_BOOLEAN
                            elif issubclass(spec[2], AbsFieldHelperClass):
                                if spec[2].is_valid_spec(spec):
                                    return SPEC_HELPER_CLASS
                                else:
                                    raise AbsFieldSpecError
                            else:
                                raise AbsFieldSpecError
                        elif 1 < spec[1] <= PARAM_MAX_INTEGER_BIT_WIDTH:
                            if spec[2] == TAGGED:
                                return SPEC_INTEGER
                            elif issubclass(spec[2], AbsFieldHelperClass):
                                if spec[2].is_valid_spec(spec):
                                    return SPEC_HELPER_CLASS
                                else:
                                    raise AbsFieldSpecError
                            else:
                                raise AbsFieldSpecError
                        elif spec[1] > PARAM_MAX_INTEGER_BIT_WIDTH:
                            if issubclass(spec[2], AbsFieldHelperClass):
                                if spec[2].is_valid_spec(spec):
                                    return SPEC_HELPER_CLASS
                                else:
                                    raise AbsFieldSpecError
                            else:
                                raise AbsFieldSpecError
                        else:
                            raise AbsFieldSpecError
                    else:
                        raise AbsFieldSpecError

                elif len(spec) == 4:
                    if type(spec[1]) == int:
                        if issubclass(spec[2], AbsFieldHelperClass):
                            if spec[3] == TAGGED:
                                if spec[2].is_valid_spec(spec):
                                    return SPEC_HELPER_CLASS
                                else:
                                    raise AbsFieldSpecError
                            else:
                                raise AbsFieldSpecError
                        else:
                            raise AbsFieldSpecError
                    else:
                        raise AbsFieldSpecError
                else:
                    raise AbsFieldSpecError
            else:
                raise AbsFieldSpecError

        elif type(spec) == list and len(spec) > 0:
            if spec[0] == SWITCH:
                if (len(spec) == 3 and
                    type(spec[1]) == str and
                    type(spec[2]) == dict and
                        all([AbsFactory.is_valid_spec(s)
                             for s in spec[2].values()])):
                    return SPEC_SWITCH
                else:
                    raise AbsFieldSpecError
            elif spec[0] == DYN_ARRAY:
                if 4 <= len(spec) <= 5:
                    if type(spec[1]) != str:
                        raise AbsFieldSpecError
                    if spec[2] not in [SIZE_EXCL, SIZE_INCL, NB_ELTS]:
                        raise AbsFieldSpecError
                    if spec[3] not in [8, 16, 32, 64]:
                        raise AbsFieldSpecError
                    if len(spec) == 4:
                        return SPEC_DYN_ARRAY
                    else:
                        if type(spec[4]) == list:
                            l_child_spec = ('dummy_id', spec[4])
                            if AbsFactory.is_valid_spec(l_child_spec):
                                return SPEC_DYN_ARRAY
                            else:
                                raise AbsFieldSpecError
                        elif issubclass(spec[4], AbsFieldHelperClass):
                            l_child_spec = ('dummy_id', spec[3], spec[4])
                            if AbsFactory.is_valid_spec(l_child_spec):
                                return SPEC_DYN_ARRAY
                            else:
                                raise AbsFieldSpecError
                        else:
                            raise AbsFieldSpecError
                else:
                    raise AbsFieldSpecError
            else:
                raise AbsFieldSpecError
        else:
            raise AbsFieldSpecError

    @staticmethod
    def is_valid_spec(spec):
        AbsFactory.spec_type(spec)
        return True

    @staticmethod
    def _make_helper_class(spec, data, offset=0, context=None):
        """Sub-Factory for helper-class fields.
        Remove the class name from the spec before handing it to its constructor.
        """
        l_spec = list(spec)
        l_helper_class = l_spec.pop(2)
        return l_helper_class(l_spec, data, offset, context)

    @staticmethod
    def _make_switch(spec, data, offset=0, context=None):
        if context is None:
            raise AbsDecodingError
        elif spec[1] not in context:
            raise AbsDecodingError
        else:
            l_target_key = context[spec[1]]

            if l_target_key in spec[2]:
                return AbsFactory.make(spec[2][l_target_key], data, offset, context)
            else:
                raise AbsDecodingError

    @staticmethod
    def make(spec, data=None, offset=0, context=None):
        """Factory function for AdvancedBinaryStructure fields.

        The spec is first analysed to determine which type of field is to be created.
        The arguments are then handed to the proper sub-factory.
        """
        if type(data) == str:
            l_data = HexUtils.hex_str_to_u8(data)
        else:
            l_data = data

        l_spec_type = AbsFactory.spec_type(spec)

        if l_spec_type == SPEC_PLACEHOLDER:
            return AbsFieldPlaceholder(spec, l_data, offset, context)
        elif l_spec_type == SPEC_BOOLEAN:
            return AbsFieldBoolean(spec, l_data, offset, context)
        elif l_spec_type == SPEC_INTEGER:
            return AbsFieldInteger(spec, l_data, offset, context)
        elif l_spec_type == SPEC_HELPER_CLASS:
            return AbsFactory._make_helper_class(spec, l_data, offset, context)
        elif l_spec_type == SPEC_STRUCT:
            return AbsFieldStruct(spec, l_data, offset, context)
        elif l_spec_type == SPEC_SWITCH:
            return AbsFactory._make_switch(spec, l_data, offset, context)
        elif l_spec_type == SPEC_DYN_ARRAY:
            return AbsFieldDynArray(spec, l_data, offset, context)
        else:
            raise AbsFieldSpecError


class AbsError(Exception):
    """Base class for AdvancedBinaryStructure errors"""
    pass


class AbsFieldSpecError(AbsError):
    """Raised when there is an error in a field specification."""
    pass


class AbsDecodingError(AbsError):
    """Raised when there is an error while decoding a value."""
    pass


class AbsOutOfRangeError(AbsError):
    """Raised when a decoded value is out of range."""
    pass


class AbsFieldMixin(object):
    """Mixin class used for defining AdvancedBinaryStructure Fields.

    This class only provides the underlying mechanisms but it doesn't do much on its own.

    It provides :
    - a default implementation of _parse_args(spec, data, offset, context) which does some
      basic checks and takes care of building the _raw_data attributes after having called
      the _decode method.

    - accessors for _id, _bit_width, _value, _is_tagged and _raw_data

    Subclasses should override at least the following methods in order to do anything useful :
    - __init__ => must call _parse_args
    - __repr__
    - _decode_spec
    - _decode_data
    """
    def __init__(self):
        self._id = None
        self._bit_width = 0
        self._value = None
        self._is_tagged = False
        self._raw_data = None

    def __eq__(self, y):
        return self._value == y

    def __hash__(self):
        return hash(self._value)

    def _parse_args(self, spec, data, offset=0, context=None):
        # TODO: decorator ?
        self._decode_spec(spec)
        if data is not None:
            if offset >= 8:
                # TODO : fix that
                # The caller must ensure that the provided data starts at the first useful byte.
                # Consequently, the offset must not cross the first provided byte.
                raise AbsDecodingError
            self._decode_data(spec, data, offset, context)
            if self._bit_width > 0:
                self._raw_data = HexUtils.extract(data, offset, self._bit_width)

    def _decode_spec(self, spec):
        pass

    def _decode_data(self, spec, data, offset=0, context=None):
        pass

    def id(self):
        return self._id

    def bit_width(self):
        return self._bit_width

    def value(self):
        return self._value

    def is_tagged(self):
        return self._is_tagged

    def raw_data(self, as_hex=False):
        if as_hex:
            return ''.join(['%02X' % b for b in self._raw_data])
        else:
            return self._raw_data


class AbsFieldHelperClass(AbsFieldMixin):
    @staticmethod
    def is_valid_spec(spec):
        return False


class AbsFieldPlaceholder(AbsFieldHelperClass):
    """This class implements a simple empty field.

    It can be used as a placeholder, to indicate that the field has indeed been parsed, but that it
    was empty and that it doesn't consume any bit of structure.

    AbsFieldMixin.bit_width() will always return 0
    """
    def __init__(self, spec, data=None, offset=0, context=None):
        super(AbsFieldPlaceholder, self).__init__()
        self._id = spec[0]
        self._parse_args(spec, data, offset, context)

    def __repr__(self):
        return '(None)'

    def _decode_spec(self, spec):
        if type(spec) == str:
            self._id = spec
        elif type(spec) == tuple:
            self._id = spec[0]
        else:
            raise AbsDecodingError


class AbsFieldInteger(AbsFieldHelperClass):
    """Built-in helper class to represent a integer fields.
    """
    def __init__(self, spec, data=None, offset=0, context=None):
        super(AbsFieldInteger, self).__init__()
        self._parse_args(spec, data, offset, context)

    def __repr__(self):
        return '{value:d} (0x{value:0{width}X}){tagged:s}' \
            .format(value=self._value,
                    width=(self._bit_width + 3) // 4,
                    tagged=' <TAGGED>' if self._is_tagged else '')

    def _decode_spec(self, spec):
        self._id = spec[0]
        self._bit_width = spec[1]
        if len(spec) == 3:
            if spec[2] == TAGGED:
                self._is_tagged = True
            else:
                raise AbsDecodingError
        else:
            self._is_tagged = False

    def _decode_data(self, spec, data, offset=0, context=None):
        # Build a map of all the needed bits
        # (ie. a list of tuple of (byte_idx, offset_within_byte))
        l_bitmap = [HexUtils.to_bitwise_addr(l_addr)
                    for l_addr in range(offset, offset + self._bit_width)]
        # Turn this into a list of 0s and 1s corresponding to the value
        # (ie. equivalent to applying a mask, but spanning multiple adjacent bytes)
        l_value_bits = [(data[l_byte] & (2 ** (8 - l_bit - 1))) >> (8 - l_bit - 1)
                        for (l_byte, l_bit) in l_bitmap]
        # Finally, elevate each 1-bit to its power of 2, and sum them up to obtain the final
        # field value
        self._value = sum([2 ** (self._bit_width - i - 1)
                           for (i, b) in enumerate(l_value_bits) if b == 1])

    @staticmethod
    def is_valid_spec(spec):
        return 2 <= spec[1] <= PARAM_MAX_INTEGER_BIT_WIDTH


class AbsFieldBoolean(AbsFieldHelperClass):
    """Built-in helper class to represent boolean fields.
    """
    def __init__(self, spec, data=None, offset=0, context=None):
        super(AbsFieldBoolean, self).__init__()
        self._parse_args(spec, data, offset, context)

    def __repr__(self):
        return '{value:s}{tagged:s}' \
            .format(value=repr(self._value),
                    tagged=' <TAGGED>' if self._is_tagged else '')

    def _decode_spec(self, spec):
        self._id = spec[0]
        self._bit_width = spec[1]
        if len(spec) == 3:
            if spec[2] == TAGGED:
                self._is_tagged = True
            else:
                raise AbsDecodingError
        else:
            self._is_tagged = False

    def _decode_data(self, spec, data, offset=0, context=None):
        l_value = (data[0] & (1 << 8 - offset - 1)) >> (8 - offset - 1)
        if l_value == 0:
            self._value = False
        elif l_value == 1:
            self._value = True
        else:
            raise AbsDecodingError

    @staticmethod
    def is_valid_spec(spec):
        return spec[1] == 1


class AbsFieldAscii(AbsFieldHelperClass):
    """Built-in helper class to represent ASCII fields.
    """
    def __init__(self, spec, data=None, offset=0, context=None):
        super(AbsFieldAscii, self).__init__()
        self._parse_args(spec, data, offset, context)

    def __repr__(self):
        return '{value:s} (0x{raw_data:s}){tagged:s}' \
            .format(value=self._value,
                    raw_data=''.join(['{:02X}'.format(i) for i in self._raw_data]),
                    tagged=' <TAGGED>' if self._is_tagged else '')

    def _decode_spec(self, spec):
        self._id = spec[0]
        if spec[1] % 8 == 0:
            self._bit_width = spec[1]
        else:
            raise AbsDecodingError
        if len(spec) == 3:
            if spec[2] == TAGGED:
                self._is_tagged = True
            else:
                raise AbsDecodingError
        else:
            self._is_tagged = False

    def _decode_data(self, spec, data, offset=0, context=None):
        l_data = HexUtils.extract(data, offset, self._bit_width)
        self._value = ''.join(['{:c}'.format(i) for i in l_data])

    @staticmethod
    def is_valid_spec(spec):
        return spec[1] % 8 == 0


class AbsFieldRawData(AbsFieldHelperClass):
    """Built-in helper class to represent raw data fields.
    """
    def __init__(self, spec, data=None, offset=0, context=None):
        super(AbsFieldRawData, self).__init__()
        self._parse_args(spec, data, offset, context)

    def __repr__(self):
        return '0x{raw_data:s}{tagged:s}' \
            .format(raw_data=self._value,
                    tagged=' <TAGGED>' if self._is_tagged else '')

    def _decode_spec(self, spec):
        self._id = spec[0]
        self._bit_width = spec[1]
        if len(spec) == 3:
            if spec[2] == TAGGED:
                self._is_tagged = True
            else:
                raise AbsDecodingError
        else:
            self._is_tagged = False

    def _decode_data(self, spec, data, offset=0, context=None):
        l_data = HexUtils.extract(data, offset, self._bit_width)
        self._value = ''.join(['{:02X}'.format(i) for i in l_data])

    @staticmethod
    def is_valid_spec(spec):
        return True


class AbsFieldStruct(collections.OrderedDict, AbsFieldHelperClass):
    """Class for struct-like AdvancedBinaryStructure fields.
    """
    def __init__(self, spec, data=None, offset=0, context=None):
        super(AbsFieldStruct, self).__init__()
        AbsFieldHelperClass.__init__(self)
        self._parse_args(spec, data, offset, context)

    def _decode_spec(self, spec):
        self._id = spec[0]

    def _decode_data(self, spec, data, offset=0, context=None):
        if context is None:
            l_context = {}
        else:
            l_context = context

        l_offset = offset
        for l_spec in spec[1]:
            (l_byte_addr, l_byte_offset) = HexUtils.to_bitwise_addr(l_offset)
            l_child = AbsFactory.make(l_spec, data[l_byte_addr:], l_byte_offset, l_context)
            self[l_child.id()] = l_child
            if l_child.is_tagged():
                if l_child.id() in l_context:
                    raise AbsDecodingError
                else:
                    l_context[l_child.id()] = l_child
            l_offset += l_child.bit_width()
        self._bit_width = l_offset - offset


class AbsFieldDynArray(collections.OrderedDict, AbsFieldHelperClass):
    """Class for dynamic arrays AdvancedBinaryStructure fields.
    """
    class LengthField(AbsFieldInteger):
        def __init__(self, spec, data=None, offset=0, context=None):
            super(AbsFieldDynArray.LengthField, self).__init__(spec, data, offset, context)
            self._parse_args(spec, data, offset, context)

        def __repr__(self):
            return '{value:d} elements (0x{value:0{width}X}){tagged:s}' \
                .format(value=self._value,
                        width=(self._bit_width + 3) // 4,
                        tagged=' <TAGGED>' if self._is_tagged else '')

    class SizeField(AbsFieldInteger):
        def __init__(self, spec, data=None, offset=0, context=None):
            super(AbsFieldDynArray.SizeField, self).__init__(spec, data, offset, context)
            self._parse_args(spec, data, offset, context)
            self._unit = 0
            self._excl = False

        def set_unit_excl(self, unit, excl):
            self._unit = unit
            self._excl = excl

        def __repr__(self):
            if self._unit == 8:
                l_unit = ' bytes'
            elif self._unit == 16:
                l_unit = ' word16'
            elif self._unit == 32:
                l_unit = ' word32'
            elif self._unit == 64:
                l_unit = ' word64'
            else:
                raise AbsDecodingError
            if self._excl:
                l_header = 'header excluded'
            else:
                l_header = 'including header'
            return '{value:d}{unit:s}, {header:s} (0x{value:0{width}X}){tagged:s}' \
                .format(value=self._value,
                        unit=l_unit,
                        header=l_header,
                        width=(self._bit_width + 3) // 4,
                        tagged=' <TAGGED>' if self._is_tagged else '')

    def __init__(self, spec, data=None, offset=0, context=None):
        super(AbsFieldDynArray, self).__init__()
        AbsFieldHelperClass.__init__(self)
        self._header_type = None
        self._header_bitwidth = 0
        self._child_spec = None
        self._parse_args(spec, data, offset, context)

    def _decode_spec(self, spec):
        self._id = spec[1]
        self._header_type = spec[2]
        self._header_bitwidth = spec[3]
        if len(spec) == 5:
            if type(spec[4]) == list:
                self._child_spec = ('child', spec[4])
            elif issubclass(spec[4], AbsFieldHelperClass):
                self._child_spec = ('child', spec[3], spec[4])
            else:
                raise AbsDecodingError
        else:
            self._child_spec = ('child', spec[3])

    def _decode_data(self, spec, data, offset=0, context=None):
        if context is None:
            l_context = {}
        else:
            l_context = context

            # First decode the header
        l_offset = offset
        (l_byte_addr, l_byte_offset) = HexUtils.to_bitwise_addr(l_offset)
        if self._header_type == SIZE_EXCL:
            l_header = AbsFactory.make(('size', self._header_bitwidth, AbsFieldDynArray.SizeField),
                                       data[l_byte_addr:],
                                       l_byte_offset,
                                       l_context)
            l_header.set_unit_excl(self._header_bitwidth, True)

        elif self._header_type == SIZE_INCL:
            l_header = AbsFactory.make(('size', self._header_bitwidth, AbsFieldDynArray.SizeField),
                                       data[l_byte_addr:],
                                       l_byte_offset,
                                       l_context)
            l_header.set_unit_excl(self._header_bitwidth, False)

        elif self._header_type == NB_ELTS:
            l_header = AbsFactory.make(('length', self._header_bitwidth,
                                        AbsFieldDynArray.LengthField),
                                       data[l_byte_addr:],
                                       l_byte_offset,
                                       l_context)
        else:
            raise AbsDecodingError
        self[l_header.id()] = l_header
        l_offset += l_header.bit_width()

        self['data'] = []
        if self._header_type == NB_ELTS:
            for i in range(l_header.value()):
                (l_byte_addr, l_byte_offset) = HexUtils.to_bitwise_addr(l_offset)
                self['data'].append(AbsFactory.make(self._child_spec,
                                                    data[l_byte_addr:],
                                                    l_byte_offset))
                l_offset += self['data'][-1].bit_width()
        else:
            if self._header_type == SIZE_INCL:
                l_end_offset = offset + l_header.value() * l_header.bit_width()
            elif self._header_type == SIZE_EXCL:
                l_end_offset = offset + (l_header.value() + 1) * l_header.bit_width()
            else:
                raise AbsDecodingError
            while l_offset < l_end_offset:
                (l_byte_addr, l_byte_offset) = HexUtils.to_bitwise_addr(l_offset)
                self['data'].append(AbsFactory.make(self._child_spec,
                                                    data[l_byte_addr:],
                                                    l_byte_offset))
                l_offset += self['data'][-1].bit_width()

        self._bit_width = l_offset - offset


if __name__ == "__main__":
    import doctest
    doctest.testmod(verbose=True, report=True, optionflags=doctest.REPORT_NDIFF,
                    exclude_empty=True)
