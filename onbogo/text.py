"""Text normalization helpers shared across scraper and store modules."""


def fix_encoding(s):
    """Fix double-encoded mojibake (UTF-8 bytes mis-decoded as Latin-1).

    The common failure mode from the Publix API: the API emits UTF-8 bytes
    but the client library decoded them as Latin-1, leaving 'CafÃ©' where
    the original was 'Café'. Round-tripping through Latin-1 → UTF-8 recovers
    the original. If the string was already valid (plain ASCII or correctly
    decoded Unicode), the inner decode will raise and we return the original
    unchanged — so this helper is safe to apply to any string.
    """
    if not s:
        return s
    try:
        return s.encode("latin-1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return s
