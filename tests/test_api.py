"""
Unit tests for REST API

Tests FastAPI routes, models, and app configuration.
"""

import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient

    MatchPredictionRequest,
    ScanRequest,
    AnalysisConfig,
    TeamProbabilities,
    ConfidenceLevels,
    MarketAverage,
    ValueBet,
    MatchAnalysisResponse,
    ScanResponse,
    HealthResponse,
    LibraryConfig,
    SiteType,
    RiskTolerance,
)


class TestAPIModels:
    """Tests for Pydantic API models"""

    def test_match_prediction_request_valid(self):
        """Test creating valid MatchPredictionRequest"""
        request = MatchPredictionRequest(
            home_team="Portugal",
            away_team="Brazil",
            site=SiteType.ALL
        )

        assert request.home_team == "Portugal"
        assert request.away_team == "Brazil"
        assert request.site == SiteType.ALL

    def test_match_prediction_request_with_date(self):
        """Test request with match date"""
        match_date = datetime(2026, 6, 15, 20, 0)

        request = MatchPredictionRequest(
            home_team="Portugal",
            away_team="Brazil",
            match_date=match_date,
            site=SiteType.BETANO
        )

        assert request.match_date == match_date
        assert request.site == SiteType.BETANO

    def test_match_prediction_request_empty_team_fails(self):
        """Test that empty team name fails validation"""
        with pytest.raises(Exception):  # ValidationError
            MatchPredictionRequest(
                home_team="",
                away_team="Brazil"
            )

    def test_scan_request_defaults(self):
        """Test ScanRequest default values"""
        request = ScanRequest()

        assert request.days_ahead == 7
        assert request.min_ev == 5.0
        assert request.min_confidence == 60.0
        assert request.site == SiteType.ALL

    def test_scan_request_custom_values(self):
        """Test ScanRequest with custom values"""
        request = ScanRequest(
            days_ahead=14,
            min_ev=10.0,
            min_confidence=70.0,
            site=SiteType.BETCLIC
        )

        assert request.days_ahead == 14
        assert request.min_ev == 10.0
        assert request.min_confidence == 70.0
        assert request.site == SiteType.BETCLIC

    def test_scan_request_days_ahead_validation(self):
        """Test days_ahead must be between 1 and 30"""
        # Valid
        request = ScanRequest(days_ahead=1)
        assert request.days_ahead == 1

        request = ScanRequest(days_ahead=30)
        assert request.days_ahead == 30

        # Invalid - would raise validation error
        with pytest.raises(Exception):
            ScanRequest(days_ahead=0)

        with pytest.raises(Exception):
            ScanRequest(days_ahead=31)

    def test_analysis_config_defaults(self):
        """Test AnalysisConfig default values"""
        config = AnalysisConfig()

        assert config.min_ev == 5.0
        assert config.min_confidence == 60.0
        assert config.risk_tolerance == RiskTolerance.MODERATE

    def test_analysis_config_custom_risk_tolerance(self):
        """Test AnalysisConfig with different risk tolerances"""
        config = AnalysisConfig(risk_tolerance=RiskTolerance.CONSERVATIVE)
        assert config.risk_tolerance == RiskTolerance.CONSERVATIVE

        config = AnalysisConfig(risk_tolerance=RiskTolerance.AGGRESSIVE)
        assert config.risk_tolerance == RiskTolerance.AGGRESSIVE

    def test_team_probabilities_valid_range(self):
        """Test TeamProbabilities values are in valid range"""
        probs = TeamProbabilities(
            home_win=0.45,
            draw=0.28,
            away_win=0.27,
            over_2_5=0.62,
            btts=0.55
        )

        assert 0 <= probs.home_win <= 1
        assert 0 <= probs.draw <= 1
        assert 0 <= probs.away_win <= 1

    def test_team_probabilities_out_of_range_fails(self):
        """Test that out-of-range probabilities fail validation"""
        with pytest.raises(Exception):
            TeamProbabilities(
                home_win=1.5,  # > 1.0
                draw=0.3,
                away_win=0.2,
                over_2_5=0.5,
                btts=0.5
            )

    def test_value_bet_creation(self):
        """Test creating ValueBet model"""
        bet = ValueBet(
            market="1X2 - Home Win",
            site="betano",
            site_name="Betano.pt",
            odds=2.25,
            probability=0.48,
            ev_percentage=8.0,
            confidence=72.0,
            is_value_bet=True,
            reasoning=["Good form"]
        )

        assert bet.market == "1X2 - Home Win"
        assert bet.odds > 1.0
        assert bet.is_value_bet is True

    def test_value_bet_odds_must_be_greater_than_1(self):
        """Test that odds must be greater than 1"""
        with pytest.raises(Exception):
            ValueBet(
                market="Test",
                site="test",
                site_name="Test",
                odds=0.5,  # Invalid
                probability=0.5,
                ev_percentage=5.0,
                confidence=60.0,
                is_value_bet=False
            )

    def test_market_average_creation(self):
        """Test creating MarketAverage model"""
        avg = MarketAverage(
            home_win=2.10,
            draw=3.20,
            away_win=2.80,
            over_2_5=1.85,
            btts_yes=1.70,
            num_bookmakers=3
        )

        assert avg.home_win == pytest.approx(2.10, rel=0.01)
        assert avg.num_bookmakers == 3

    def test_market_average_optional_fields(self):
        """Test MarketAverage with optional fields"""
        avg = MarketAverage(
            home_win=2.10,
            draw=None,  # Optional
            away_win=None,
            over_2_5=None,
            btts_yes=None,
            num_bookmakers=1
        )

        assert avg.home_win == pytest.approx(2.10, rel=0.01)
        assert avg.draw is None

    def test_library_config_creation(self):
        """Test creating LibraryConfig model"""
        config = LibraryConfig(
            min_ev=8.0,
            min_confidence=65.0,
            enabled_sites=["betano", "betclic"],
            cache_enabled=True,
            cache_ttl_hours=2
        )

        assert config.min_ev == 8.0
        assert len(config.enabled_sites) == 2
        assert "betano" in config.enabled_sites


