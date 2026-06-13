"""Scrapers package for Portuguese betting sites"""

from .base_scraper import BaseScraper, ScraperError
from .betano_scraper import BetanoScraper
from .betclic_scraper import BetclicScraper
from .bwin_scraper import BwinScraper
from .casinoportugal_scraper import CasinoPortugalScraper
from .esc_scraper import EscScraper
from .goldenpark_scraper import GoldenParkScraper
from .lebull_scraper import LeBullScraper
from .placard_scraper import PlacardScraper
from .solverde_scraper import SolverdeScraper

__all__ = [
    "BaseScraper",
    "ScraperError",
    "BetanoScraper",
    "BetclicScraper",
    "BwinScraper",
    "CasinoPortugalScraper",
    "EscScraper",
    "GoldenParkScraper",
    "LeBullScraper",
    "PlacardScraper",
    "SolverdeScraper",
]
