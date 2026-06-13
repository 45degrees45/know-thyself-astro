"""
AstroService — wraps astro_engine/ calculation modules.

Provides calculate() and build_summary() for chart generation and summarisation.
"""
import sys
import os
from datetime import datetime, timezone

# Add astro_engine/ to path so we can import its modules directly
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "astro_engine"))

from geo import geocode
from calc import calculate_chart
from dasha import current_period
from yoga import find_yogas

# Jyotish nakshatra → spirit animal mapping
MOON_ANIMAL = {
    "Ashwini":            ("Horse",     "🐎"),
    "Bharani":            ("Elephant",  "🐘"),
    "Krittika":           ("Goat",      "🐐"),
    "Rohini":             ("Serpent",   "🐍"),
    "Mrigashira":         ("Serpent",   "🐍"),
    "Ardra":              ("Dog",       "🐕"),
    "Punarvasu":          ("Cat",       "🐈"),
    "Pushya":             ("Goat",      "🐐"),
    "Ashlesha":           ("Cat",       "🐈"),
    "Magha":              ("Rat",       "🐀"),
    "Purva Phalguni":     ("Rat",       "🐀"),
    "Uttara Phalguni":    ("Cow",       "🐄"),
    "Hasta":              ("Buffalo",   "🦬"),
    "Chitra":             ("Tiger",     "🐅"),
    "Swati":              ("Buffalo",   "🦬"),
    "Vishakha":           ("Tiger",     "🐅"),
    "Anuradha":           ("Deer",      "🦌"),
    "Jyeshtha":           ("Deer",      "🦌"),
    "Mula":               ("Dog",       "🐕"),
    "Purva Ashadha":      ("Monkey",    "🐒"),
    "Uttara Ashadha":     ("Mongoose",  "🦡"),
    "Shravana":           ("Monkey",    "🐒"),
    "Dhanishtha":         ("Lion",      "🦁"),
    "Shatabhisha":        ("Horse",     "🐎"),
    "Purva Bhadrapada":   ("Lion",      "🦁"),
    "Uttara Bhadrapada":  ("Cow",       "🐄"),
    "Revati":             ("Elephant",  "🐘"),
}


class AstroService:
    def calculate(self, birth_date: str, birth_time: str, birth_place: str) -> dict:
        """
        Calculate a full Vedic birth chart.

        Returns a dict with lagna, planets, yogas, dasha, and spirit animal.
        """
        geo = geocode(birth_place)
        chart = calculate_chart(
            birth_date, birth_time,
            geo["lat"], geo["lon"], geo["timezone"],
        )

        yogas = find_yogas(chart)

        # current_period needs (moon_lon: float, birth_dt: naive-UTC datetime)
        moon_lon = chart["planets"]["Moon"]["longitude"]
        birth_dt = datetime.fromisoformat(chart["birth_utc"]).replace(tzinfo=None)
        dasha = current_period(moon_lon, birth_dt)

        # dasha keys: {"mahadasha": {"planet": ...}, "bhukti": {"planet": ...}, "antara": {"planet": ...}}
        maha = dasha.get("mahadasha", {}).get("planet", "")
        bhuk = dasha.get("bhukti", {}).get("planet", "")
        anta = dasha.get("antara", {}).get("planet", "")
        dasha_str = "/".join(p for p in [maha, bhuk, anta] if p)

        moon_nakshatra = chart["planets"]["Moon"]["nakshatra"]
        animal_name, animal_emoji = MOON_ANIMAL.get(moon_nakshatra, ("Eagle", "🦅"))

        return {
            "lagna":          chart["ascendant"]["sign"],
            "lagna_deg":      round(chart["ascendant"]["degrees"], 2),
            "planets":        chart["planets"],
            "moon_nakshatra": moon_nakshatra,
            "yogas":          [y["name"] for y in yogas],
            "yoga_details":   yogas,
            "current_dasha":  dasha_str,
            "animal":         animal_name,
            "animal_emoji":   animal_emoji,
            "raw_chart":      chart,
        }

    def build_summary(self, chart_json: dict) -> dict:
        """
        Distil a full calculate() result into a lightweight summary dict.
        """
        return {
            "lagna":        chart_json["lagna"],
            "lagna_deg":    chart_json["lagna_deg"],
            "current_dasha": chart_json["current_dasha"],
            "yogas":        chart_json["yogas"][:3],
            "animal":       chart_json["animal"],
            "animal_emoji": chart_json["animal_emoji"],
        }
