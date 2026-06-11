import axios, { AxiosInstance, AxiosError } from 'axios'
import type {
  MatchAnalysisResponse,
  ScanResponse,
  BookmakerStatus,
  HealthResponse,
} from '@types/index'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

class ApiClient {
  private client: AxiosInstance

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
      timeout: 30000,
    })

    // Request interceptor for adding auth headers
    this.client.interceptors.request.use(
      (config) => {
        const apiKey = import.meta.env.VITE_API_KEY
        if (apiKey) {
          config.headers['X-API-Key'] = apiKey
        }
        return config
      },
      (error) => Promise.reject(error)
    )

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError) => {
        if (error.response?.status === 401) {
          console.error('Authentication failed. Please check your API key.')
        } else if (error.response?.status === 429) {
          console.error('Rate limit exceeded. Please try again later.')
        }
        return Promise.reject(error)
      }
    )
  }

  async getHealth(): Promise<HealthResponse> {
    const response = await this.client.get<HealthResponse>('/health')
    return response.data
  }

  async getBookmakers(): Promise<BookmakerStatus[]> {
    const response = await this.client.get<BookmakerStatus[]>('/api/v1/bookmakers')
    return response.data
  }

  async predictMatch(
    homeTeam: string,
    awayTeam: string,
    site: string = 'all'
  ): Promise<MatchAnalysisResponse> {
    const response = await this.client.post<MatchAnalysisResponse>('/api/v1/predict', {
      home_team: homeTeam,
      away_team: awayTeam,
      site,
    })
    return response.data
  }

  async scanMatches(
    daysAhead: number = 7,
    site: string = 'all',
    minEv: number = 5.0
  ): Promise<ScanResponse> {
    const response = await this.client.post<ScanResponse>('/api/v1/scan', {
      days_ahead: daysAhead,
      site,
      min_ev: minEv,
    })
    return response.data
  }

  async getConfig() {
    const response = await this.client.get('/api/v1/config')
    return response.data
  }

  async updateConfig(config: Record<string, unknown>) {
    const response = await this.client.put('/api/v1/config', config)
    return response.data
  }
}

export const api = new ApiClient()
export default api
