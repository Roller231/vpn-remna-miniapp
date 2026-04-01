import { useTelegram } from '../contexts/TelegramContext'
import './ProfilePage.css'

const ProfilePage = () => {
  const { user } = useTelegram()

  const handleCopyId = () => {
    if (user?.id) {
      navigator.clipboard.writeText(user.id.toString())
        .then(() => {
          console.log('ID copied to clipboard')
        })
        .catch(err => {
          console.error('Failed to copy ID: ', err)
        })
    }
  }

  return (
    <div className="profile-page">
      <div className="user-card">
        <div className="user-avatar">
          {user?.first_name?.[0] || 'U'}
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
    </div>
  )
}

export default ProfilePage
