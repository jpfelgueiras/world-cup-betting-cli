"""Integration-style tests covering CLI, library, and API flows end to end."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List

from click.testing import CliRunner
from fastapi.testclient import TestClient

from src.api.app import create_app
from src.cli.main import cli
from src.library import BettingInsights
from src.scrapers.base_scraper import OddsData
from src.utils.ev_calculator import BetRecommendation


@dataclass
class DummyPrediction:
    home_team: str = "Portugal"
    away_team: str = "Brazil"
    home_win_prob: float = 0.4
    draw_prob: float = 0.25
    away_win_prob: float = 0.35
    home_confidence: float = 71.0
    draw_confidence: float = 63.0
    away_confidence: float = 68.0
    over_2_5_prob: float = 0.61
    btts_prob: float = 0.57
    key_factors: List[str] = None

    def __post_init__(self):
        if self.key_factors is None:
            self.key_factors = [
                "Portugal creating high-quality chances",
                "Brazil strong in transition",
            ]


class StubScraper:
    def __init__(self, site_key: str, site_name: str, match_date: datetime):
        self.site_key = site_key
        self.site_name = site_name
        self.match_date = match_date

    def get_match_odds(self, home_team: str, away_team: str, match_date=None):
        return OddsData(
            match_id=f"{home_team}_{away_team}_{self.site_key}",
            home_team=home_team,
            away_team=away_team,
            match_date=match_date or self.match_date,
            site=self.site_key,
            site_name=self.site_name,
            home_win=2.4,
            draw=3.3,
            away_win=2.9,
            over_2_5=1.95,
            under_2_5=1.85,
            btts_yes=1.8,
            btts_no=2.0,
        )

    def get_upcoming_matches(self, days_ahead: int = 7):
        return [
            self.get_match_odds("Portugal", "Brazil", self.match_date),
            self.get_match_odds("Spain", "Germany", self.match_date),
        ]


def test_library_analyze_match_integration(monkeypatch):
    insights = BettingInsights(cache_enabled=False, enabled_sites=[])
    insights.engine.predict_match = lambda *_args, **_kwargs: DummyPrediction()
    insights.scrapers = [
        StubScraper("betano", "Betano.pt", datetime(2026, 6, 15, 20, 0)),
        StubScraper("betclic", "Betclic.pt", datetime(2026, 6, 15, 20, 0)),
    ]

    result = insights.analyze_match("Portugal", "Brazil")

    assert result.home_team == "Portugal"
    assert result.away_team == "Brazil"
    assert result.num_bookmakers == 2
    assert result.market_avg_home == 2.4
    assert result.market_avg_draw == 3.3
    assert result.market_avg_away == 2.9
    assert result.key_factors == [
        "Portugal creating high-quality chances",
        "Brazil strong in transition",
    ]
    assert result.home_win_prob == 0.4
    assert result.has_value_bets is True
    assert all(bet.site in {"betano", "betclic"} for bet in result.value_bets)


def test_library_scan_upcoming_matches_aggregates_integration(monkeypatch):
    insights = BettingInsights(cache_enabled=False, enabled_sites=[])
    insights.scrapers = [
        StubScraper("betano", "Betano.pt", datetime(2026, 6, 15, 20, 0))
    ]

    def fake_analyze_match(
        home_team,
        away_team,
        match_date=None,
        min_ev=None,
        min_confidence=None,
    ):
        return type(
            "ScanMatch",
            (),
            {
                "home_team": home_team,
                "away_team": away_team,
                "match_date": match_date,
                "value_bets": [
                    BetRecommendation(
                        market="1X2 - Home Win",
                        site="betano",
                        site_name="Betano.pt",
                        odds=2.4,
                        probability=0.4,
                        ev_percentage=6.0,
                        confidence=71.0,
                        reasoning=["edge"],
                        is_value_bet=True,
                    )
                ],
                "has_value_bets": True,
            },
        )()

    monkeypatch.setattr(insights, "analyze_match", fake_analyze_match)

    result = insights.scan_upcoming_matches(days_ahead=5)

    assert result.total_matches == 2
    assert result.matches_with_value_bets == 2
    assert result.total_value_bets == 2
    assert len(result.matches) == 2


def test_api_predict_and_scan_endpoints_integration(monkeypatch):
    monkeypatch.setenv("DEV_MODE", "true")
    client = TestClient(create_app())

    prediction = DummyPrediction()

    class StubEngine:
        def predict_match(self, *_args, **_kwargs):
            return prediction

    monkeypatch.setattr("src.api.routes.get_prediction_engine", lambda: StubEngine())
    monkeypatch.setattr(
        "src.api.routes.get_scrapers",
        lambda site="all": [
            StubScraper("betano", "Betano.pt", datetime(2026, 6, 15, 20, 0))
        ],
    )

    predict_response = client.post(
        "/api/v1/predict",
        json={"home_team": "Portugal", "away_team": "Brazil", "site": "betano"},
    )
    assert predict_response.status_code == 200
    predict_data = predict_response.json()
    assert predict_data["home_team"] == "Portugal"
    assert predict_data["market_averages"]["num_bookmakers"] == 1
    assert predict_data["metadata"]["model_version"] == "1.0.0"
    assert isinstance(predict_data["value_bets"], list)

    scan_response = client.post(
        "/api/v1/scan",
        json={"days_ahead": 3, "site": "betano"},
    )
    assert scan_response.status_code == 200
    scan_data = scan_response.json()
    assert scan_data["total_matches"] == 2
    assert scan_data["matches_with_value_bets"] >= 1
    assert scan_data["filters_applied"]["risk_tolerance"] == "moderate"


def test_cli_predict_json_flow_integration(monkeypatch):
    runner = CliRunner()

    monkeypatch.setattr(
        "src.cli.main.create_mock_team_data", lambda team: {"name": team}
    )
    monkeypatch.setattr(
        "src.cli.main.PredictionEngine",
        lambda: type(
            "Engine",
            (),
            {"predict_match": lambda *_a, **_k: DummyPrediction()},
        )(),
    )
    monkeypatch.setattr(
        "src.cli.main.get_scrapers",
        lambda _site: [
            StubScraper("betano", "Betano.pt", datetime(2026, 6, 15, 20, 0))
        ],
    )

    result = runner.invoke(
        cli,
        ["predict", "Portugal vs Brazil", "--site", "betano", "--format", "json"],
    )

    assert result.exit_code == 0
    assert '"probabilities"' in result.output
    assert '"market_averages"' in result.output
    assert '"value_bets"' in result.output
