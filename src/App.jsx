import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { TelegramProvider } from './contexts/TelegramContext'
import Layout from './components/Layout'
import MainPage from './pages/MainPage'
import SettingsPage from './pages/SettingsPage'
import ProfilePage from './pages/ProfilePage'
import SupportPage from './pages/SupportPage'
import './App.css'

function App() {
  return (
    <TelegramProvider>
      <Router>
        <Layout>
          <Routes>
            <Route path="/" element={<MainPage />} />
            <Route path="/settings" element={<SettingsPage />} />
            <Route path="/profile" element={<ProfilePage />} />
            <Route path="/support" element={<SupportPage />} />
          </Routes>
        </Layout>
      </Router>
    </TelegramProvider>
  )
}

export default App
