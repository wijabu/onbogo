"""Keyword matching for the user's shopping list against product titles.

Combines Unicode normalization (fixes curly apostrophes, accents, punctuation
drift) with rapidfuzz partial_ratio (tolerates minor brand-spelling mismatch
like "Sweet Baby Rays" vs "Sweet Baby Ray's"). A substring match scores 100 on
partial_ratio, so a single threshold covers both exact and fuzzy hits.
"""

import re
import unicodedata

from rapidfuzz import fuzz


# Similarity floor for a fav to count as matching a product title. Tuned from
# architect review: 87 catches spelling drift ("Rays" vs "Ray's") without
# pulling in unrelated items.
_FUZZY_THRESHOLD = 87

# Curly/smart apostrophes → straight ASCII so "Ray's" and "Ray\u2019s" compare equal.
_SMART_APOSTROPHES = str.maketrans({
    "\u2018": "'", "\u2019": "'", "\u02bc": "'", "\u02bb": "'", "\u201b": "'",
})


def normalize(s):
    """Lowercase, strip accents/punctuation, collapse whitespace."""
    if not s:
        return ""
    s = s.translate(_SMART_APOSTROPHES)
    s = unicodedata.normalize("NFKD", s)
    s = s.encode("ascii", "ignore").decode("ascii")
    s = s.lower()
    s = re.sub(r"[^\w\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def matches(fav, title):
    """True if `fav` is a reasonable match for `title`."""
    norm_fav = normalize(fav)
    norm_title = normalize(title)
    if not norm_fav or not norm_title:
        return False
    return fuzz.partial_ratio(norm_fav, norm_title) >= _FUZZY_THRESHOLD
