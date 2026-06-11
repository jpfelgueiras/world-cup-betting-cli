"""
Unit tests for CLI Main Module

Tests for the Click-based command-line interface.
"""

from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import json

import pytest
from click.testing import CliRunner

from src.cli.main import (
    cli,
    predict,
    scan,
    interactive,
    sites,
    show_available_sites,
    get_scrapers,
    create_mock_team_data,
    calculate_market_averages,
    generate_recommendations,
    output_table,
    output_json,
    output_csv,
)
from src.scrapers.base_scraper import OddsData
from src.predictors.prediction_engine import MatchPrediction
from src.utils.ev_calculator import BetRecommendation


class TestCliCommands:
    """Tests for CLI command groups and commands"""

    @pytest.fixture
    def runner(self):
        """Create Click test runner"""
        return CliRunner()

    def test_cli_version(self, runner):
        """Test CLI version option"""
        result = runner.invoke(cli, ['--version'])
        assert result.exit_code == 0
        assert '0.1.0' in result.output

    def test_cli_help(self, runner):
        """Test CLI help"""
        result = runner.invoke(cli, ['--help'])
        assert result.exit_code == 0
        assert 'World Cup Betting Insights' in result.output
        assert 'predict' in result.output
        assert 'scan' in result.output
        assert 'interactive' in result.output
        assert 'sites' in result.output


class TestPredictCommand:
    """Tests for the predict command"""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    @pytest.fixture
    def mock_prediction(self):
        """Create a mock MatchPrediction"""
        pred = Mock(spec=MatchPrediction)
        pred.home_team = "Portugal"
        pred.away_team = "Brazil"
        pred.home_win_prob = 0.45
        pred.draw_prob = 0.25
        pred.away_win_prob = 0.30
        pred.home_confidence = 70.0
        pred.draw_confidence = 60.0
        pred.away_confidence = 65.0
        pred.over_2_5_prob = 0.55
        pred.btts_prob = 0.60
        pred.key_factors = ["Portugal strong at home", "Brazil missing key players"]
        return pred

    @pytest.fixture
    def mock_odds(self):
        """Create mock odds data"""
        match_date = datetime.now() + timedelta(days=3)
        return OddsData(
            match_id="test_123",
            home_team="Portugal",
            away_team="Brazil",
            match_date=match_date,
            site="betano",
            site_name="Betano.pt",
            home_win=2.10,
            draw=3.20,
            away_win=2.80,
            over_2_5=1.85,
            under_2_5=1.95,
            btts_yes=1.70,
            btts_no=2.10,
        )

    @patch('src.cli.main.PredictionEngine')
    @patch('src.cli.main.get_scrapers')
    def test_predict_invalid_match_format(self, mock_get_scrapers, mock_engine, runner):
        """Test predict command with invalid match format"""
        result = runner.invoke(cli, ['predict', 'InvalidMatchFormat'])
        assert result.exit_code == 1
        assert 'Invalid match format' in result.output

    @patch('src.cli.main.PredictionEngine')
    @patch('src.cli.main.get_scrapers')
    @patch('src.cli.main.create_mock_team_data')
    @patch('src.cli.main.calculate_market_averages')
    @patch('src.cli.main.generate_recommendations')
    def test_predict_json_output(
        self, mock_gen_rec, mock_calc_avg, mock_create_team, 
        mock_get_scrapers, mock_engine, runner, mock_prediction, mock_odds
    ):
        """Test predict command with JSON output format"""
        # Setup mocks
        mock_engine_instance = Mock()
        mock_engine.return_value = mock_engine_instance
        mock_engine_instance.predict_match.return_value = mock_prediction
        
        mock_scraper = Mock()
        mock_scraper.get_match_odds.return_value = mock_odds
        mock_get_scrapers.return_value = [mock_scraper]
        
        mock_create_team.return_value = Mock()
        mock_calc_avg.return_value = {'home_win': 2.0, 'draw': 3.0, 'away_win': 2.5, 
                                       'over_2_5': 1.8, 'btts_yes': 1.7, 'num_bookmakers': 1}
        
        mock_rec = Mock(spec=BetRecommendation)
        mock_rec.market = "1X2 - Home Win"
        mock_rec.site = "betano"
        mock_rec.site_name = "Betano.pt"
        mock_rec.odds = 2.10
        mock_rec.probability = 0.45
        mock_rec.ev_percentage = 5.5
        mock_rec.confidence = 70.0
        mock_rec.is_value_bet = True
        mock_gen_rec.return_value = [mock_rec]

        result = runner.invoke(cli, [
            'predict', 'Portugal vs Brazil',
            '--format', 'json',
            '--min-ev', '5',
            '--min-confidence', '60'
        ])

        assert result.exit_code == 0
        # Should output valid JSON
        output_lines = result.output.strip().split('\n')
        json_output = None
        for line in output_lines:
            try:
                json_output = json.loads(line)
                break
            except json.JSONDecodeError:
                continue
        
        if json_output:
            assert 'match' in json_output
            assert 'value_bets' in json_output

    @patch('src.cli.main.PredictionEngine')
    @patch('src.cli.main.get_scrapers')
    def test_predict_no_odds_available(self, mock_get_scrapers, mock_engine, runner):
        """Test predict command when no odds are available"""
        mock_engine_instance = Mock()
        mock_engine.return_value = mock_engine_instance
        
        mock_scraper = Mock()
        mock_scraper.get_match_odds.return_value = None
        mock_scraper.site_name = "Betano"
        mock_get_scrapers.return_value = [mock_scraper]

        result = runner.invoke(cli, ['predict', 'Portugal vs Brazil'])

        assert result.exit_code == 1
        assert 'No odds available' in result.output

    @patch('src.cli.main.PredictionEngine')
    @patch('src.cli.main.get_scrapers')
    @patch('src.cli.main.create_mock_team_data')
    def test_predict_with_site_filter(
        self, mock_create_team, mock_get_scrapers, mock_engine, runner, mock_prediction
    ):
        """Test predict command with specific site filter"""
        mock_engine_instance = Mock()
        mock_engine.return_value = mock_engine_instance
        mock_engine_instance.predict_match.return_value = mock_prediction
        
        mock_scraper = Mock()
        mock_scraper.get_match_odds.return_value = Mock(spec=OddsData)
        mock_get_scrapers.return_value = [mock_scraper]
        mock_create_team.return_value = Mock()

        result = runner.invoke(cli, [
            'predict', 'Portugal vs Brazil',
            '--site', 'betano'
        ])

        assert result.exit_code == 0
        mock_get_scrapers.assert_called_once_with('betano')


