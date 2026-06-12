import { ScanMatchResult } from '@types/index'
import { TrendingUp, AlertCircle } from 'lucide-react'

interface MatchCardProps {
  match: ScanMatchResult
}

export function MatchCard({ match }: MatchCardProps) {
  const topBet = match.top_value_bet

  return (
    <div className="bg-gray-800 rounded-lg p-6 border border-gray-700 hover:border-primary-500 transition-colors">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-lg font-semibold">
            {match.home_team} vs {match.away_team}
          </h3>
          {match.match_date && (
            <p className="text-sm text-gray-400">
              {new Date(match.match_date).toLocaleDateString()}
            </p>
          )}
        </div>
        <div className="text-right">
          <span className="text-2xl font-bold text-primary-500">{match.value_bet_count}</span>
          <p className="text-sm text-gray-400">Value Bets</p>
        </div>
      </div>

      {topBet && (
        <div className="bg-gray-700 rounded-md p-4">
          <div className="flex items-center mb-2">
            <TrendingUp className="h-5 w-5 text-success mr-2" />
            <span className="font-medium">Top Value Bet</span>
          </div>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-gray-400">Market:</span>
              <p className="font-medium">{topBet.market}</p>
            </div>
            <div>
              <span className="text-gray-400">Bookmaker:</span>
              <p className="font-medium">{topBet.site_name}</p>
            </div>
            <div>
              <span className="text-gray-400">Odds:</span>
              <p className="font-medium">{topBet.odds.toFixed(2)}</p>
            </div>
            <div>
              <span className="text-gray-400">EV:</span>
              <p className="font-medium text-success">+{topBet.ev_percentage.toFixed(1)}%</p>
            </div>
          </div>
        </div>
      )}

      {!topBet && match.value_bet_count > 0 && (
        <div className="flex items-center text-yellow-500">
          <AlertCircle className="h-5 w-5 mr-2" />
          <span>Value bets available - view details for more information</span>
        </div>
      )}
    </div>
  )
}
