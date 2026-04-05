import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { TelegramProvider, useTelegram } from './contexts/TelegramContext'
import { ApiProvider } from './contexts/ApiContext'
import Layout from './components/Layout'
import MainPage from './pages/MainPage'
import SettingsPage from './pages/SettingsPage'
import ProfilePage from './pages/ProfilePage'
import SupportPage from './pages/SupportPage'
import PurchasePage from './pages/PurchasePage'
import BalancePage from './pages/BalancePage'
import TransactionsPage from './pages/TransactionsPage'
import ReferralPage from './pages/ReferralPage'
import SaveAccessPage from './pages/SaveAccessPage'
import './App.css'

function AppWithApi() {
  const { webApp } = useTelegram()
  return (
    <ApiProvider webApp={webApp}>
      <Router>
        <Routes>
          <Route path="/purchase" element={<PurchasePage />} />
          <Route path="/*" element={
            <Layout>
              <Routes>
                <Route path="/" element={<MainPage />} />
                <Route path="/settings" element={<SettingsPage />} />
                <Route path="/profile" element={<ProfilePage />} />
                <Route path="/balance" element={<BalancePage />} />
                <Route path="/transactions" element={<TransactionsPage />} />
                <Route path="/referrals" element={<ReferralPage />} />
                <Route path="/save-access" element={<SaveAccessPage />} />
                <Route path="/support" element={<SupportPage />} />
              </Routes>
            </Layout>
          } />
        </Routes>
      </Router>
    </ApiProvider>
  )
}

function App() {
  return (
    <TelegramProvider>
      <AppWithApi />
    </TelegramProvider>
  )
}

export default App
