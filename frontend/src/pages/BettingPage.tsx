import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { api } from '@services/api'
import { ValueBetTable } from '@components/ValueBetTable'
import type { MatchAnalysisResponse } from '@/types/index'
import { Search, TrendingUp } from 'lucide-react'

export function BettingPage() {
  const [homeTeam, setHomeTeam] = useState('')
  const [awayTeam, setAwayTeam] = useState('')

  const mutation = useMutation<MatchAnalysisResponse, Error, { home: string; away: string }>({
    mutationFn: ({ home, away }) => api.predictMatch(home, away),
  })

  const handleAnalyze = (e: React.FormEvent) => {
    e.preventDefault()
    if (homeTeam && awayTeam) {
      mutation.mutate({ home: homeTeam, away: awayTeam })
    }
  }

  return (
    <div className="space-y-8">
      <h1 className="text-3xl font-bold">Betting Analysis</h1>

      {/* Analysis Form */}
      <form onSubmit={handleAnalyze} className="bg-gray-800 rounded-lg p-6 border border-gray-700">
        <h2 className="text-xl font-semibold mb-4">Analyze a Match</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-medium mb-2">Home Team</label>
            <input
              type="text"
              value={homeTeam}
              onChange={(e) => setHomeTeam(e.target.value)}
              placeholder="e.g., Portugal"
              className="w-full bg-gray-700 border border-gray-600 rounded-md px-4 py-2 focus:outline-none focus:border-primary-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-2">Away Team</label>
            <input
              type="text"
              value={awayTeam}
              onChange={(e) => setAwayTeam(e.target.value)}
              placeholder="e.g., Brazil"
              className="w-full bg-gray-700 border border-gray-600 rounded-md px-4 py-2 focus:outline-none focus:border-primary-500"
            />
          </div>
        </div>
        <button
          type="submit"
          disabled={!homeTeam || !awayTeam || mutation.isPending}
          className="mt-6 bg-primary-600 hover:bg-primary-700 disabled:bg-gray-600 text-white px-6 py-2 rounded-md font-medium transition-colors flex items-center"
        >
          <Search className="h-4 w-4 mr-2" />
          {mutation.isPending ? 'Analyzing...' : 'Analyze Match'}
        </button>
      </form>

      {/* Results */}
      {mutation.data && (
        <div className="space-y-6">
          {/* Match Info */}
          <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
            <h2 className="text-2xl font-bold mb-2">
              {mutation.data.home_team} vs {mutation.data.away_team}
            </h2>
            {mutation.data.match_date && (
              <p className="text-gray-400">
                {new Date(mutation.data.match_date).toLocaleString()}
              </p>
            )}
          </div>

          {/* Probabilities */}
          <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
            <h3 className="text-xl font-semibold mb-4">Model Probabilities</h3>
            <div className="grid grid-cols-3 gap-4">
              <div className="text-center">
                <p className="text-3xl font-bold text-primary-500">
                  {(mutation.data.probabilities.home_win * 100).toFixed(1)}%
                </p>
                <p className="text-sm text-gray-400">Home Win</p>
              </div>
              <div className="text-center">
                <p className="text-3xl font-bold text-warning">
                  {(mutation.data.probabilities.draw * 100).toFixed(1)}%
                </p>
                <p className="text-sm text-gray-400">Draw</p>
              </div>
              <div className="text-center">
                <p className="text-3xl font-bold text-success">
                  {(mutation.data.probabilities.away_win * 100).toFixed(1)}%
                </p>
                <p className="text-sm text-gray-400">Away Win</p>
              </div>
            </div>
          </div>

          {/* Value Bets */}
          <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
            <div className="flex items-center mb-4">
              <TrendingUp className="h-6 w-6 text-success mr-2" />
              <h3 className="text-xl font-semibold">Value Bets</h3>
            </div>
            <ValueBetTable bets={mutation.data.value_bets} />
          </div>

          {/* Key Factors */}
          {mutation.data.key_factors.length > 0 && (
            <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
              <h3 className="text-xl font-semibold mb-4">Key Factors</h3>
              <ul className="space-y-2">
                {mutation.data.key_factors.map((factor, index) => (
                  <li key={index} className="flex items-start">
                    <span className="text-primary-500 mr-2">•</span>
                    <span>{factor}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {mutation.error && (
        <div className="bg-danger/10 border border-danger rounded-lg p-4">
          <p className="text-danger">Error analyzing match. Please try again.</p>
        </div>
      )}
    </div>
  )
}
