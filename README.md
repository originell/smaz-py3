# smaz-py3

[![Downloads/month](https://img.shields.io/pypi/dm/smaz-py3)](https://pypistats.org/packages/smaz-py3)
[![PyPI version](https://img.shields.io/pypi/v/smaz-py3)](https://pypi.org/project/smaz-py3/)
[![CI](https://img.shields.io/github/actions/workflow/status/originell/smaz-py3/main.yml?branch=main&label=CI)](https://github.com/originell/smaz-py3/actions/workflows/main.yml)
[![Python versions](https://img.shields.io/pypi/pyversions/smaz-py3)](https://pypi.org/project/smaz-py3/)

Small string compression using [_smaz_](https://github.com/antirez/smaz) compression
algorithm.

Support follows Python's upstream lifecycle, including security fixes. The current
supported releases are Python 3.11–3.15.

Version 2.0 uses Rust while preserving the `compress()` and `decompress()` API
and the SMAZ compressed format. You can reuse data compressed with 1.x.
Building from source requires Rust 1.83 or newer; installing a prebuilt wheel
does not require a Rust compiler.

## Why do I need this?

Use smaz when you store or send many short text values individually, and saving a
few bytes per value adds up. Examples include status messages, short descriptions
in database records or caches, paths, and URLs.

Here are some actual sizes, comparing UTF-8 input with `smaz.compress()` output:

| Text | UTF-8 bytes | Compressed bytes |
| --- | ---: | ---: |
| `waiting for approval` | 20 | 11 |
| `the connection was closed` | 25 | 12 |
| `/users/settings` | 15 | 10 |
| `http://example.com` | 18 | 8 |
| `12345678901234567890` | 20 | 22 |

smaz's built-in dictionary works well with common English text. Numbers and text
that the dictionary cannot match can get larger, as the last example shows.
Measure your own data before choosing it. The usage example below shows how to
measure the sizes.

## How do I use this?

Let's install:

```sh
$ uv add smaz-py3
```

_Note_: the `-py3` is important. There is an original release, kudos to Benjamin
Sergeant, but it does not work with Python 3+.

Now, a usage example.

```python
import smaz
# First we compress our example sentence.
compressed = smaz.compress("The quick brown fox jumps over the lazy dog.")
# The output is raw bytes. As can be seen in the decompress() call below.
# Now, we decompress these raw bytes again. This should return our example
# sentence.
decompressed = smaz.decompress(b'H\x00\xfeq&\x83\xfek^sA)\xdc\xfa\x00\xfej&-<\x95\xe7\r\x0b\x89\xdbG\x18\x06;n')
# This does not fail, which means we have successfully compressed and
# decompressed without damaging anything.
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

### Decoder errors

Catch `ValueError` for incomplete SMAZ literals. For example,
`decompress(b"\xfe")` fails because the literal marker has no following byte.
Catch `UnicodeDecodeError` when the decoded bytes are not valid UTF-8.

When decoding SMAZ data from another source, expect `decompress()` to preserve
embedded NUL characters (`\x00`) and the text after them. The old C wrapper
truncated output at the first NUL. Remove or replace embedded NULs before
calling `compress()`; otherwise, it raises `ValueError`.

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

Behind the scenes, smaz uses NUL bytes in compression. However, when converting from
C back to a Python string object, NUL is used to mark the end of the string. The
above sentence, compressed, has the NUL byte right after the `H` (`H\x00\xfeq…`).
That's why it stops right then and there. Again, `smaz-py3` is not affected by this,
mostly because I got lucky in choosing this example sentence.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup, tests, Git hooks,
benchmarks, and distribution builds.

## Credits

Credit where credit is due. First to [antirez's SMAZ compression](https://github.com/antirez/smaz)
and to the [original python 2 wrapper](https://pypi.org/project/smaz/) by Benjamin
Sergeant.
