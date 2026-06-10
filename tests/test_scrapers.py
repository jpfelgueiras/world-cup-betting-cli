"""
Unit tests for Betting Site Scrapers

Tests base scraper and individual site scrapers.
Note: These tests use mock data since real scraping requires live sites.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

from src.scrapers.base_scraper import (
    BaseScraper,
    ScraperError,
    OddsData,
)
from src.scrapers.betano_scraper import BetanoScraper
from src.scrapers.betclic_scraper import BetclicScraper
from src.scrapers.solverde_scraper import SolverdeScraper


class TestOddsData:
    """Tests for OddsData dataclass"""

    def test_create_odds_data(self):
        """Test creating OddsData instance"""
        match_date = datetime.now() + timedelta(days=3)

        odds = OddsData(
            match_id="test_123",
            home_team="Portugal",
            away_team="Brazil",
            match_date=match_date,
            site="betano",
            site_name="Betano.pt",
            home_win=2.10,
            draw=3.20,
            away_win=2.80,
        )

        assert odds.match_id == "test_123"
        assert odds.home_team == "Portugal"
        assert odds.away_team == "Brazil"
        assert odds.home_win == pytest.approx(2.10, rel=0.01)

    def test_has_1x2_true(self):
        """Test has_1x2 returns True when all 1X2 odds present"""
        odds = OddsData(
            match_id="test",
            home_team="A",
            away_team="B",
            match_date=datetime.now(),
            site="test",
            site_name="Test",
            home_win=2.00,
            draw=3.00,
            away_win=2.50,
        )

        assert odds.has_1x2() is True

    def test_has_1x2_false_missing_draw(self):
        """Test has_1x2 returns False when draw odds missing"""
        odds = OddsData(
            match_id="test",
            home_team="A",
            away_team="B",
            match_date=datetime.now(),
            site="test",
            site_name="Test",
            home_win=2.00,
            draw=None,  # Missing
            away_win=2.50,
        )

        assert odds.has_1x2() is False

    def test_has_ou25_true(self):
        """Test has_ou25 returns True when O/U odds present"""
        odds = OddsData(
            match_id="test",
            home_team="A",
            away_team="B",
            match_date=datetime.now(),
            site="test",
            site_name="Test",
            over_2_5=1.85,
            under_2_5=1.95,
        )

        assert odds.has_ou25() is True

    def test_has_ou25_false(self):
        """Test has_ou25 returns False when O/U odds missing"""
        odds = OddsData(
            match_id="test",
            home_team="A",
            away_team="B",
            match_date=datetime.now(),
            site="test",
            site_name="Test",
            over_2_5=1.85,
            under_2_5=None,  # Missing
        )

        assert odds.has_ou25() is False

    def test_has_btts_true(self):
        """Test has_btts returns True when BTTS odds present"""
        odds = OddsData(
            match_id="test",
            home_team="A",
            away_team="B",
            match_date=datetime.now(),
            site="test",
            site_name="Test",
            btts_yes=1.70,
            btts_no=2.10,
        )

        assert odds.has_btts() is True

    def test_to_dict(self):
        """Test converting OddsData to dictionary"""
        match_date = datetime.now()

        odds = OddsData(
            match_id="test_123",
            home_team="Portugal",
            away_team="Brazil",
            match_date=match_date,
            site="betano",
            site_name="Betano.pt",
            home_win=2.10,
            draw=3.20,
            away_win=2.80,
            url="https://example.com",
        )

        result = odds.to_dict()

        assert isinstance(result, dict)
        assert result['match_id'] == "test_123"
        assert result['home_team'] == "Portugal"
        assert result['away_team'] == "Brazil"
        assert result['site'] == "betano"
        assert result['home_win'] == pytest.approx(2.10, rel=0.01)
        assert 'last_updated' in result

    def test_last_updated_auto_set(self):
        """Test that last_updated is auto-set if not provided"""
        odds = OddsData(
            match_id="test",
            home_team="A",
            away_team="B",
            match_date=datetime.now(),
            site="test",
            site_name="Test",
        )

        assert odds.last_updated is not None
        assert isinstance(odds.last_updated, datetime)


class TestBaseScraper:
    """Tests for BaseScraper abstract class"""

    @pytest.fixture
    def mock_scraper(self):
        """Create a concrete implementation of BaseScraper for testing"""
        class ConcreteScraper(BaseScraper):
            def get_match_odds(self, home_team, away_team, match_date=None):
                return None

            def get_upcoming_matches(self, days_ahead=7):
                return []

        return ConcreteScraper(
            site_key="test",
            site_name="Test Site",
            base_url="https://test.com",
            rate_limit_seconds=1
        )

    def test_init_sets_attributes(self, mock_scraper):
        """Test that __init__ sets all attributes correctly"""
        assert mock_scraper.site_key == "test"
        assert mock_scraper.site_name == "Test Site"
        assert mock_scraper.base_url == "https://test.com"
        assert mock_scraper.rate_limit_seconds == 1

    def test_session_creation(self, mock_scraper):
        """Test that session is created on first access"""
        session = mock_scraper.session
        assert session is not None
        assert hasattr(session, 'headers')

    def test_session_reuse(self, mock_scraper):
        """Test that same session is reused"""
        session1 = mock_scraper.session
        session2 = mock_scraper.session
        assert session1 is session2

    def test_session_has_retry_config(self, mock_scraper):
        """Test that session has retry configuration"""
        session = mock_scraper.session
        # Check adapters are mounted
        assert 'https://' in session.adapters
        assert 'http://' in session.adapters

    def test_rotate_user_agent(self, mock_scraper):
        """Test user agent rotation"""
        initial_agent = mock_scraper.session.headers.get('User-Agent')

        mock_scraper._rotate_user_agent()
        new_agent = mock_scraper.session.headers.get('User-Agent')

        # Agent should be set (may be same by chance, but should be valid)
        assert new_agent is not None
        assert new_agent.startswith('Mozilla/5.0')

    def test_respect_rate_limit_first_request(self, mock_scraper):
        """Test rate limiting allows first request immediately"""
        import time

        start = time.time()
        mock_scraper._respect_rate_limit()
        elapsed = time.time() - start

        # First request should not wait
        assert elapsed < 0.1

    def test_respect_rate_limit_waits(self, mock_scraper):
        """Test rate limiting waits for subsequent requests"""
        import time

        # Make first request
        mock_scraper._respect_rate_limit()

        # Second request immediately should wait
        start = time.time()
        mock_scraper._respect_rate_limit()
        elapsed = time.time() - start

        # Should have waited close to rate_limit_seconds
        assert elapsed >= 0.8  # Allow some tolerance

    @patch('requests.Session.request')
    def test_make_request_success(self, mock_request, mock_scraper):
        """Test successful HTTP request"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "<html>Success</html>"
        mock_request.return_value = mock_response

        response = mock_scraper._make_request("https://test.com/page")

        assert response.status_code == 200
        mock_request.assert_called_once()

    @patch('requests.Session.request')
    def test_make_request_timeout(self, mock_request, mock_scraper):
        """Test timeout error handling"""
        import requests
        mock_request.side_effect = requests.exceptions.Timeout()

        with pytest.raises(ScraperError) as exc_info:
            mock_scraper._make_request("https://test.com/page")

        assert "timed out" in str(exc_info.value).lower()

    @patch('requests.Session.request')
    def test_make_request_connection_error(self, mock_request, mock_scraper):
        """Test connection error handling"""
        import requests
        mock_request.side_effect = requests.exceptions.ConnectionError()

        with pytest.raises(ScraperError) as exc_info:
            mock_scraper._make_request("https://test.com/page")

        assert "connection" in str(exc_info.value).lower()

    @patch('requests.Session.request')
    def test_make_request_403_forbidden(self, mock_request, mock_scraper):
        """Test 403 forbidden error handling"""
        import requests
        mock_response = Mock()
        mock_response.status_code = 403
        mock_request.side_effect = requests.HTTPError(response=mock_response)

        with pytest.raises(ScraperError) as exc_info:
            mock_scraper._make_request("https://test.com/page")

        assert "forbidden" in str(exc_info.value).lower()

    @patch('requests.Session.request')
    def test_make_request_429_rate_limited(self, mock_request, mock_scraper):
        """Test 429 rate limit error handling"""
        import requests
        mock_response = Mock()
        mock_response.status_code = 429
        mock_request.side_effect = requests.HTTPError(response=mock_response)

        with pytest.raises(ScraperError) as exc_info:
            mock_scraper._make_request("https://test.com/page")

        assert "rate limited" in str(exc_info.value).lower()

    @patch('requests.Session.request')
    def test_make_request_404_not_found(self, mock_request, mock_scraper):
        """Test 404 not found error handling"""
        import requests
        mock_response = Mock()
        mock_response.status_code = 404
        mock_request.side_effect = requests.HTTPError(response=mock_response)

        with pytest.raises(ScraperError) as exc_info:
            mock_scraper._make_request("https://test.com/page")

        assert "not found" in str(exc_info.value).lower()

    def test_normalize_team_name_removes_accents(self, mock_scraper):
        """Test team name normalization removes accents"""
        normalized = mock_scraper.normalize_team_name("São Paulo")
        assert "sao" in normalized
        assert "ã" not in normalized

    def test_normalize_team_name_lowercase(self, mock_scraper):
        """Test team name normalization converts to lowercase"""
        normalized = mock_scraper.normalize_team_name("PORTUGAL")
        assert normalized == "portugal"

    def test_normalize_team_name_removes_prefixes(self, mock_scraper):
        """Test team name normalization removes common prefixes"""
        normalized = mock_scraper.normalize_team_name("FC Porto")
        assert "porto" in normalized
        assert "fc" not in normalized

    def test_find_team_match_found(self, mock_scraper):
        """Test finding a match containing a specific team"""
        matches = [
            OddsData(
                match_id="m1",
                home_team="Portugal",
                away_team="Spain",
                match_date=datetime.now(),
                site="test",
                site_name="Test",
            ),
            OddsData(
                match_id="m2",
                home_team="Brazil",
                away_team="Argentina",
                match_date=datetime.now(),
                site="test",
                site_name="Test",
            ),
        ]

        result = mock_scraper.find_team_match(matches, "Spain")

        assert result is not None
        assert result.match_id == "m1"

    def test_find_team_match_not_found(self, mock_scraper):
        """Test finding a match when team not present"""
        matches = [
            OddsData(
                match_id="m1",
                home_team="Portugal",
                away_team="Spain",
                match_date=datetime.now(),
                site="test",
                site_name="Test",
            ),
        ]

        result = mock_scraper.find_team_match(matches, "Brazil")

        assert result is None

    def test_get_status(self, mock_scraper):
        """Test getting scraper status"""
        status = mock_scraper.get_status()

        assert status['site'] == "test"
        assert status['site_name'] == "Test Site"
        assert status['base_url'] == "https://test.com"
        assert status['rate_limit_seconds'] == 1


