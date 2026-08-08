"""
UKMapSearcher
=============

A search engine over an already-built uk_map.json (see build_uk_map.py).
This module does NOT build or touch the map data -- it only loads it once
and lets you turn free-text location input into a single best match.

Usage:

    from uk_map_searcher import UKMapSearcher

    searcher = UKMapSearcher("uk_map.json")
    result = searcher.search("Skypark, Exeter, England EX5 2FL")
    if result:
        print(result.place["name"], result.confidence, result.matched_by)
"""

from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path


@dataclass
class LocationMatch:
    place: dict
    confidence: float
    matched_by: str  # postcode_unit | postcode_district | city | county | country | alias | fuzzy
    matched_text: str


_MIN_FUZZY_CONFIDENCE = 0.72

EARTH_RADIUS_MILES = 3958.8


# Matches a full UK postcode anywhere inside a longer string, e.g. pulls
# "EX5 2FL" out of "Skypark, Exeter, England EX5 2FL" or "E7 9NJ" out of
# "London E7 9NJ", or "EX5-2FL" out of "ex5-2fl". Outward: 1-2 letters,
# 1-2 digits, optional letter. Inward: 1 digit + 2 letters. Anything
# non-alphanumeric (space, hyphen, etc.) between the two is allowed.
_POSTCODE_IN_TEXT_RE = re.compile(
    r"\b([A-Za-z]{1,2}\d[A-Za-z\d]?)[^A-Za-z0-9]*(\d[A-Za-z]{2})\b"
)

# A bare postcode district/outward code on its own, e.g. "SW1", "EX5",
# "SW1A" -- letters, digit, optional trailing letter, nothing else.
_POSTCODE_DISTRICT_RE = re.compile(r"^[A-Za-z]{1,2}\d[A-Za-z]?$")


def _normalize_text(text: str) -> str:
    """Lowercase, strip punctuation (keep letters/digits/spaces), collapse
    whitespace. Used for names, counties, countries, aliases, and general
    free-text tokens."""
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _normalize_postcode(text: str) -> str:
    """Uppercase, strip everything but letters/digits, no spaces.
    'ex5 2fl', 'EX52FL', 'Ex5-2FL' all become 'EX52FL'."""
    return re.sub(r"[^A-Z0-9]", "", text.upper())


def _pick_best(candidates: list[dict]) -> dict:
    """When multiple places tie on the same match type, prefer the one
    with the highest population (requirement #12's tiebreaker)."""
    return max(candidates, key=lambda p: p.get("population", 0))