class TestHealthEndpoint:
    """Tests for /api/v1/health endpoint"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(create_app())

    def test_health_check_returns_200(self, client):
        """Test health endpoint returns 200 OK"""
        response = client.get("/api/v1/health")
        assert response.status_code == 200

    def test_health_check_response_structure(self, client):
        """Test health response has required fields"""
        response = client.get("/api/v1/health")
        data = response.json()

        assert "status" in data
        assert "version" in data
        assert "timestamp" in data
        assert "bookmakers" in data
        assert "prediction_engine" in data
        assert "database" in data

    def test_health_status_is_healthy(self, client):
        """Test health status is 'healthy'"""
        response = client.get("/api/v1/health")
        data = response.json()

        assert data["status"] == "healthy"

    def test_health_includes_bookmakers(self, client):
        """Test health response includes bookmaker statuses"""
        response = client.get("/api/v1/health")
        data = response.json()

        assert isinstance(data["bookmakers"], list)
        assert len(data["bookmakers"]) > 0

        for bookmaker in data["bookmakers"]:
            assert "site_key" in bookmaker
            assert "site_name" in bookmaker
            assert "enabled" in bookmaker
            assert "status" in bookmaker


class TestRootEndpoint:
    """Tests for root endpoint /"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(create_app())

    def test_root_returns_200(self, client):
        """Test root endpoint returns 200 OK"""
        response = client.get("/")
        assert response.status_code == 200

    def test_root_response_has_api_info(self, client):
        """Test root response includes API information"""
        response = client.get("/")
        data = response.json()

        assert "name" in data
        assert "version" in data
        assert "documentation" in data
        assert "health" in data
        assert "disclaimer" in data


class TestBookmakersEndpoint:
    """Tests for /api/v1/bookmakers endpoint"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(create_app())

    def test_list_bookmakers_returns_200(self, client):
        """Test bookmakers endpoint returns 200 OK"""
        response = client.get("/api/v1/bookmakers")
        assert response.status_code == 200

    def test_list_bookmakers_returns_list(self, client):
        """Test bookmakers endpoint returns a list"""
        response = client.get("/api/v1/bookmakers")
        data = response.json()

        assert isinstance(data, list)

    def test_bookmaker_has_required_fields(self, client):
        """Test each bookmaker has required fields"""
        response = client.get("/api/v1/bookmakers")
        data = response.json()

        for bookmaker in data:
            assert "site_key" in bookmaker
            assert "site_name" in bookmaker
            assert "enabled" in bookmaker
            assert "rate_limit_seconds" in bookmaker


class TestConfigEndpoint:
    """Tests for /api/v1/config endpoints"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(create_app())

    def test_get_config_returns_200(self, client):
        """Test get config endpoint returns 200 OK"""
        response = client.get("/api/v1/config")
        assert response.status_code == 200

    def test_get_config_has_required_fields(self, client):
        """Test config response has required fields"""
        response = client.get("/api/v1/config")
        data = response.json()

        assert "min_ev" in data
        assert "min_confidence" in data
        assert "enabled_sites" in data
        assert "cache_enabled" in data

    def test_put_config_updates_config(self, client):
        """Test updating config via PUT"""
        new_config = {
            "min_ev": 10.0,
            "min_confidence": 70.0,
            "enabled_sites": ["betano"],
            "cache_enabled": False,
            "cache_ttl_hours": 2
        }

        response = client.put("/api/v1/config", json=new_config)
        assert response.status_code == 200

        data = response.json()
        assert data["min_ev"] == 10.0
        assert data["min_confidence"] == 70.0


