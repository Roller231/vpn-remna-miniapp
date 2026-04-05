import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useTelegram } from '../contexts/TelegramContext'
import { useApi } from '../contexts/ApiContext'
import { fetchLoginLink } from '../api/client'
import './ProfilePage.css'

const ProfilePage = () => {
  const navigate = useNavigate()
  const { user } = useTelegram()
  const [urlCopied, setUrlCopied] = useState(false)
  const [loginUrl, setLoginUrl]   = useState(null)

  useEffect(() => {
    fetchLoginLink().then(d => setLoginUrl(d?.login_url ?? null)).catch(() => {})
  }, [])

  const handleCopyId = () => {
    if (user?.id) {
      navigator.clipboard.writeText(user.id.toString())
        .then(() => console.log('ID copied to clipboard'))
        .catch(err => console.error('Failed to copy ID: ', err))
    }
  }

  const handleCopyUrl = () => {
    if (!loginUrl) return
    navigator.clipboard.writeText(loginUrl).then(() => {
      setUrlCopied(true)
      setTimeout(() => setUrlCopied(false), 2000)
    })
  }

  return (
    <div className="profile-page">
      <div className="user-card">
        <div className="user-avatar">
          {user?.photo_url ? (
            <img src={user.photo_url} alt="Avatar" className="avatar-image" />
          ) : (
            user?.first_name?.[0] || 'U'
          )}
        </div>
        
        <div className="user-info">
          <h2 className="user-name">
            {user?.first_name || 'Пользователь'}
          </h2>
          <p className="user-id">
            id: {user?.id || '—'}
          </p>
        </div>
        
        <button className="copy-button" onClick={handleCopyId}>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <rect x="9" y="9" width="13" height="13" rx="2" ry="2" stroke="currentColor" strokeWidth="2"/>
            <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" stroke="currentColor" strokeWidth="2"/>
          </svg>
        </button>
      </div>

      <div className="profile-menu">
        <div className="menu-items">
          <h3 className="menu-title">Настройки профиля</h3>
          
          <div className="menu-item clickable" onClick={() => navigate('/balance')}>
            <div className="menu-icon">
              <div className="icon-container">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <rect x="2" y="4" width="20" height="16" rx="2" stroke="currentColor" strokeWidth="2"/>
                  <path d="M7 15h10M7 11h4" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
                </svg>
              </div>
            </div>
            <div className="menu-content">
              <h4>Баланс и оплата</h4>
              <p>Ваш баланс и способы оплаты</p>
            </div>
          </div>

          <div className="menu-item clickable" onClick={() => navigate('/transactions')}>
            <div className="menu-icon">
              <div className="icon-container">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M3 3h18v18H3zM9 9h6v6H9z" stroke="currentColor" strokeWidth="2" strokeLinejoin="round"/>
                  <path d="M9 1v6M15 1v6M9 17v6M15 17v6M1 9h6M1 15h6M17 9h6M17 15h6" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
                </svg>
              </div>
            </div>
            <div className="menu-content">
              <h4>История операций</h4>
              <p>Список ваших транзакций</p>
            </div>
          </div>

          <div className="menu-item clickable" onClick={() => navigate('/referrals')}>
            <div className="menu-icon">
              <div className="icon-container">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" stroke="currentColor" strokeWidth="2"/>
                  <circle cx="9" cy="7" r="4" stroke="currentColor" strokeWidth="2"/>
                  <path d="M22 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75" stroke="currentColor" strokeWidth="2"/>
                </svg>
              </div>
            </div>
            <div className="menu-content">
              <h4>Реферальная программа</h4>
              <p>Получайте бонусы за приглашения</p>
            </div>
          </div>

          <div className="menu-item clickable" onClick={() => navigate('/save-access')}>
            <div className="menu-icon">
              <div className="icon-container">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" stroke="currentColor" strokeWidth="2"/>
                  <path d="M9 12l2 2 4-4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              </div>
            </div>
            <div className="menu-content">
              <h4>Сохранение доступа</h4>
              <p>На случай блокировки Telegram</p>
            </div>
          </div>
        </div>
      </div>

      <div className="profile-menu">
        <div className="menu-items">
          <h3 className="menu-title">Поддержка</h3>
          
          <div className="menu-item">
            <div className="menu-icon">
              <div className="icon-container">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <rect x="2" y="3" width="20" height="14" rx="2" ry="2" stroke="currentColor" strokeWidth="2"/>
                  <line x1="8" y1="21" x2="16" y2="21" stroke="currentColor" strokeWidth="2"/>
                  <line x1="12" y1="17" x2="12" y2="21" stroke="currentColor" strokeWidth="2"/>
                </svg>
              </div>
            </div>
            <div className="menu-content">
              <h4>Установка на другом устройстве</h4>
              <p>Подробная инструкция для установки</p>
            </div>
          </div>

          <div className="menu-item">
            <div className="menu-icon">
              <div className="icon-container">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" stroke="currentColor" strokeWidth="2"/>
                  <path d="M8 9h8M8 13h6" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
                </svg>
              </div>
            </div>
            <div className="menu-content">
              <h4>Связаться с поддержкой</h4>
              <p>Решение проблем онлайн</p>
            </div>
          </div>

          <div className="menu-item">
            <div className="menu-icon">
              <div className="icon-container">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" stroke="currentColor" strokeWidth="2"/>
                  <polyline points="14,2 14,8 20,8" stroke="currentColor" strokeWidth="2"/>
                  <line x1="16" y1="13" x2="8" y2="13" stroke="currentColor" strokeWidth="2"/>
                  <line x1="16" y1="17" x2="8" y2="17" stroke="currentColor" strokeWidth="2"/>
                  <polyline points="10,9 9,9 8,9" stroke="currentColor" strokeWidth="2"/>
                </svg>
              </div>
            </div>
            <div className="menu-content">
              <h4>Пользовательское соглашение</h4>
              <p>Соглашения и правила сервиса</p>
            </div>
          </div>
        </div>
      </div>
      {loginUrl && (
        <div className="sub-url-bar">
          <button className="sub-url-card" onClick={handleCopyUrl}>
            <div className="sub-url-text">{loginUrl}</div>
            <div className="sub-url-copy">
              {urlCopied
                ? <svg width="18" height="18" viewBox="0 0 24 24" fill="none"><path d="M20 6L9 17l-5-5" stroke="#2bb86a" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"/></svg>
                : <svg width="18" height="18" viewBox="0 0 24 24" fill="none"><rect x="9" y="9" width="13" height="13" rx="2" stroke="currentColor" strokeWidth="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" stroke="currentColor" strokeWidth="2"/></svg>
              }
            </div>
          </button>
          <p className="sub-url-label">Ваша ссылка на личный кабинет</p>
        </div>
      )}
    </div>
  )
}

export default ProfilePage
