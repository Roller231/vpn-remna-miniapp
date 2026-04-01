import { useState } from 'react'
import { useTelegram } from '../contexts/TelegramContext'
import './MainPage.css'

const MainPage = () => {
  const { user } = useTelegram()
  const [isConnected, setIsConnected] = useState(false)
  const [isConnecting, setIsConnecting] = useState(false)

  const handleConnect = async () => {
    setIsConnecting(true)
    setTimeout(() => {
      setIsConnected(!isConnected)
      setIsConnecting(false)
    }, 1500)
  }

  const formatDate = (date) => {
    const options = { day: 'numeric', month: 'long', year: 'numeric' }
    return new Date(date).toLocaleDateString('ru-RU', options)
  }

  const subscriptionEndDate = new Date()
  subscriptionEndDate.setDate(subscriptionEndDate.getDate() + 5)

  return (
    <div className="main-page">
      <div className="status-section">
        <div className={`connection-circle ${isConnected ? 'connected' : 'disconnected'} ${isConnecting ? 'connecting' : ''}`}>
          <div className="circle-inner">
            <svg width="80" height="80" viewBox="0 0 80 80" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M40 20C28.9543 20 20 28.9543 20 40C20 51.0457 28.9543 60 40 60C51.0457 60 60 51.0457 60 40C60 28.9543 51.0457 20 40 20Z" fill="currentColor" fillOpacity="0.2"/>
              <path d="M40 25C31.7157 25 25 31.7157 25 40C25 48.2843 31.7157 55 40 55C48.2843 55 55 48.2843 55 40C55 31.7157 48.2843 25 40 25Z" fill="currentColor" fillOpacity="0.3"/>
              <path d="M40 30C34.4772 30 30 34.4772 30 40C30 45.5228 34.4772 50 40 50C45.5228 50 50 45.5228 50 40C50 34.4772 45.5228 30 40 30Z" fill="currentColor"/>
              <path d="M35 38L38 41L45 34" stroke="white" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" opacity={isConnected ? "1" : "0"}/>
            </svg>
          </div>
        </div>

        <div className="status-info">
          <h2 className="subscription-date">
            до {formatDate(subscriptionEndDate)}
          </h2>
          <p className={`status-text ${isConnected ? 'online' : 'offline'}`}>
            {isConnected ? 'online' : 'offline'}
          </p>
        </div>
      </div>

      <div className="trial-badge">
        пробный период
      </div>

      <div className="action-buttons">
        <button 
          className="btn-primary"
          onClick={handleConnect}
          disabled={isConnecting}
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2"/>
            <path d="M12 6V12L16 14" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
          </svg>
          {isConnecting ? 'Подключение...' : isConnected ? 'Отключить' : 'Купить подписку'}
        </button>

        <button className="btn-secondary">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M13 2L3 14H12L11 22L21 10H12L13 2Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
          Установка и настройка
        </button>
      </div>

      <div className="footer-info">
        <p>@ultimavpnbot</p>
      </div>
    </div>
  )
}

export default MainPage