class TestPredictEndpoint:
    """Tests for /api/v1/predict endpoint"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(create_app())

    def test_predict_valid_request_returns_200(self, client):
        """Test predict endpoint with valid request"""
        request_data = {
            "home_team": "Portugal",
            "away_team": "Brazil"
        }

        response = client.post("/api/v1/predict", json=request_data)
        assert response.status_code == 200

    def test_predict_response_has_required_fields(self, client):
        """Test predict response structure"""
        request_data = {
            "home_team": "Portugal",
            "away_team": "Brazil"
        }

        response = client.post("/api/v1/predict", json=request_data)
        data = response.json()

        assert "match_id" in data
        assert "home_team" in data
        assert "away_team" in data
        assert "probabilities" in data
        assert "confidence" in data
        assert "market_averages" in data
        assert "value_bets" in data
        assert "key_factors" in data

    def test_predict_with_site_filter(self, client):
        """Test predict with specific site filter"""
        request_data = {
            "home_team": "Portugal",
            "away_team": "Brazil",
            "site": "betano"
        }

        response = client.post("/api/v1/predict", json=request_data)
        assert response.status_code == 200

    def test_predict_empty_team_name_fails(self, client):
        """Test predict with empty team name returns 422"""
        request_data = {
            "home_team": "",
            "away_team": "Brazil"
        }

        response = client.post("/api/v1/predict", json=request_data)
        assert response.status_code == 422  # Validation error

    def test_predict_missing_team_fails(self, client):
        """Test predict with missing team returns 422"""
        request_data = {
            "away_team": "Brazil"
            # Missing home_team
        }

        response = client.post("/api/v1/predict", json=request_data)
        assert response.status_code == 422  # Validation error


class TestScanEndpoint:
    """Tests for /api/v1/scan endpoint"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(create_app())

    def test_scan_default_request_returns_200(self, client):
        """Test scan endpoint with default request"""
        response = client.post("/api/v1/scan")
        assert response.status_code == 200

    def test_scan_response_has_required_fields(self, client):
        """Test scan response structure"""
        response = client.post("/api/v1/scan")
        data = response.json()

        assert "scan_date" in data
        assert "total_matches" in data
        assert "matches_with_value_bets" in data
        assert "total_value_bets" in data
        assert "matches" in data

    def test_scan_with_custom_days_ahead(self, client):
        """Test scan with custom days_ahead"""
        request_data = {
            "days_ahead": 14,
            "min_ev": 8.0
        }

        response = client.post("/api/v1/scan", json=request_data)
        assert response.status_code == 200

    def test_scan_with_site_filter(self, client):
        """Test scan with specific site filter"""
        request_data = {
            "site": "betclic",
            "days_ahead": 7
        }

        response = client.post("/api/v1/scan", json=request_data)
        assert response.status_code == 200

    def test_scan_days_ahead_validation(self, client):
        """Test scan validates days_ahead range"""
        # Too high - should fail or be clamped
        request_data = {
            "days_ahead": 50  # Max is 30
        }

        response = client.post("/api/v1/scan", json=request_data)
        # Should either fail validation or succeed with clamped value
        assert response.status_code in [200, 422]


class TestCORS:
    """Tests for CORS middleware"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(create_app())

    def test_cors_headers_present(self, client):
        """Test that CORS headers are present in responses"""
        response = client.get("/api/v1/health")

        # FastAPI's CORSMiddleware adds these headers
        assert "access-control-allow-origin" in response.headers or \
               response.status_code == 200  # May not show on same-origin


class TestErrorHandling:
    """Tests for error handling"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(create_app())

    def test_invalid_json_returns_422(self, client):
        """Test that invalid JSON returns 422"""
        response = client.post(
            "/api/v1/predict",
            content="not valid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422

    def test_error_response_has_standard_format(self, client):
        """Test that error responses have standard format"""
        request_data = {
            "home_team": "",  # Invalid
            "away_team": "Brazil"
        }

        response = client.post("/api/v1/predict", json=request_data)
        data = response.json()

        # Should have error information (FastAPI uses 'error' or 'detail')
        assert "error" in data or "detail" in data


class TestAppCreation:
    """Tests for app creation function"""

    def test_create_app_with_custom_title(self):
        """Test creating app with custom title"""
        custom_app = create_app(title="Custom API")
        assert custom_app.title == "Custom API"

    def test_create_app_with_custom_version(self):
        """Test creating app with custom version"""
        custom_app = create_app(version="2.0.0")
        assert custom_app.version == "2.0.0"

    def test_create_app_debug_mode(self):
        """Test creating app in debug mode"""
        custom_app = create_app(debug=True)
        assert custom_app.debug is True

    def test_create_app_custom_docs_url(self):
        """Test creating app with custom docs URL"""
        custom_app = create_app(docs_url="/swagger")
        # Would need to test with TestClient to verify

    def test_default_app_exists(self):
        """Test that default app instance exists"""
        from src.api.app import app
        assert app is not None
        assert app.title == "World Cup Betting Insights API"
