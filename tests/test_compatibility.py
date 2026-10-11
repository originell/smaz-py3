import ast
import re
from functools import cache

import pytest
from hypothesis import given, settings, strategies as st

import smaz
from benchmarks.build_reference import REFERENCE


@cache
def original_codebook():
    source = (REFERENCE / "smaz" / "smaz.c").read_text()
    block = source.split("static char *Smaz_rcb[254] = {", 1)[1].split("};", 1)[0]
    return [
        ast.literal_eval(literal) for literal in re.findall(r'"(?:\\.|[^"\\])*"', block)
    ]


@pytest.mark.parametrize("code,word", list(enumerate(original_codebook())))
def test_codebook(c_reference, code, word):
    assert smaz.compress(word) == c_reference.compress(word) == bytes([code])
    assert smaz.decompress(bytes([code])) == c_reference.decompress(bytes([code]))


@given(
    st.text(
        alphabet=st.characters(exclude_characters="\x00", exclude_categories=("Cs",))
    )
)
@settings(max_examples=10000)
def test_wire_compatibility(c_reference, string):
    compressed = smaz.compress(string)
    assert compressed == c_reference.compress(string)
    assert c_reference.decompress(compressed) == string
    assert smaz.decompress(c_reference.compress(string)) == string


def test_dictionary_pairs(c_reference):
    for first in original_codebook():
        for second in original_codebook():
            string = first + second
            assert smaz.compress(string) == c_reference.compress(string), repr(string)


@pytest.mark.parametrize("length", [0, 1, 2, 255, 256, 257, 511, 512, 513, 4095])
@pytest.mark.parametrize("character", ["X", "é", "😀", "t"])
def test_literal_and_buffer_boundaries(c_reference, length, character):
    string = character * length
    compressed = smaz.compress(string)
    assert compressed == c_reference.compress(string)
    assert smaz.decompress(compressed) == string


@pytest.mark.parametrize(
    "string",
    ["the " * 16384, "😀" * 16384, "Xt" * 32768],
    ids=["large-English", "large-Unicode", "large-alternating"],
)
def test_large_strings(c_reference, string):
    assert smaz.compress(string) == c_reference.compress(string)
    assert smaz.decompress(smaz.compress(string)) == string


def test_known_wire_format():
    assert smaz.compress("The quick brown fox jumps over the lazy dog.") == (
        b"H\x00\xfeq&\x83\xfek^sA)\xdc\xfa\x00\xfej&-<\x95\xe7\r\x0b\x89\xdbG\x18\x06;n"
    )


@pytest.mark.parametrize("string", ["\x00", "hello\x00world", "é\x00", "\x00the"])
def test_embedded_null_rejected(string):
    with pytest.raises(ValueError, match="embedded null character"):
        smaz.compress(string)


@pytest.mark.parametrize("string", ["\ud800", "hello\udfff"])
def test_surrogates_rejected(string):
    with pytest.raises(UnicodeEncodeError):
        smaz.compress(string)


@pytest.mark.parametrize("data", [b"\xfe", b"\xff", b"\xff\x00", b"\xff\x02ab"])
def test_truncated_data_rejected(data):
    with pytest.raises(ValueError, match="truncated SMAZ"):
        smaz.decompress(data)


@pytest.mark.parametrize("data", [b"\xfe\x80", b"\xff\x01\xc0\xaf"])
def test_invalid_utf8_rejected(data):
    with pytest.raises(UnicodeDecodeError):
        smaz.decompress(data)


def test_decoded_null_preserved():
    assert smaz.decompress(b"\xfe\x00\x01") == "\x00the"


@pytest.mark.parametrize("value", [bytearray(b"a"), memoryview(b"a"), None])
def test_decompress_requires_bytes(value):
    with pytest.raises(TypeError):
        smaz.decompress(value)


def test_positional_only():
    with pytest.raises(TypeError):
        smaz.compress(string="hello")
    with pytest.raises(TypeError):
        smaz.decompress(bytes=b"\x01")


@given(st.binary(max_size=1024))
@settings(max_examples=10000)
def test_arbitrary_compressed_data(data):
    words = original_codebook()
    output = bytearray()
    position = 0
    try:
        while position < len(data):
            code = data[position]
            position += 1
            if code == 254:
                output.append(data[position])
                position += 1
            elif code == 255:
                length = data[position] + 1
                position += 1
                if len(data) - position < length:
                    raise IndexError
                output.extend(data[position : position + length])
                position += length
            else:
                output.extend(words[code].encode("ascii"))
    except IndexError:
        with pytest.raises(ValueError, match="truncated SMAZ"):
            smaz.decompress(data)
        return
    try:
        text = output.decode("utf-8")
    except UnicodeDecodeError:
        with pytest.raises(UnicodeDecodeError):
            smaz.decompress(data)
    else:
        assert smaz.decompress(data) == text
