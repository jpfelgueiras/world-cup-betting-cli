import { ExternalLink, Github, Shield, TrendingUp, Cpu } from 'lucide-react'

export function AboutPage() {
  return (
    <div className="space-y-8">
      <h1 className="text-3xl font-bold">About</h1>

      {/* Project Overview */}
      <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
        <h2 className="text-xl font-semibold mb-4">World Cup Betting Insights</h2>
        <p className="text-gray-300 mb-4">
          This application provides AI-powered betting insights for football matches by comparing 
          model-generated probabilities with odds from Portuguese licensed bookmakers.
        </p>
        <p className="text-gray-300">
          The goal is to identify value bets - situations where the model's assessed probability 
          suggests a bet has positive expected value (EV) compared to the bookmaker's odds.
        </p>
      </div>

      {/* Features */}
      <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
        <h2 className="text-xl font-semibold mb-4">Features</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="flex items-start">
            <Cpu className="h-6 w-6 text-primary-500 mr-3 mt-1" />
            <div>
              <h3 className="font-medium mb-1">AI Predictions</h3>
              <p className="text-sm text-gray-400">
                Machine learning models analyze team statistics, form, and historical data 
                to generate match outcome probabilities.
              </p>
            </div>
          </div>
          <div className="flex items-start">
            <TrendingUp className="h-6 w-6 text-success mr-3 mt-1" />
            <div>
              <h3 className="font-medium mb-1">Value Detection</h3>
              <p className="text-sm text-gray-400">
                Automatically identifies bets with positive expected value by comparing 
                model probabilities against market odds.
              </p>
            </div>
          </div>
          <div className="flex items-start">
            <Shield className="h-6 w-6 text-warning mr-3 mt-1" />
            <div>
              <h3 className="font-medium mb-1">Licensed Bookmakers</h3>
              <p className="text-sm text-gray-400">
                Integrates with SRIJ-regulated Portuguese bookmakers including Betano, 
                Betclic, Solverde, and more.
              </p>
            </div>
          </div>
          <div className="flex items-start">
            <ExternalLink className="h-6 w-6 text-blue-500 mr-3 mt-1" />
            <div>
              <h3 className="font-medium mb-1">REST API</h3>
              <p className="text-sm text-gray-400">
                Full RESTful API for programmatic access and integration with other 
                tools and services.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Technology Stack */}
      <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
        <h2 className="text-xl font-semibold mb-4">Technology Stack</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <h3 className="font-medium mb-2 text-primary-500">Backend</h3>
            <ul className="space-y-1 text-sm text-gray-400">
              <li>• Python 3.11</li>
              <li>• FastAPI</li>
              <li>• Pydantic</li>
              <li>• Scikit-learn & XGBoost</li>
              <li>• pytest</li>
            </ul>
          </div>
          <div>
            <h3 className="font-medium mb-2 text-success">Frontend</h3>
            <ul className="space-y-1 text-sm text-gray-400">
              <li>• React 18</li>
              <li>• TypeScript</li>
              <li>• Vite</li>
              <li>• Tailwind CSS</li>
              <li>• TanStack Query</li>
            </ul>
          </div>
        </div>
      </div>

      {/* Responsible Gambling */}
      <div className="bg-yellow-900/20 border border-yellow-700 rounded-lg p-6">
        <h2 className="text-xl font-semibold mb-4 text-yellow-500">⚠️ Responsible Gambling</h2>
        <p className="text-gray-300 mb-4">
          This software is for analysis and entertainment purposes only. There are no guaranteed wins.
        </p>
        <ul className="space-y-2 text-sm text-gray-300 mb-4">
          <li>• You must be 18+ to gamble in Portugal</li>
          <li>• Only use licensed operators</li>
          <li>• Never bet more than you can afford to lose</li>
          <li>• Gambling should not be seen as a way to make money</li>
        </ul>
        <a
          href="https://www.srij.turismodeportugal.pt/"
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center text-yellow-500 hover:text-yellow-400"
        >
          <ExternalLink className="h-4 w-4 mr-2" />
          Portuguese Gambling Authority (SRIJ)
        </a>
      </div>

      {/* Links */}
      <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
        <h2 className="text-xl font-semibold mb-4">Links</h2>
        <div className="space-y-2">
          <a
            href="https://github.com/jpfelgueiras/world-cup-betting-cli"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center text-primary-500 hover:text-primary-400"
          >
            <Github className="h-4 w-4 mr-2" />
            GitHub Repository
          </a>
          <a
            href="https://www.srij.turismodeportugal.pt/"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center text-primary-500 hover:text-primary-400"
          >
            <ExternalLink className="h-4 w-4 mr-2" />
            SRIJ - Portuguese Gambling Authority
          </a>
        </div>
      </div>
    </div>
  )
}
