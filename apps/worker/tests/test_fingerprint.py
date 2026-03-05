"""Tests for myscout.canonicalization.fingerprint pure functions."""

from myscout.canonicalization.fingerprint import normalize_text, generate_fingerprint


# ── normalize_text ──────────────────────────────────────────────


class TestNormalizeText:
    def test_lowercases(self):
        assert normalize_text("HELLO WORLD") == "hello world"

    def test_strips_punctuation(self):
        assert normalize_text("Hello, World!") == "hello world"

    def test_collapses_whitespace(self):
        assert normalize_text("  hello   world  ") == "hello world"

    def test_none_returns_empty(self):
        assert normalize_text(None) == ""

    def test_empty_string(self):
        assert normalize_text("") == ""

    def test_preserves_alphanumeric(self):
        assert normalize_text("python3 react18") == "python3 react18"


# ── generate_fingerprint ────────────────────────────────────────


class TestGenerateFingerprint:
    def test_returns_hex_string(self):
        fp = generate_fingerprint("Acme", "Engineer", "NYC", "Build things")
        assert isinstance(fp, str)
        assert len(fp) == 64  # SHA-256 hex

    def test_deterministic(self):
        args = ("Acme", "Software Engineer", "NYC", "Great job")
        assert generate_fingerprint(*args) == generate_fingerprint(*args)

    def test_case_insensitive(self):
        fp1 = generate_fingerprint("ACME", "SOFTWARE ENGINEER", "NYC", "desc")
        fp2 = generate_fingerprint("acme", "software engineer", "nyc", "desc")
        assert fp1 == fp2

    def test_punctuation_insensitive(self):
        fp1 = generate_fingerprint("Acme, Inc.", "Sr. Engineer", "NY", "desc")
        fp2 = generate_fingerprint("Acme Inc", "Sr Engineer", "NY", "desc")
        assert fp1 == fp2

    def test_different_inputs_differ(self):
        fp1 = generate_fingerprint("Acme", "Engineer", "NYC", "desc")
        fp2 = generate_fingerprint("Acme", "Designer", "NYC", "desc")
        assert fp1 != fp2

    def test_none_location_defaults_to_remote(self):
        fp1 = generate_fingerprint("Acme", "Engineer", None, "desc")
        fp2 = generate_fingerprint("Acme", "Engineer", "remote", "desc")
        assert fp1 == fp2

    def test_long_description_truncated(self):
        # Fingerprint only uses first 600 chars of description
        desc_short = "x" * 600
        desc_long = "x" * 600 + "y" * 1000
        fp1 = generate_fingerprint("Acme", "Eng", "NYC", desc_short)
        fp2 = generate_fingerprint("Acme", "Eng", "NYC", desc_long)
        assert fp1 == fp2
