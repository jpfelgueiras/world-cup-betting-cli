import { useQuery } from '@tanstack/react-query'
import { api } from '@services/api'
import type { BookmakerStatus } from '@types/index'
import { ExternalLink, Shield } from 'lucide-react'

export function LeaguesPage() {
  const { data: bookmakers, isLoading, error } = useQuery<BookmakerStatus[]>({
    queryKey: ['bookmakers'],
    queryFn: () => api.getBookmakers(),
  })

  // Mock leagues data - would come from backend in production
  const leagues = [
    { id: '1', name: 'FIFA World Cup', country: 'International', matches_count: 48 },
    { id: '2', name: 'UEFA Euro', country: 'Europe', matches_count: 51 },
    { id: '3', name: 'Primeira Liga', country: 'Portugal', matches_count: 306 },
    { id: '4', name: 'Premier League', country: 'England', matches_count: 380 },
    { id: '5', name: 'La Liga', country: 'Spain', matches_count: 380 },
  ]

  return (
    <div className="space-y-8">
      <h1 className="text-3xl font-bold">Leagues & Bookmakers</h1>

      {/* Leagues Section */}
      <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
        <h2 className="text-xl font-semibold mb-4">Available Leagues</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {leagues.map((league) => (
            <div key={league.id} className="bg-gray-700 rounded-md p-4">
              <h3 className="font-medium">{league.name}</h3>
              <p className="text-sm text-gray-400">{league.country}</p>
              <p className="text-sm text-primary-500 mt-2">{league.matches_count} matches</p>
            </div>
          ))}
        </div>
      </div>

      {/* Bookmakers Section */}
      <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
        <h2 className="text-xl font-semibold mb-4">Portuguese Licensed Bookmakers</h2>
        
        {isLoading && (
          <div className="text-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500 mx-auto"></div>
          </div>
        )}

        {error && (
          <div className="text-danger">Error loading bookmakers</div>
        )}

        {bookmakers && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {bookmakers.map((bookmaker) => (
              <div key={bookmaker.site_key} className="bg-gray-700 rounded-md p-4">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="font-medium">{bookmaker.site_name}</h3>
                  <Shield className={`h-5 w-5 ${bookmaker.enabled ? 'text-success' : 'text-gray-500'}`} />
                </div>
                <div className="space-y-1 text-sm">
                  <p className="text-gray-400">
                    Status: <span className={bookmaker.enabled ? 'text-success' : 'text-danger'}>
                      {bookmaker.enabled ? 'Enabled' : 'Disabled'}
                    </span>
                  </p>
                  <p className="text-gray-400">
                    Rate Limit: {bookmaker.rate_limit_seconds}s
                  </p>
                </div>
              </div>
            ))}
          </div>
        )}

        <div className="mt-6 p-4 bg-blue-900/20 border border-blue-800 rounded-md">
          <div className="flex items-start">
            <Shield className="h-5 w-5 text-blue-400 mr-2 mt-0.5" />
            <div>
              <h4 className="font-medium text-blue-400 mb-1">SRIJ Regulated</h4>
              <p className="text-sm text-blue-300">
                All listed bookmakers are licensed and regulated by SRIJ 
                (Serviço de Regulação e Inspeção de Jogos), the Portuguese Gambling Authority.
              </p>
              <a
                href="https://www.srij.turismodeportugal.pt/"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center text-sm text-blue-400 hover:text-blue-300 mt-2"
              >
                <ExternalLink className="h-3 w-3 mr-1" />
                Verify licenses at SRIJ
              </a>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
