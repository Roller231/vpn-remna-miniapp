import { useTelegram } from '../contexts/TelegramContext'
import './ProfilePage.css'

const ProfilePage = () => {
  const { user } = useTelegram()

  return (
    <div className="profile-page">
      <div className="page-header">
        <h1>Профиль</h1>
      </div>

      <div className="profile-content">
        <div className="profile-card">
          <div className="profile-avatar">
            {user?.first_name?.[0] || 'U'}
          </div>
          <h2 className="profile-name">
            {user?.first_name || 'Пользователь'} {user?.last_name || ''}
          </h2>
          {user?.username && (
            <p className="profile-username">@{user.username}</p>
          )}
        </div>

        <div className="balance-card">
          <div className="balance-header">
            <span>Баланс</span>
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2"/>
              <path d="M12 6V12L16 14" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
            </svg>
          </div>
          <div className="balance-amount">199 ₽</div>
          <button className="btn-topup">Пополнить</button>
        </div>

        <div className="info-section">
          <h3>Информация</h3>
          <div className="info-item">
            <span>ID пользователя</span>
            <span className="info-value">{user?.id || '—'}</span>
          </div>
          <div className="info-item">
            <span>Дата регистрации</span>
            <span className="info-value">1 апреля 2026</span>
          </div>
          <div className="info-item">
            <span>Статус подписки</span>
            <span className="info-value status-trial">Пробный период</span>
          </div>
        </div>
      </div>
    </div>
  )
}

export default ProfilePage