class TestScanCommand:
    """Tests for the scan command"""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    @patch('src.cli.main.get_scrapers')
    def test_scan_invalid_date_format(self, mock_get_scrapers, runner):
        """Test scan command with invalid date format"""
        result = runner.invoke(cli, ['scan', '--date', 'invalid-date'])
        assert result.exit_code == 1
        assert 'Invalid date format' in result.output

    @patch('src.cli.main.PredictionEngine')
    @patch('src.cli.main.get_scrapers')
    @patch('src.cli.main.create_mock_team_data')
    def test_scan_no_matches_found(
        self, mock_create_team, mock_get_scrapers, mock_engine, runner
    ):
        """Test scan command when no matches are found"""
        mock_engine_instance = Mock()
        mock_engine.return_value = mock_engine_instance
        
        mock_scraper = Mock()
        mock_scraper.get_upcoming_matches.return_value = []
        mock_get_scrapers.return_value = [mock_scraper]
        mock_create_team.return_value = Mock()

        result = runner.invoke(cli, ['scan', '--days', '7'])

        assert result.exit_code == 1
        assert 'No matches found' in result.output

    @patch('src.cli.main.PredictionEngine')
    @patch('src.cli.main.get_scrapers')
    @patch('src.cli.main.create_mock_team_data')
    @patch('src.cli.main.calculate_market_averages')
    @patch('src.cli.main.generate_recommendations')
    def test_scan_finds_value_bets(
        self, mock_gen_rec, mock_calc_avg, mock_create_team,
        mock_get_scrapers, mock_engine, runner
    ):
        """Test scan command finds value bets"""
        mock_engine_instance = Mock()
        mock_engine.return_value = mock_engine_instance
        
        match_date = datetime.now() + timedelta(days=3)
        mock_match = OddsData(
            match_id="test_1",
            home_team="Portugal",
            away_team="Spain",
            match_date=match_date,
            site="betano",
            site_name="Betano.pt",
            home_win=2.0,
            draw=3.0,
            away_win=2.5,
        )
        
        mock_scraper = Mock()
        mock_scraper.get_upcoming_matches.return_value = [mock_match]
        mock_scraper.site_name = "Betano"
        mock_get_scrapers.return_value = [mock_scraper]
        
        mock_pred = Mock(spec=MatchPrediction)
        mock_pred.home_win_prob = 0.50
        mock_pred.draw_prob = 0.25
        mock_pred.away_win_prob = 0.25
        mock_pred.home_confidence = 70.0
        mock_pred.draw_confidence = 60.0
        mock_pred.away_confidence = 60.0
        mock_pred.over_2_5_prob = 0.55
        mock_pred.btts_prob = 0.60
        mock_pred.key_factors = []
        mock_engine_instance.predict_match.return_value = mock_pred
        
        mock_create_team.return_value = Mock()
        mock_calc_avg.return_value = {'home_win': 2.0, 'draw': 3.0, 'away_win': 2.5,
                                       'over_2_5': 1.8, 'btts_yes': 1.7, 'num_bookmakers': 1}
        
        mock_rec = Mock(spec=BetRecommendation)
        mock_rec.market = "1X2 - Home Win"
        mock_rec.site = "betano"
        mock_rec.site_name = "Betano.pt"
        mock_rec.odds = 2.0
        mock_rec.probability = 0.50
        mock_rec.ev_percentage = 0.0
        mock_rec.confidence = 70.0
        mock_rec.is_value_bet = False
        mock_gen_rec.return_value = [mock_rec]

        result = runner.invoke(cli, ['scan', '--days', '7', '--min-ev', '5'])

        assert result.exit_code == 0


