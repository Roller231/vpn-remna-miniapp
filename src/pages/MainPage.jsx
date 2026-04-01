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
          <div className="expanding-circles">
            <div className="circle-wave circle-wave-1"></div>
            <div className="circle-wave circle-wave-2"></div>
            <div className="circle-wave circle-wave-3"></div>
            <div className="circle-wave circle-wave-4"></div>
          </div>
          <div className="logo-container">
            <img src="/img/logo.png" alt="VPN Logo" className="vpn-logo" />
            {isConnected && <div className="connection-indicator"></div>}
          </div>
        </div>

        <div className="status-info-container">
          <div className="status-left">
            <h2 className="subscription-date">
              до {formatDate(subscriptionEndDate)}
            </h2>
            <p className={`status-text ${isConnected ? 'online' : 'offline'}`}>
              {isConnected ? 'online' : 'offline'}
            </p>
          </div>
          <div className="trial-badge">
            пробный период
          </div>
        </div>
      </div>

      <div className="action-buttons">
        <button 
          className="btn-primary"
          onClick={handleConnect}
          disabled={isConnecting}
        >
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2"/>
            <path d="M12 6V12L16 14" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
          </svg>
          {isConnecting ? 'Подключение...' : isConnected ? 'Отключить' : 'Купить подписку'}
        </button>

        <button className="btn-secondary">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M13 2L3 14H12L11 22L21 10H12L13 2Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
          Установка и настройка
        </button>
      </div>

    </div>
  )
}

export default MainPage
