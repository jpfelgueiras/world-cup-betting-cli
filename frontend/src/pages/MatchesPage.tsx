import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { api } from '@services/api'
import { MatchCard } from '@components/MatchCard'
import { Search } from 'lucide-react'
import type { ScanResponse } from '@types/index'

export function MatchesPage() {
  const [searchTerm, setSearchTerm] = useState('')
  const [sortBy, setSortBy] = useState<'date' | 'ev'>('ev')

  const { data, isLoading, error } = useQuery<ScanResponse>({
    queryKey: ['scan-all'],
    queryFn: () => api.scanMatches(7, 'all', 0),
  })

  const filteredMatches = data?.matches.filter((match) =>
    match.home_team.toLowerCase().includes(searchTerm.toLowerCase()) ||
    match.away_team.toLowerCase().includes(searchTerm.toLowerCase())
  )

  const sortedMatches = filteredMatches?.sort((a, b) => {
    if (sortBy === 'ev') {
      return (b.top_value_bet?.ev_percentage || 0) - (a.top_value_bet?.ev_percentage || 0)
    }
    return 0 // Date sorting would go here
  })

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">Matches</h1>
        <div className="flex items-center space-x-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search teams..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="bg-gray-800 border border-gray-700 rounded-md pl-10 pr-4 py-2 text-sm focus:outline-none focus:border-primary-500"
            />
          </div>
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as 'date' | 'ev')}
            className="bg-gray-800 border border-gray-700 rounded-md px-4 py-2 text-sm focus:outline-none focus:border-primary-500"
          >
            <option value="ev">Sort by EV</option>
            <option value="date">Sort by Date</option>
          </select>
        </div>
      </div>

      {isLoading && (
        <div className="text-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-500 mx-auto"></div>
          <p className="mt-4 text-gray-400">Loading matches...</p>
        </div>
      )}

      {error && (
        <div className="bg-danger/10 border border-danger rounded-lg p-4">
          <p className="text-danger">Error loading matches. Please try again.</p>
        </div>
      )}

      {sortedMatches && sortedMatches.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {sortedMatches.map((match) => (
            <MatchCard key={match.match_id} match={match} />
          ))}
        </div>
      ) : (
        !isLoading && (
          <div className="text-center py-12 text-gray-400">
            <p>No matches found</p>
          </div>
        )
      )}
    </div>
  )
}
