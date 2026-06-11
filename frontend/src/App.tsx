import { Routes, Route } from 'react-router-dom'
import { Layout } from '@components/Layout'
import { HomePage } from '@pages/HomePage'
import { MatchesPage } from '@pages/MatchesPage'
import { BettingPage } from '@pages/BettingPage'
import { LeaguesPage } from '@pages/LeaguesPage'
import { SettingsPage } from '@pages/SettingsPage'
import { AboutPage } from '@pages/AboutPage'

function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<HomePage />} />
        <Route path="matches" element={<MatchesPage />} />
        <Route path="betting" element={<BettingPage />} />
        <Route path="leagues" element={<LeaguesPage />} />
        <Route path="settings" element={<SettingsPage />} />
        <Route path="about" element={<AboutPage />} />
      </Route>
    </Routes>
  )
}

export default App
