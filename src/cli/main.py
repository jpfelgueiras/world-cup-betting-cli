"""
World Cup Betting Insights CLI

Main command-line interface using Click framework.
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import click
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import DEFAULT_MIN_CONFIDENCE  # noqa: E402
from config import BETTING_SITES, DEFAULT_MIN_EV, DISCLAIMER
from predictors.prediction_engine import MatchPrediction  # noqa: E402
from predictors.prediction_engine import PredictionEngine
from predictors.team_stats import TeamData  # noqa: E402
from scrapers.betano_scraper import BetanoScraper  # noqa: E402
from scrapers.betclic_scraper import BetclicScraper  # noqa: E402
from scrapers.solverde_scraper import SolverdeScraper  # noqa: E402
from utils.ev_calculator import BetRecommendation  # noqa: E402
from utils.ev_calculator import find_best_value_bets, format_ev_display

console = Console()


@click.group()
@click.version_option(version="0.1.0", prog_name="worldcup")
def cli():
    """
    🏆 World Cup Betting Insights CLI

    Find value bets for World Cup matches by comparing AI predictions
    against odds from Portuguese licensed betting sites.

    ⚠️  RESPONSIBLE GAMBLING: This tool provides insights only.
    No guaranteed wins. You must be 18+ to gamble in Portugal.
    """
    pass


@cli.command()
@click.argument("match")
@click.option(
    "--site",
    "-s",
    type=click.Choice(["betano", "betclic", "solverde", "all"]),
    default="all",
    help="Specific betting site to analyze",
)
@click.option(
    "--min-ev",
    type=float,
    default=DEFAULT_MIN_EV,
    help=f"Minimum EV threshold (default: {DEFAULT_MIN_EV}%)",
)
@click.option(
    "--min-confidence",
    type=float,
    default=DEFAULT_MIN_CONFIDENCE,
    help=f"Minimum confidence threshold (default: {DEFAULT_MIN_CONFIDENCE}%)",
)
@click.option(
    "--format",
    "-f",
    "output_format",
    type=click.Choice(["table", "json", "csv"]),
    default="table",
    help="Output format",
)
def predict(
    match: str, site: str, min_ev: float, min_confidence: float, output_format: str
):
    """
    Analyze a specific match.

    MATCH format: "Team A vs Team B"

    Example: worldcup predict "Portugal vs Brazil"
    """
    # Parse match string
    if "vs" not in match and "versus" not in match:
        console.print('[red]❌ Invalid match format. Use: "Team A vs Team B"[/red]')
        sys.exit(1)

    # Split team names
    separator = "vs" if "vs" in match else "versus"
    parts = match.split(separator)
    home_team = parts[0].strip()
    away_team = parts[1].strip()

    console.print(
        f"\n[bold blue]🔍 Analyzing: {home_team} vs {away_team}[/bold blue]\n"
    )

    # Create prediction engine
    engine = PredictionEngine()

    # Generate mock team data (in real version, would fetch from APIs)
    home_data = create_mock_team_data(home_team)
    away_data = create_mock_team_data(away_team)

    # Generate prediction
    prediction = engine.predict_match(home_data, away_data)

    # Get odds from scrapers
    scrapers = get_scrapers(site)
    all_odds = []

    for scraper in scrapers:
        try:
            odds = scraper.get_match_odds(home_team, away_team)
            if odds:
                all_odds.append(odds)
        except Exception as e:
            console.print(
                f"[yellow]⚠️  {scraper.site_name} unavailable: {str(e)[:50]}[/yellow]"
            )

    if not all_odds:
        console.print("[red]❌ No odds available from any betting site[/red]")
        sys.exit(1)

    # Calculate market averages
    market_avg = calculate_market_averages(all_odds)

    # Generate bet recommendations
    recommendations = generate_recommendations(
        prediction, all_odds, market_avg, min_ev, min_confidence
    )

    # Output results
    if output_format == "json":
        output_json(prediction, market_avg, recommendations)
    elif output_format == "csv":
        output_csv(recommendations)
    else:
        output_table(prediction, market_avg, recommendations)

    # Show disclaimer
    console.print(Panel(DISCLAIMER, style="yellow", box=box.ROUNDED))


@cli.command()
@click.option(
    "--date",
    "-d",
    type=str,
    default=None,
    help="Specific date (YYYY-MM-DD), defaults to next 7 days",
)
@click.option("--days", type=int, default=7, help="Number of days to scan ahead")
@click.option(
    "--min-ev",
    type=float,
    default=DEFAULT_MIN_EV,
    help=f"Minimum EV threshold (default: {DEFAULT_MIN_EV}%)",
)
@click.option(
    "--site",
    "-s",
    type=click.Choice(["betano", "betclic", "solverde", "all"]),
    default="all",
    help="Specific betting site",
)
def scan(date: Optional[str], days: int, min_ev: float, site: str):
    """
    Scan upcoming matches for value bets.

    Example: worldcup scan --date 2026-06-15 --min-ev 10
    """
    console.print("\n[bold blue]📅 Scanning upcoming matches...[/bold blue]\n")

    # Determine date range
    if date:
        try:
            datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            console.print("[red]❌ Invalid date format. Use YYYY-MM-DD[/red]")
            sys.exit(1)

    # Get scrapers
    scrapers = get_scrapers(site)

    # Collect all upcoming matches
    all_matches = {}

    for scraper in scrapers:
        try:
            matches = scraper.get_upcoming_matches(days_ahead=days)
            for match in matches:
                key = f"{match.home_team}_{match.away_team}"
                if key not in all_matches:
                    all_matches[key] = {"match": match, "odds": []}
                all_matches[key]["odds"].append(match)
        except Exception as e:
            console.print(
                f"[yellow]⚠️  {scraper.site_name} scan failed: {str(e)[:50]}[/yellow]"
            )

    if not all_matches:
        console.print("[red]❌ No matches found[/red]")
        sys.exit(1)

    console.print(f"Found [bold]{len(all_matches)}[/bold] upcoming matches\n")

    # Analyze each match for value bets
    value_bet_count = 0
    engine = PredictionEngine()

    for match_key, data in all_matches.items():
        match = data["match"]
        odds_list = data["odds"]

        # Create mock team data
        home_data = create_mock_team_data(match.home_team)
        away_data = create_mock_team_data(match.away_team)

        # Generate prediction
        prediction = engine.predict_match(home_data, away_data)

        # Calculate market averages
        market_avg = calculate_market_averages(odds_list)

        # Generate recommendations
        recommendations = generate_recommendations(
            prediction, odds_list, market_avg, min_ev, DEFAULT_MIN_CONFIDENCE
        )

        # Show if there are value bets
        value_bets = [r for r in recommendations if r.is_value_bet]
        if value_bets:
            value_bet_count += len(value_bets)
            console.print(
                f"[bold green]✅ {match.home_team} vs {match.away_team}[/bold green] - {len(value_bets)} value bets found"
            )

            # Show top value bet
            best = max(value_bets, key=lambda x: x.ev_percentage)
            console.print(
                f"   Best: {best.market} @ {best.site_name} ({best.odds}) → EV {format_ev_display(best.ev_percentage)}"
            )
            console.print()

    if value_bet_count == 0:
        console.print("[yellow]⚠️  No value bets found matching your criteria[/yellow]")
    else:
        console.print(
            f"\n[bold green]🎯 Total value bets found: {value_bet_count}[/bold green]"
        )

    console.print(Panel(DISCLAIMER, style="yellow", box=box.ROUNDED))


@cli.command()
def interactive():
    """
    Interactive mode for browsing matches and filtering bets.
    """
    console.print("\n[bold blue]🎮 Interactive Mode[/bold blue]\n")
    console.print("Welcome to World Cup Betting Insights Interactive Mode!")
    console.print("Type 'help' for commands, 'quit' to exit.\n")

    while True:
        try:
            cmd = click.prompt(
                "Command",
                type=click.Choice(
                    ["scan", "predict", "sites", "quit"], case_sensitive=False
                ),
                default="scan",
                show_choices=True,
            )

            if cmd == "quit":
                console.print("\n👋 Good luck and bet responsibly!")
                break
            elif cmd == "sites":
                show_available_sites()
            elif cmd == "scan":
                min_ev = click.prompt("Minimum EV %", type=float, default=5.0)
                # Would trigger scan here
                console.print(
                    f"[yellow]Scan with {min_ev}% EV threshold (not implemented in demo)[/yellow]"
                )
            elif cmd == "predict":
                match = click.prompt("Match (Team A vs Team B)")
                # Would trigger predict here
                console.print(
                    f"[yellow]Predict {match} (not implemented in demo)[/yellow]"
                )

        except KeyboardInterrupt:
            console.print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            console.print(f"[red]Error: {str(e)}[/red]")


@cli.command()
def sites():
    """Show available betting sites and their status"""
    show_available_sites()


def show_available_sites():
    """Display available betting sites"""
    table = Table(title="🇵🇹 Portuguese Licensed Betting Sites", box=box.ROUNDED)
    table.add_column("Site", style="cyan")
    table.add_column("URL", style="blue")
    table.add_column("Status", justify="center")
    table.add_column("Rate Limit", justify="center")

    for site_key, config in BETTING_SITES.items():
        status = "✅ Enabled" if config.get("enabled", False) else "⏸️ Disabled"
        table.add_row(
            config.get("name", site_key),
            config.get("url", "N/A"),
            status,
            f"{config.get('rate_limit_seconds', 5)}s",
        )

    console.print(table)
    console.print(
        "\nℹ️  All sites are regulated by SRIJ (Portuguese Gambling Authority)"
    )


# Helper functions


def get_scrapers(site: str) -> List:
    """Get list of scrapers based on site parameter"""
    scrapers = []

    if site == "all" or site == "betano":
        scrapers.append(BetanoScraper())
    if site == "all" or site == "betclic":
        scrapers.append(BetclicScraper())
    if site == "all" or site == "solverde":
        scrapers.append(SolverdeScraper())

    return scrapers


def create_mock_team_data(team_name: str) -> TeamData:
    """Create mock team data for demonstration"""
    import random

    # Mock data - in real version would fetch from APIs
    return TeamData(
        name=team_name,
        fifa_ranking=random.randint(1, 50),
        elo_rating=random.randint(1400, 2000),
        matches_played=10,
        wins=random.randint(4, 9),
        draws=random.randint(1, 4),
        losses=random.randint(0, 3),
        goals_scored=random.randint(15, 30),
        goals_conceded=random.randint(5, 15),
        avg_xg_for=random.uniform(1.5, 2.5),
        avg_xg_against=random.uniform(0.8, 1.5),
        avg_possession=random.uniform(45, 65),
        clean_sheets=random.randint(3, 7),
        rest_days=random.randint(2, 7),
    )


def calculate_market_averages(odds_list: List) -> dict:
    """Calculate average odds across all bookmakers"""
    from utils.ev_calculator import calculate_market_average

    home_odds = [o.home_win for o in odds_list if o.home_win]
    draw_odds = [o.draw for o in odds_list if o.draw]
    away_odds = [o.away_win for o in odds_list if o.away_win]
    over_odds = [o.over_2_5 for o in odds_list if o.over_2_5]
    btts_odds = [o.btts_yes for o in odds_list if o.btts_yes]

    return {
        "home_win": calculate_market_average(home_odds) if home_odds else 0,
        "draw": calculate_market_average(draw_odds) if draw_odds else 0,
        "away_win": calculate_market_average(away_odds) if away_odds else 0,
        "over_2_5": calculate_market_average(over_odds) if over_odds else 0,
        "btts_yes": calculate_market_average(btts_odds) if btts_odds else 0,
        "num_bookmakers": len(odds_list),
    }


def generate_recommendations(
    prediction: MatchPrediction,
    odds_list: List,
    market_avg: dict,
    min_ev: float,
    min_confidence: float,
) -> List[BetRecommendation]:
    """Generate bet recommendations based on prediction and odds"""
    from utils.ev_calculator import analyze_bet

    recommendations = []

    # 1X2 market recommendations
    for odds in odds_list:
        if odds.home_win:
            rec = analyze_bet(
                market="1X2 - Home Win",
                site=odds.site,
                site_name=odds.site_name,
                odds=odds.home_win,
                model_probability=prediction.home_win_prob,
                confidence=prediction.home_confidence,
                reasoning=prediction.key_factors,
                min_ev=min_ev,
                min_confidence=min_confidence,
            )
            recommendations.append(rec)

        if odds.draw:
            rec = analyze_bet(
                market="1X2 - Draw",
                site=odds.site,
                site_name=odds.site_name,
                odds=odds.draw,
                model_probability=prediction.draw_prob,
                confidence=prediction.draw_confidence,
                reasoning=prediction.key_factors,
                min_ev=min_ev,
                min_confidence=min_confidence,
            )
            recommendations.append(rec)

        if odds.away_win:
            rec = analyze_bet(
                market="1X2 - Away Win",
                site=odds.site,
                site_name=odds.site_name,
                odds=odds.away_win,
                model_probability=prediction.away_win_prob,
                confidence=prediction.away_confidence,
                reasoning=prediction.key_factors,
                min_ev=min_ev,
                min_confidence=min_confidence,
            )
            recommendations.append(rec)

        # Over/Under 2.5
        if odds.over_2_5:
            rec = analyze_bet(
                market="Over 2.5 Goals",
                site=odds.site,
                site_name=odds.site_name,
                odds=odds.over_2_5,
                model_probability=prediction.over_2_5_prob,
                confidence=65.0,  # Default confidence for secondary markets
                reasoning=prediction.key_factors,
                min_ev=min_ev,
                min_confidence=min_confidence,
            )
            recommendations.append(rec)

        # BTTS
        if odds.btts_yes:
            rec = analyze_bet(
                market="Both Teams To Score",
                site=odds.site,
                site_name=odds.site_name,
                odds=odds.btts_yes,
                model_probability=prediction.btts_prob,
                confidence=65.0,
                reasoning=prediction.key_factors,
                min_ev=min_ev,
                min_confidence=min_confidence,
            )
            recommendations.append(rec)

    return recommendations


def output_table(
    prediction: MatchPrediction,
    market_avg: dict,
    recommendations: List[BetRecommendation],
):
    """Output results as formatted table"""
    # Match info panel
    console.print(
        Panel(
            f"[bold]{prediction.home_team}[/bold] vs [bold]{prediction.away_team}[/bold]\n"
            f"Model: {prediction.home_win_prob * 100:.1f}% / {prediction.draw_prob * 100:.1f}% / {prediction.away_win_prob * 100:.1f}%\n"
            f"Over 2.5: {prediction.over_2_5_prob * 100:.1f}% | BTTS: {prediction.btts_prob * 100:.1f}%",
            title="📊 Model Prediction",
            box=box.ROUNDED,
        )
    )

    # Market averages
    if market_avg["num_bookmakers"] > 0:
        avg_table = Table(
            title=f"Market Average ({market_avg['num_bookmakers']} bookmakers)",
            box=box.SIMPLE,
        )
        avg_table.add_column("Market", style="cyan")
        avg_table.add_column("Average Odds", justify="right")

        if market_avg["home_win"]:
            avg_table.add_row("Home Win", f"{market_avg['home_win']:.2f}")
        if market_avg["draw"]:
            avg_table.add_row("Draw", f"{market_avg['draw']:.2f}")
        if market_avg["away_win"]:
            avg_table.add_row("Away Win", f"{market_avg['away_win']:.2f}")
        if market_avg["over_2_5"]:
            avg_table.add_row("Over 2.5", f"{market_avg['over_2_5']:.2f}")
        if market_avg["btts_yes"]:
            avg_table.add_row("BTTS Yes", f"{market_avg['btts_yes']:.2f}")

        console.print(avg_table)
        console.print()

    # Value bets
    value_bets = find_best_value_bets(recommendations)

    if value_bets:
        console.print("[bold green]✅ Best Value Bets:[/bold green]\n")

        bets_table = Table(box=box.ROUNDED)
        bets_table.add_column("Market", style="cyan")
        bets_table.add_column("Site", style="blue")
        bets_table.add_column("Odds", justify="right")
        bets_table.add_column("EV", justify="right", style="green")
        bets_table.add_column("Confidence", justify="right")

        for bet in value_bets[:10]:  # Top 10
            conf_icon = (
                "🟢" if bet.confidence >= 70 else "🟡" if bet.confidence >= 60 else "🔴"
            )
            bets_table.add_row(
                bet.market,
                bet.site_name,
                f"{bet.odds:.2f}",
                format_ev_display(bet.ev_percentage),
                f"{conf_icon} {bet.confidence:.0f}%",
            )

        console.print(bets_table)

        # Show reasoning for top bet
        if value_bets and value_bets[0].reasoning:
            console.print("\n[bold]💡 Key Factors:[/bold]")
            for factor in value_bets[0].reasoning[:3]:
                console.print(f"  • {factor}")
    else:
        console.print("[yellow]⚠️  No value bets found matching your criteria[/yellow]")


def output_json(
    prediction: MatchPrediction,
    market_avg: dict,
    recommendations: List[BetRecommendation],
):
    """Output results as JSON"""
    value_bets = find_best_value_bets(recommendations)

    result = {
        "match": {
            "home_team": prediction.home_team,
            "away_team": prediction.away_team,
            "probabilities": {
                "home_win": round(prediction.home_win_prob, 4),
                "draw": round(prediction.draw_prob, 4),
                "away_win": round(prediction.away_win_prob, 4),
                "over_2_5": round(prediction.over_2_5_prob, 4),
                "btts": round(prediction.btts_prob, 4),
            },
        },
        "market_averages": {
            k: round(v, 2) if isinstance(v, float) else v for k, v in market_avg.items()
        },
        "value_bets": [
            {
                "market": b.market,
                "site": b.site,
                "site_name": b.site_name,
                "odds": b.odds,
                "probability": round(b.probability, 4),
                "ev_percentage": round(b.ev_percentage, 2),
                "confidence": round(b.confidence, 2),
            }
            for b in value_bets[:10]
        ],
        "key_factors": prediction.key_factors,
    }

    console.print(json.dumps(result, indent=2))


def output_csv(recommendations: List[BetRecommendation]):
    """Output results as CSV"""
    import csv
    import io

    value_bets = find_best_value_bets(recommendations)

    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow(
        ["Market", "Site", "Odds", "Probability", "EV%", "Confidence", "IsValueBet"]
    )

    # Data rows
    for bet in value_bets:
        writer.writerow(
            [
                bet.market,
                bet.site_name,
                bet.odds,
                round(bet.probability, 4),
                round(bet.ev_percentage, 2),
                round(bet.confidence, 2),
                bet.is_value_bet,
            ]
        )

    console.print(output.getvalue())


if __name__ == "__main__":
    cli()
