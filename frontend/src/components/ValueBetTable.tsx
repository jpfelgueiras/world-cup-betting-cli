import { CheckCircle } from 'lucide-react'

interface ValueBetTableProps {
  bets: ValueBet[]
  limit?: number
}

export function ValueBetTable({ bets, limit }: ValueBetTableProps) {
  const displayBets = limit ? bets.slice(0, limit) : bets

  if (displayBets.length === 0) {
    return (
      <div className="text-center py-8 text-gray-400">
        <p>No value bets found matching your criteria</p>
      </div>
    )
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-gray-700">
            <th className="text-left py-3 px-4 font-medium">Market</th>
            <th className="text-left py-3 px-4 font-medium">Bookmaker</th>
            <th className="text-right py-3 px-4 font-medium">Odds</th>
            <th className="text-right py-3 px-4 font-medium">Probability</th>
            <th className="text-right py-3 px-4 font-medium">EV</th>
            <th className="text-center py-3 px-4 font-medium">Confidence</th>
          </tr>
        </thead>
        <tbody>
          {displayBets.map((bet, index) => (
            <tr key={index} className="border-b border-gray-800 hover:bg-gray-800">
              <td className="py-3 px-4">{bet.market}</td>
              <td className="py-3 px-4">{bet.site_name}</td>
              <td className="text-right py-3 px-4 font-medium">{bet.odds.toFixed(2)}</td>
              <td className="text-right py-3 px-4">{(bet.probability * 100).toFixed(1)}%</td>
              <td className="text-right py-3 px-4">
                <span className={bet.ev_percentage > 0 ? 'text-success' : 'text-danger'}>
                  {bet.ev_percentage > 0 ? '+' : ''}{bet.ev_percentage.toFixed(1)}%
                </span>
              </td>
              <td className="text-center py-3 px-4">
                <div className="flex items-center justify-center">
                  {bet.confidence >= 70 ? (
                    <CheckCircle className="h-4 w-4 text-success mr-1" />
                  ) : bet.confidence >= 60 ? (
                    <CheckCircle className="h-4 w-4 text-warning mr-1" />
                  ) : (
                    <CheckCircle className="h-4 w-4 text-danger mr-1" />
                  )}
                  <span>{bet.confidence.toFixed(0)}%</span>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