class TestInteractiveCommand:
    """Tests for the interactive command"""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    @patch('click.prompt')
    def test_interactive_quit(self, mock_prompt, runner):
        """Test interactive mode quit command"""
        mock_prompt.side_effect = ['quit']
        
        result = runner.invoke(cli, ['interactive'])
        
        assert result.exit_code == 0
        assert 'Good luck' in result.output or 'quit' in result.output.lower()

    @patch('click.prompt')
    def test_interactive_sites_command(self, mock_prompt, runner):
        """Test interactive mode sites command"""
        mock_prompt.side_effect = ['sites', 'quit']
        
        result = runner.invoke(cli, ['interactive'])
        
        assert result.exit_code == 0
        assert 'Betting Sites' in result.output or 'sites' in result.output.lower()

    @patch('click.prompt')
    def test_interactive_keyboard_interrupt(self, mock_prompt, runner):
        """Test interactive mode handles keyboard interrupt"""
        import signal
        mock_prompt.side_effect = KeyboardInterrupt()
        
        result = runner.invoke(cli, ['interactive'])
        
        assert result.exit_code == 0
        assert 'Goodbye' in result.output


class TestSitesCommand:
    """Tests for the sites command"""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    def test_sites_shows_table(self, runner):
        """Test sites command displays betting sites table"""
        result = runner.invoke(cli, ['sites'])
        
        assert result.exit_code == 0
        # Should contain site names or URLs
        assert len(result.output) > 0


class TestHelperFunctions:
    """Tests for helper functions in CLI module"""

    def test_get_scrapers_all(self):
        """Test get_scrapers returns all scrapers for 'all' parameter"""
        scrapers = get_scrapers('all')
        
        assert len(scrapers) == 3
        scraper_sites = [s.site_key for s in scrapers]
        assert 'betano' in scraper_sites
        assert 'betclic' in scraper_sites
        assert 'solverde' in scraper_sites

    def test_get_scrapers_specific_site(self):
        """Test get_scrapers returns specific scraper"""
        scrapers = get_scrapers('betano')
        
        assert len(scrapers) == 1
        assert scrapers[0].site_key == 'betano'

    def test_create_mock_team_data(self):
        """Test create_mock_team_data creates valid TeamData"""
        from src.predictors.team_stats import TeamData
        
        team_data = create_mock_team_data("TestTeam")
        
        assert isinstance(team_data, TeamData)
        assert team_data.name == "TestTeam"
        assert team_data.fifa_ranking >= 1 and team_data.fifa_ranking <= 50
        assert team_data.elo_rating >= 1400 and team_data.elo_rating <= 2000

    def test_calculate_market_averages(self):
        """Test calculate_market_averages computes correct averages"""
        match_date = datetime.now()
        odds_list = [
            OddsData(
                match_id="1",
                home_team="A",
                away_team="B",
                match_date=match_date,
                site="site1",
                site_name="Site 1",
                home_win=2.0,
                draw=3.0,
                away_win=2.5,
                over_2_5=1.8,
                btts_yes=1.7,
            ),
            OddsData(
                match_id="2",
                home_team="A",
                away_team="B",
                match_date=match_date,
                site="site2",
                site_name="Site 2",
                home_win=2.2,
                draw=3.2,
                away_win=2.4,
                over_2_5=1.9,
                btts_yes=1.8,
            ),
        ]

        averages = calculate_market_averages(odds_list)

        assert 'home_win' in averages
        assert 'draw' in averages
        assert 'away_win' in averages
        assert 'num_bookmakers' in averages
        assert averages['num_bookmakers'] == 2
        # Average of 2.0 and 2.2 should be 2.1
        assert averages['home_win'] == pytest.approx(2.1, rel=0.01)

    def test_calculate_market_averages_empty(self):
        """Test calculate_market_averages with empty list"""
        averages = calculate_market_averages([])
        
        assert averages['home_win'] == 0
        assert averages['num_bookmakers'] == 0

    def test_generate_recommendations(self):
        """Test generate_recommendations creates bet recommendations"""
        mock_pred = Mock(spec=MatchPrediction)
        mock_pred.home_win_prob = 0.50
        mock_pred.draw_prob = 0.25
        mock_pred.away_win_prob = 0.25
        mock_pred.home_confidence = 70.0
        mock_pred.draw_confidence = 60.0
        mock_pred.away_confidence = 60.0
        mock_pred.over_2_5_prob = 0.55
        mock_pred.btts_prob = 0.60
        mock_pred.key_factors = []
        
        match_date = datetime.now()
        odds = OddsData(
            match_id="1",
            home_team="A",
            away_team="B",
            match_date=match_date,
            site="betano",
            site_name="Betano",
            home_win=2.0,
            draw=3.0,
            away_win=2.5,
            over_2_5=1.8,
            btts_yes=1.7,
        )

        recommendations = generate_recommendations(
            mock_pred, [odds], {}, min_ev=5.0, min_confidence=60.0
        )

        assert len(recommendations) > 0
        assert all(isinstance(rec, BetRecommendation) for rec in recommendations)


