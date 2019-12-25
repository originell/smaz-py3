# smaz-py3

Small string compression using [_smaz_](https://github.com/antirez/smaz) compression
algorithm.

This library wraps the original C code, so it should be quite fast. It also has a
testsuite that uses [hypothesis](https://hypothesis.readthedocs.io/en/latest/) based
property testing - a fancy way of saying that the tests are run with randomly
generated strings using most of unicode, to better guard against edge cases.

## Why do I need this?

You are working with tons of short strings (text messages, urls,...) and want to save
space.

According to the original code and notes, it achieves best compression with english
strings (up to 50%) that do not contain a ton of numbers. However, any other language
might just work as well (allegedly still up to 30%).

Note that in certain cases it is possible that the compression increases the size.
Keep that in mind and maybe first run some tests. Measuring size is explained in the
example below as well.

## How do I use this?

Let's install:

```sh
$ pip install smaz-py3
```

_Note_: the `-py3` is important. There is an original release, kudos to Benjamin
Sergeant, but it does not work with Python 3+.

Now, a usage example.

```python
import smaz
# First we compress our example sentence.
compressed = smaz.compress("The quick brown fox jumps over the lazy dog.")
# The output is raw bytes. As can be seen in the decompress() call below.
# Now, we decompress these raw bytes again. This should return our example sentence.
decompressed = smaz.decompress(b'H\x00\xfeq&\x83\xfek^sA)\xdc\xfa\x00\xfej&-<\x95\xe7\r\x0b\x89\xdbG\x18\x06;n')
#  This does not fail, which means we have successfully compressed and decompressed
#  without damaging anything.
assert decompressed == "The quick brown fox jumps over the lazy dog."
```

How much did we compress?

```python
# First, we get the actual byte size of our example string.
original_size = len("The quick brown fox jumps over the lazy dog.".encode("utf-8"))  # 44 bytes
# As `compressed` is already raw bytes, we can also call len() on this
compressed_size = len(compressed)  # 31 bytes
compression_ratio = 1 - compressed_size / original_size  # 0.295
```

So we saved about 30% (0.295 \* 100 and some rounding 😉).

If the compression ratio would be below 0, we would have actually increased the
string. Yes, this can happen. Again, smaz works best on _small_ strings.

### A small note about NULL bytes

Currently, `smaz-py3` does not support strings with NULL bytes (`\x00`) in compression:

```python
>>> import smaz
>>> smaz.compress("The quick brown fox\x00 jumps over the lazy dog.")
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
ValueError: embedded null character
```

My reasoning behind this is that in most scenarios you want to clean that away
beforehand anyways. If you think this is wrong, please open up an
[issue on github](https://github.com/originell/smaz-py3). I am happy for further input!

## Migrating from Python 2 `smaz`

If you have been using the [Python 2 `smaz` library](https://pypi.org/project/smaz/),
this Python 3 version exposes the same API, so it is a drop-in replacement.

**Important**: While developing this extension, I think I found a bug in the original
library. Using Python 2.7.16:

```python
>>> import smaz
>>> smaz.compress("The quick brown fox jumps over the lazy dog.")
'H'  # this is wrong.
>>> small = smaz.compress("The quick brown fox jumps over the lazy dog.")
>>> smaz.decompress(small)
'The'  # information lost.
```

So, if you are actually upgrading from this, please make sure that you are not
affected by this. `smaz-py3` is not prone to this bug.

Behind the scenes, smaz uses NULL bytes in compression. However, when converting from
C back to a Python string object, NULL is used to mark the end of the string. The
above sentence, compressed, has the NULL byte right after the `H` (`H\x00\xfeq…`).
That's why it stops right then and there. Again, `smaz-py3` is not affected by this,
mostly because I got lucky in choosing this example sentence.

## Credits

Credit where credit is due. First to [antirez's SMAZ compression](https://github.com/antirez/smaz)
and to the [original python 2 wrapper](https://pypi.org/project/smaz/) by Benjamin
Sergeant.
