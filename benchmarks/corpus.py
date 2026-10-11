"""Shared inputs for the C and Rust Python API benchmarks."""

REFERENCE_COMMIT = "0ec8b64c1e062529f178b48d4dc6b02a626fa45c"

CASES = {
    "empty": "",
    "one character": "a",
    "short word": "foobar",
    "English sentence": "The quick brown fox jumps over the lazy dog.",
    "English paragraph": (
        "Nothing is more difficult, and therefore more precious, "
        "than to be able to decide. This is an example of what works "
        "very well with smaz."
    ),
    "URL": "http://github.com/antirez/smaz/tree/master",
    "numbers": "1000 numbers 2000 will 10 20 30 compress very little",
    "Italian": "Nel mezzo del cammin di nostra vita, mi ritrovai in una selva oscura",
    "Unicode": "Grüße aus Österreich! Καλημέρα κόσμε! こんにちは世界 🌍😀",
    "literal run 255": "X" * 255,
    "literal run 256": "X" * 256,
    "literal run 257": "X" * 257,
    "alternating literals": "Xt" * 128,
    "English 4 KiB": ("the quick brown fox jumps over the lazy dog. " * 96)[:4095],
    "Unicode 4 KiB": "😀" * 1023,
}


def load_rust():
    import smaz

    native = getattr(smaz, "smaz", smaz)
    if getattr(native, "_build_profile", None) != "release":
        raise RuntimeError(
            "Build the Rust extension in release mode before benchmarking."
        )
    return smaz, native


def prepare_inputs(module):
    """Precompress inputs and check round trips outside the timed region."""
    inputs = []
    for name, text in CASES.items():
        # The unchanged C decoder leaks when it grows its 4096-byte buffer.
        if len(text.encode("utf-8")) >= 4096:
            raise ValueError(f"{name}: decoded input must stay below 4096 bytes")
        encoded = module.compress(text)
        if module.decompress(encoded) != text:
            raise RuntimeError(f"{name}: round trip failed")
        inputs.append((name, text, encoded))
    return inputs


def verify_backends():
    """Require byte-for-byte agreement before comparing backend performance."""
    from benchmarks.build_reference import build_reference

    rust, _ = load_rust()
    reference = build_reference()
    if prepare_inputs(reference) != prepare_inputs(rust):
        raise RuntimeError("C and Rust produced different compressed bytes")