def _haversine_miles(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance between two lat/lon points, in miles."""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * EARTH_RADIUS_MILES * math.asin(math.sqrt(a))


class UKMapSearcher:
    """Loads uk_map.json once and answers location search queries."""

    def __init__(self, map_path: str | Path = "uk_map.json") -> None:
        with open(map_path, encoding="utf-8") as f:
            self.places: list[dict] = json.load(f)

        # O(1) lookup indexes, built once here in __init__.
        self._by_postcode_unit: dict[str, dict] = {}
        self._by_postcode_district: dict[str, list[dict]] = {}
        self._by_city: dict[str, list[dict]] = {}
        self._by_alias: dict[str, list[dict]] = {}
        self._by_county: dict[str, list[dict]] = {}
        self._by_country: dict[str, list[dict]] = {}

        # Flat list of (normalized_text, place) for fuzzy fallback only.
        self._fuzzy_pool: list[tuple[str, dict]] = []

        self._build_indexes()

    # -- Index building -----------------------------------------------------

    def _build_indexes(self) -> None:
        for place in self.places:
            # Postcode units are already unique strings like "SW1A 1AA".
            for unit in place.get("postcode_units", []):
                key = _normalize_postcode(unit)
                self._by_postcode_unit[key] = place

            for district in place.get("postcode_districts", []):
                key = _normalize_postcode(district)
                self._by_postcode_district.setdefault(key, []).append(place)

            name_key = _normalize_text(place.get("name", ""))
            if name_key:
                self._by_city.setdefault(name_key, []).append(place)
                self._fuzzy_pool.append((name_key, place))

            for alias in place.get("aliases", []):
                alias_key = _normalize_text(alias)
                if alias_key:
                    self._by_alias.setdefault(alias_key, []).append(place)

            county_key = _normalize_text(place.get("county", ""))
            if county_key:
                self._by_county.setdefault(county_key, []).append(place)

            country_key = _normalize_text(place.get("country", ""))
            if country_key:
                self._by_country.setdefault(country_key, []).append(place)

    # -- Public API -----------------------------------------------------------

    def search(self, query: str) -> LocationMatch | None:
        """Turn free-text location input into a single best LocationMatch,
        or None if nothing is confident enough."""
        if not query or not query.strip():
            return None

        # 1. Try to find a postcode anywhere in the query -- postcodes are
        #    the strongest, most specific signal, so check them first
        #    regardless of what else is in the string
        #    (e.g. "Skypark, Exeter, England EX5 2FL").
        postcode_match = self._search_postcode(query)
        if postcode_match is not None:
            return postcode_match

        # 2. Try exact matches against city / county / country / alias,
        #    using the whole normalized query as a single token.
        normalized = _normalize_text(query)
        exact_match = self._search_exact(normalized)
        if exact_match is not None:
            return exact_match

        # 3. Try exact matches against individual words/phrases within the
        #    query, in case it's a longer free-text string
        #    ("Green Street West Ward London" -> "london" matches city).
        phrase_match = self._search_within_text(normalized)
        if phrase_match is not None:
            return phrase_match

        # 4. Fall back to fuzzy matching against place names.
        return self._search_fuzzy(normalized)

    # -- Postcode matching -----------------------------------------------------

    def _search_postcode(self, query: str) -> LocationMatch | None:
        stripped = query.strip()

        # 1. Look for a full postcode (outward + inward) anywhere in the
        #    text, e.g. pulling "EX5 2FL" out of "Skypark, Exeter, England
        #    EX5 2FL" or "E7 9NJ" out of "London E7 9NJ". This must run
        #    before any city/county/alias matching so a postcode embedded
        #    in a longer address always wins, per the postcode_unit /
        #    postcode_district priority in requirement #12.
        full_match = _POSTCODE_IN_TEXT_RE.search(stripped)
        if full_match:
            compact = _normalize_postcode(full_match.group(0))
            if compact in self._by_postcode_unit:
                place = self._by_postcode_unit[compact]
                return LocationMatch(
                    place=place, confidence=1.0,
                    matched_by="postcode_unit", matched_text=full_match.group(0).strip(),
                )
            outward = _normalize_postcode(full_match.group(1))
            if outward in self._by_postcode_district:
                place = _pick_best(self._by_postcode_district[outward])
                return LocationMatch(
                    place=place, confidence=0.95,
                    matched_by="postcode_district", matched_text=full_match.group(0).strip(),
                )

        # 2. No full postcode found (or its district wasn't in the data) --
        #    check whether the ENTIRE query, on its own, looks like a bare
        #    postcode district ("SW1", "EX5", "SW1A"). Only applies when
        #    the whole (whitespace-stripped) query is just that district,
        #    so free text like "London" doesn't get treated as a district.
        compact_whole = _normalize_postcode(stripped)
        if compact_whole and _POSTCODE_DISTRICT_RE.match(compact_whole):
            if compact_whole in self._by_postcode_district:
                place = _pick_best(self._by_postcode_district[compact_whole])
                return LocationMatch(
                    place=place, confidence=0.9,
                    matched_by="postcode_district", matched_text=stripped,
                )
            # Not an exact district (e.g. "SW1" has no places directly under
            # it, only "SW1A", "SW1E", ...) -- try it as a PREFIX match
            # across all known districts, since that's clearly what the
            # user means by a shortened outward code.
            prefix_candidates: list[dict] = []
            for district, places in self._by_postcode_district.items():
                if district.startswith(compact_whole):
                    prefix_candidates.extend(places)
            if prefix_candidates:
                place = _pick_best(prefix_candidates)
                return LocationMatch(
                    place=place, confidence=0.8,
                    matched_by="postcode_district", matched_text=stripped,
                )

        return None

    # -- Exact matching -----------------------------------------------------

    def _search_exact(self, normalized: str) -> LocationMatch | None:
        if normalized in self._by_city:
            place = _pick_best(self._by_city[normalized])
            return LocationMatch(
                place=place, confidence=1.0, matched_by="city", matched_text=normalized,
            )
        if normalized in self._by_county:
            place = _pick_best(self._by_county[normalized])
            return LocationMatch(
                place=place, confidence=0.9, matched_by="county", matched_text=normalized,
            )
        if normalized in self._by_country:
            place = _pick_best(self._by_country[normalized])
            return LocationMatch(
                place=place, confidence=0.85, matched_by="country", matched_text=normalized,
            )
        if normalized in self._by_alias:
            place = _pick_best(self._by_alias[normalized])
            return LocationMatch(
                place=place, confidence=0.95, matched_by="alias", matched_text=normalized,
            )
        return None

    def _search_within_text(self, normalized: str) -> LocationMatch | None:
        """For longer free-text queries, look for a known city/county/
        country/alias as a word run within the text. Checks longer runs
        first so multi-word place names are preferred over single-word
        partial matches, and checks city > county > country > alias in
        that priority order (requirement #12)."""
        words = normalized.split()
        if len(words) <= 1:
            return None  # already covered by _search_exact

        runs: list[str] = []
        for length in range(len(words), 0, -1):
            for start in range(0, len(words) - length + 1):
                runs.append(" ".join(words[start:start + length]))

        for index, matched_by, confidence in (
            (self._by_city, "city", 1.0),
            (self._by_county, "county", 0.9),
            (self._by_country, "country", 0.85),
            (self._by_alias, "alias", 0.95),
        ):
            for run in runs:
                if run in index:
                    place = _pick_best(index[run])
                    return LocationMatch(
                        place=place, confidence=confidence,
                        matched_by=matched_by, matched_text=run,
                    )
        return None

    # -- Fuzzy fallback -----------------------------------------------------

    def _search_fuzzy(self, normalized: str) -> LocationMatch | None:
        """Fuzzy fallback using stdlib difflib against place names only.
        Only reached when nothing matched exactly."""
        best_place: dict | None = None
        best_ratio = 0.0

        for name_key, place in self._fuzzy_pool:
            ratio = SequenceMatcher(None, normalized, name_key).ratio()
            if ratio > best_ratio:
                best_ratio = ratio
                best_place = place

        if best_place is not None and best_ratio >= _MIN_FUZZY_CONFIDENCE:
            return LocationMatch(
                place=best_place, confidence=round(best_ratio, 3),
                matched_by="fuzzy", matched_text=normalized,
            )
        return None

    # -- Radius search -----------------------------------------------------

    def _resolve_coords(self, address_or_coords: str | tuple[float, float]) -> tuple[float, float] | None:
        """Accept either a free-text address (resolved via search()) or an
        explicit (lat, lon) tuple, and return coordinates either way.

        Passing (lat, lon) directly is a way to sidestep ambiguous place
        names -- e.g. search("Clifton") can't know which of the UK's many
        same-named Cliftons you mean, but (53.9762, -1.0932) always points
        to exactly one spot."""
        if isinstance(address_or_coords, tuple):
            return address_or_coords

        match = self.search(address_or_coords)
        if match is None:
            return None
        return match.place["lat"], match.place["lon"]

    def find_within_radius(
        self, address: str | tuple[float, float], radius_mi: float
    ) -> list[dict]:
        """Given an address (free text, or an explicit (lat, lon) tuple)
        and a radius in miles, return every place whose coordinates fall
        within that radius, sorted nearest-first.

        Returns an empty list if `address` doesn't resolve to anything, or
        if no places fall within the radius. The origin place itself
        (distance 0) is included if it matches a real place in the data.

        Example:
            searcher.find_within_radius("Skypark, Exeter, England EX5 2FL", 50)
            -> [ {...place dict...}, {...place dict...}, ... ]  # nearest first

            # Or, to sidestep an ambiguous name like "Clifton":
            searcher.find_within_radius((53.9762, -1.0932), 5)
        """
        origin = self._resolve_coords(address)
        if origin is None:
            return []
        origin_lat, origin_lon = origin

        results: list[tuple[float, dict]] = []
        for place in self.places:
            distance = _haversine_miles(origin_lat, origin_lon, place["lat"], place["lon"])
            if distance <= radius_mi:
                results.append((distance, place))

        results.sort(key=lambda pair: pair[0])
        return [place for _distance, place in results]

    def is_within_radius(
        self,
        address: str | tuple[float, float],
        radius_mi: float,
        target_address: str | tuple[float, float],
    ) -> bool:
        """Given an origin address, a radius in miles, and a target
        address, return True if the target falls within that radius of the
        origin, False otherwise (including if either address fails to
        resolve). Both `address` and `target_address` accept either
        free-text or an explicit (lat, lon) tuple -- see find_within_radius
        for why you might want to pass coordinates directly.

        Example:
            searcher.is_within_radius(
                "Skypark, Exeter, England EX5 2FL", 50, "Exmouth"
            )
            -> True
        """
        origin = self._resolve_coords(address)
        target = self._resolve_coords(target_address)
        if origin is None or target is None:
            return False

        distance = _haversine_miles(origin[0], origin[1], target[0], target[1])
        return distance <= radius_mi

if __name__ == "__main__":
    searcher = UKMapSearcher("uk_map.json")

    print(searcher.is_within_radius("London", 50, "Exeter"))
