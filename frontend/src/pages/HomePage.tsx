import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { api } from '@services/api'
import { TrendingUp, Search, Activity } from 'lucide-react'
import type { ScanResponse } from '@types/index'

export function HomePage() {
  const [daysAhead, setDaysAhead] = useState(7)
  const [minEv, setMinEv] = useState(5.0)

  const { data, isLoading, error, refetch } = useQuery<ScanResponse>({
    queryKey: ['scan', daysAhead, minEv],
    queryFn: () => api.scanMatches(daysAhead, 'all', minEv),
  })

  return (
    <div className="space-y-8">
      {/* Hero Section */}
      <div className="text-center py-12">
        <h1 className="text-4xl font-bold mb-4">
          AI-Powered Betting Insights
        </h1>
        <p className="text-xl text-gray-400 mb-8">
          Find value bets for World Cup matches by comparing AI predictions against odds from Portuguese bookmakers
        </p>
      </div>

      {/* Quick Stats */}
      {data && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
            <div className="flex items-center mb-2">
              <Activity className="h-6 w-6 text-primary-500 mr-2" />
              <h3 className="text-lg font-semibold">Matches Scanned</h3>
            </div>
            <p className="text-3xl font-bold">{data.total_matches}</p>
          </div>
          <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
            <div className="flex items-center mb-2">
              <TrendingUp className="h-6 w-6 text-success mr-2" />
              <h3 className="text-lg font-semibold">Matches with Value</h3>
            </div>
            <p className="text-3xl font-bold text-success">{data.matches_with_value_bets}</p>
          </div>
          <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
            <div className="flex items-center mb-2">
              <Search className="h-6 w-6 text-warning mr-2" />
              <h3 className="text-lg font-semibold">Total Value Bets</h3>
            </div>
            <p className="text-3xl font-bold text-warning">{data.total_value_bets}</p>
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
        <h2 className="text-xl font-semibold mb-4">Scan Settings</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-medium mb-2">Days Ahead</label>
            <input
              type="range"
              min="1"
              max="30"
              value={daysAhead}
              onChange={(e) => setDaysAhead(Number(e.target.value))}
              className="w-full"
            />
            <span className="text-sm text-gray-400">{daysAhead} days</span>
          </div>
          <div>
            <label className="block text-sm font-medium mb-2">Minimum EV (%)</label>
            <input
              type="range"
              min="0"
              max="20"
              step="0.5"
              value={minEv}
              onChange={(e) => setMinEv(Number(e.target.value))}
              className="w-full"
            />
            <span className="text-sm text-gray-400">{minEv}%</span>
          </div>
        </div>
        <button
          onClick={() => refetch()}
          className="mt-4 bg-primary-600 hover:bg-primary-700 text-white px-6 py-2 rounded-md font-medium transition-colors"
        >
          Refresh Scan
        </button>
      </div>

      {/* Results */}
      {isLoading && (
        <div className="text-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-500 mx-auto"></div>
          <p className="mt-4 text-gray-400">Scanning matches...</p>
        </div>
      )}

      {error && (
        <div className="bg-danger/10 border border-danger rounded-lg p-4">
          <p className="text-danger">Error loading scan data. Please try again.</p>
        </div>
      )}

      {data && data.matches.length > 0 && (
        <div>
          <h2 className="text-xl font-semibold mb-4">Recent Matches with Value Bets</h2>
          <div className="space-y-4">
            {data.matches.slice(0, 5).map((match) => (
              <div key={match.match_id} className="bg-gray-800 rounded-lg p-4 border border-gray-700">
                <div className="flex justify-between items-center">
                  <div>
                    <h3 className="font-medium">
                      {match.home_team} vs {match.away_team}
                    </h3>
                    {match.match_date && (
                      <p className="text-sm text-gray-400">
                        {new Date(match.match_date).toLocaleDateString()}
                      </p>
                    )}
                  </div>
                  <div className="text-right">
                    <p className="text-sm text-gray-400">{match.value_bet_count} value bets</p>
                    {match.top_value_bet && (
                      <p className="text-success font-medium">
                        Best EV: +{match.top_value_bet.ev_percentage.toFixed(1)}%
                      </p>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {data && data.matches.length === 0 && (
        <div className="text-center py-12 text-gray-400">
          <p>No matches found with the current filters</p>
        </div>
      )}
    </div>
  )
}