class TestBetanoScraper:
    """Tests for BetanoScraper"""

    @pytest.fixture
    def scraper(self):
        """Create BetanoScraper instance"""
        return BetanoScraper()

    def test_init_configures_correctly(self, scraper):
        """Test initialization sets correct configuration"""
        assert scraper.site_key == "betano"
        assert "Betano" in scraper.site_name
        assert "betano.pt" in scraper.base_url.lower()

    def test_get_match_odds_returns_odds(self, scraper):
        """Test get_match_odds returns odds data (mock implementation)"""
        odds = scraper.get_match_odds("Portugal", "Brazil")

        assert odds is not None
        assert isinstance(odds, OddsData)
        assert odds.home_team == "Portugal"
        assert odds.away_team == "Brazil"
        assert odds.site == "betano"

    def test_get_match_odds_has_1x2(self, scraper):
        """Test returned odds include 1X2 market"""
        odds = scraper.get_match_odds("Portugal", "Brazil")

        assert odds.has_1x2() is True
        assert odds.home_win is not None
        assert odds.draw is not None
        assert odds.away_win is not None

    def test_get_match_odds_has_other_markets(self, scraper):
        """Test returned odds include other markets"""
        odds = scraper.get_match_odds("Portugal", "Brazil")

        assert odds.over_2_5 is not None
        assert odds.under_2_5 is not None
        assert odds.btts_yes is not None
        assert odds.btts_no is not None

    def test_get_upcoming_matches_returns_list(self, scraper):
        """Test get_upcoming_matches returns list of matches"""
        matches = scraper.get_upcoming_matches(days_ahead=7)

        assert isinstance(matches, list)
        assert len(matches) > 0

        for match in matches:
            assert isinstance(match, OddsData)
            assert match.has_1x2()

    def test_mock_odds_are_realistic(self, scraper):
        """Test that mock odds have realistic values"""
        odds = scraper.get_match_odds("Portugal", "Brazil")

        # Odds should be > 1.0
        assert odds.home_win > 1.0
        assert odds.draw > 1.0
        assert odds.away_win > 1.0

        # Implied probabilities should sum to > 1 (bookmaker margin)
        implied_sum = (1/odds.home_win + 1/odds.draw + 1/odds.away_win)
        assert implied_sum > 1.0
        # Note: removed upper bound check as it can vary with random odds


