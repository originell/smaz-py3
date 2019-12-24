import smaz


def test_compression():
    import ipdb

    ipdb.set_trace()
    uncompressed = "The quick brown fox jumps over the lazy dog"
    compressed = smaz.compress(uncompressed)
