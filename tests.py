import smaz


def test_ok():
    raw = "The quick brown fox jumps over the lazy dog"
    compressed = smaz.compress(raw)
    decompressed = smaz.decompress(compressed)
    assert decompressed == raw
