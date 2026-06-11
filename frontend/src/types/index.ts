export interface TeamProbabilities {
  home_win: number
  draw: number
  away_win: number
  over_2_5: number
  btts: number
}

export interface ConfidenceLevels {
  home_win: number
  draw: number
  away_win: number
}

export interface MarketAverage {
  home_win: number | null
  draw: number | null
  away_win: number | null
  over_2_5: number | null
  btts_yes: number | null
  num_bookmakers: number
}

export interface ValueBet {
  market: string
  site: string
  site_name: string
  odds: number
  probability: number
  ev_percentage: number
  confidence: number
  is_value_bet: boolean
  reasoning: string[]
}

export interface MatchAnalysisResponse {
  match_id: string
  home_team: string
  away_team: string
  match_date: string | null
  tournament_stage: string | null
  probabilities: TeamProbabilities
  confidence: ConfidenceLevels
  market_averages: MarketAverage
  value_bets: ValueBet[]
  key_factors: string[]
  metadata: Record<string, unknown>
}

export interface ScanMatchResult {
  match_id: string
  home_team: string
  away_team: string
  match_date: string | null
  value_bet_count: number
  top_value_bet: ValueBet | null
}

export interface ScanResponse {
  scan_date: string
  total_matches: number
  matches_with_value_bets: number
  total_value_bets: number
  matches: ScanMatchResult[]
  filters_applied: Record<string, unknown>
}

export interface BookmakerStatus {
  site_key: string
  site_name: string
  enabled: boolean
  rate_limit_seconds: number
  status: string
}

export interface HealthResponse {
  status: string
  version: string
  timestamp: string
  bookmakers: BookmakerStatus[]
  prediction_engine: string
  database: string
}

export interface League {
  id: string
  name: string
  country: string
  logo?: string
  matches_count: number
}

export interface Match {
  id: string
  home_team: string
  away_team: string
  date: string
  league_id: string
  status: 'scheduled' | 'live' | 'finished'
  home_score?: number
  away_score?: number
}