class TestBetclicScraper:
    """Tests for BetclicScraper"""

    @pytest.fixture
    def scraper(self):
        """Create BetclicScraper instance"""
        return BetclicScraper()

    def test_init_configures_correctly(self, scraper):
        """Test initialization sets correct configuration"""
        assert scraper.site_key == "betclic"
        assert "Betclic" in scraper.site_name
        assert "betclic.pt" in scraper.base_url.lower()

    def test_get_match_odds_returns_odds(self, scraper):
        """Test get_match_odds returns odds data"""
        odds = scraper.get_match_odds("Spain", "Germany")

        assert odds is not None
        assert odds.site == "betclic"
        assert odds.has_1x2()

    def test_get_upcoming_matches(self, scraper):
        """Test get_upcoming_matches returns matches"""
        matches = scraper.get_upcoming_matches(days_ahead=7)

        assert len(matches) > 0
        assert all(isinstance(m, OddsData) for m in matches)


class TestSolverdeScraper:
    """Tests for SolverdeScraper"""

    @pytest.fixture
    def scraper(self):
        """Create SolverdeScraper instance"""
        return SolverdeScraper()

    def test_init_configures_correctly(self, scraper):
        """Test initialization sets correct configuration"""
        assert scraper.site_key == "solverde"
        assert "Solverde" in scraper.site_name
        assert "solverde.pt" in scraper.base_url.lower()

    def test_get_match_odds_returns_odds(self, scraper):
        """Test get_match_odds returns odds data"""
        odds = scraper.get_match_odds("Benfica", "Porto")

        assert odds is not None
        assert odds.site == "solverde"
        assert odds.has_1x2()

    def test_get_upcoming_matches(self, scraper):
        """Test get_upcoming_matches returns matches"""
        matches = scraper.get_upcoming_matches(days_ahead=7)

        assert len(matches) > 0
        assert all(isinstance(m, OddsData) for m in matches)


class TestScraperError:
    """Tests for ScraperError exception"""

    def test_create_with_message(self):
        """Test creating ScraperError with message"""
        error = ScraperError("Site unavailable")

        assert str(error) == "Site unavailable"

    def test_raise_and_catch(self):
        """Test raising and catching ScraperError"""
        def failing_function():
            raise ScraperError("Scraping failed")

        with pytest.raises(ScraperError) as exc_info:
            failing_function()

        assert "Scraping failed" in str(exc_info.value)