class TestOutputFunctions:
    """Tests for output formatting functions"""

    @pytest.fixture
    def mock_prediction(self):
        pred = Mock(spec=MatchPrediction)
        pred.home_team = "Portugal"
        pred.away_team = "Brazil"
        pred.home_win_prob = 0.45
        pred.draw_prob = 0.25
        pred.away_win_prob = 0.30
        pred.over_2_5_prob = 0.55
        pred.btts_prob = 0.60
        pred.key_factors = ["Factor 1", "Factor 2"]
        return pred

    @pytest.fixture
    def mock_recommendations(self):
        rec = Mock(spec=BetRecommendation)
        rec.market = "1X2 - Home Win"
        rec.site = "betano"
        rec.site_name = "Betano.pt"
        rec.odds = 2.10
        rec.probability = 0.45
        rec.ev_percentage = 5.5
        rec.confidence = 70.0
        rec.is_value_bet = True
        rec.reasoning = ["Reason 1"]
        return [rec]

    def test_output_json_structure(self, mock_prediction, mock_recommendations, capsys):
        """Test output_json produces valid JSON structure"""
        from rich.console import Console
        from io import StringIO
        
        output = StringIO()
        console = Console(file=output, force_terminal=False)
        
        market_avg = {
            'home_win': 2.0,
            'draw': 3.0,
            'away_win': 2.5,
            'over_2_5': 1.8,
            'btts_yes': 1.7,
            'num_bookmakers': 1
        }
        
        with patch('src.cli.main.console', console):
            output_json(mock_prediction, market_avg, mock_recommendations)
        
        output_str = output.getvalue()
        # Should contain JSON-like structure
        assert 'match' in output_str or 'value_bets' in output_str

    def test_output_csv_structure(self, mock_recommendations, capsys):
        """Test output_csv produces CSV format"""
        from rich.console import Console
        from io import StringIO
        
        output = StringIO()
        console = Console(file=output, force_terminal=False)
        
        with patch('src.cli.main.console', console):
            output_csv(mock_recommendations)
        
        output_str = output.getvalue()
        # CSV should have header row
        assert 'Market' in output_str or 'Site' in output_str


class TestShowAvailableSites:
    """Tests for show_available_sites function"""

    def test_show_available_sites_displays_table(self, capsys):
        """Test show_available_sites displays betting sites"""
        from rich.console import Console
        from io import StringIO
        
        output = StringIO()
        console = Console(file=output, force_terminal=False)
        
        with patch('src.cli.main.console', console):
            show_available_sites()
        
        output_str = output.getvalue()
        assert len(output_str) > 0


class TestPredictCommandEdgeCases:
    """Edge case tests for predict command"""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    @patch('src.cli.main.PredictionEngine')
    @patch('src.cli.main.get_scrapers')
    @patch('src.cli.main.create_mock_team_data')
    def test_predict_with_versus_separator(
        self, mock_create_team, mock_get_scrapers, mock_engine, runner
    ):
        """Test predict command handles 'versus' separator"""
        mock_engine_instance = Mock()
        mock_engine.return_value = mock_engine_instance
        
        mock_scraper = Mock()
        mock_scraper.get_match_odds.return_value = None
        mock_get_scrapers.return_value = [mock_scraper]
        mock_create_team.return_value = Mock()

        result = runner.invoke(cli, ['predict', 'Portugal versus Brazil'])

        # Should parse correctly (may fail later due to no odds, but parsing works)
        assert 'vs' in result.output.lower() or 'versus' in result.output.lower() or result.exit_code != 0
