import { Outlet, Link, useLocation } from 'react-router-dom'
import { Trophy, Calendar, Target, Users, Settings, Info } from 'lucide-react'
import { clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

function cn(...inputs: (string | undefined | null | false)[]) {
  return twMerge(clsx(inputs))
}

const navigation = [
  { name: 'Home', href: '/', icon: Trophy },
  { name: 'Matches', href: '/matches', icon: Calendar },
  { name: 'Betting', href: '/betting', icon: Target },
  { name: 'Leagues', href: '/leagues', icon: Users },
  { name: 'Settings', href: '/settings', icon: Settings },
  { name: 'About', href: '/about', icon: Info },
]

export function Layout() {
  const location = useLocation()

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      {/* Header */}
      <header className="bg-gray-800 border-b border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center">
              <Trophy className="h-8 w-8 text-primary-500" />
              <span className="ml-2 text-xl font-bold">World Cup Betting Insights</span>
            </div>
            <nav className="flex space-x-4">
              {navigation.map((item) => {
                const Icon = item.icon
                const isActive = location.pathname === item.href
                return (
                  <Link
                    key={item.name}
                    to={item.href}
                    className={cn(
                      'flex items-center px-3 py-2 rounded-md text-sm font-medium transition-colors',
                      isActive
                        ? 'bg-gray-700 text-white'
                        : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                    )}
                  >
                    <Icon className="h-4 w-4 mr-2" />
                    {item.name}
                  </Link>
                )
              })}
            </nav>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Outlet />
      </main>

      {/* Footer */}
      <footer className="bg-gray-800 border-t border-gray-700 mt-auto">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <p className="text-center text-sm text-gray-400">
            ⚠️ Responsible Gambling: This tool provides insights only. No guaranteed wins.
            You must be 18+ to gamble in Portugal.
          </p>
        </div>
      </footer>
    </div>
  )
}
