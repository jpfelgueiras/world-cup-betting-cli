"""Scrapers package for Portuguese betting sites"""

from .base_scraper import BaseScraper, ScraperError
from .betano_scraper import BetanoScraper
from .betclic_scraper import BetclicScraper
from .solverde_scraper import SolverdeScraper

__all__ = [
    "BaseScraper",
    "ScraperError",
    "BetanoScraper",
    "BetclicScraper",
    "SolverdeScraper",
]
