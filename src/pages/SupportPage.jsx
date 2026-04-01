import './SupportPage.css'

const SupportPage = () => {
  const handleFaqClick = () => {
    console.log('FAQ clicked')
  }

  const handleDeviceSetupClick = () => {
    console.log('Device setup clicked')
  }

  const handleSupportClick = () => {
    console.log('Support contact clicked')
  }

  return (
    <div className="support-page">
      <div className="main-support-block">
        <div className="support-icon-large">
          <svg width="60" height="60" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" stroke="currentColor" strokeWidth="2"/>
            <path d="M8 9h8M8 13h6" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
          </svg>
        </div>
        <h1 className="support-title">Связаться с поддержкой</h1>
        <p className="support-description">
          Получите ответы на популярные вопросы или обратитесь к нам за помощью
        </p>
      </div>

      <div className="support-item" onClick={handleFaqClick}>
        <div className="support-item-icon">
          <div className="icon-container">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" stroke="currentColor" strokeWidth="2"/>
              <path d="M8 9h8M8 13h6" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
            </svg>
          </div>
        </div>
        <div className="support-item-content">
          <h3>Часто задаваемые вопросы</h3>
          <p>Ответы на часто задаваемые вопросы</p>
        </div>
      </div>

      <div className="support-item" onClick={handleDeviceSetupClick}>
        <div className="support-item-icon">
          <div className="icon-container">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <rect x="2" y="3" width="20" height="14" rx="2" ry="2" stroke="currentColor" strokeWidth="2"/>
              <line x1="8" y1="21" x2="16" y2="21" stroke="currentColor" strokeWidth="2"/>
              <line x1="12" y1="17" x2="12" y2="21" stroke="currentColor" strokeWidth="2"/>
            </svg>
          </div>
        </div>
        <div className="support-item-content">
          <h3>Установка на другом устройстве</h3>
          <p>Подробная инструкция для установки</p>
        </div>
      </div>

      <div className="support-item" onClick={handleSupportClick}>
        <div className="support-item-icon">
          <div className="icon-container">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M16 8a6 6 0 0 1 6 6v7h-4v-7a2 2 0 0 0-2-2 2 2 0 0 0-2 2v7h-4v-7a6 6 0 0 1 6-6z" stroke="currentColor" strokeWidth="2"/>
              <rect x="2" y="9" width="4" height="12" stroke="currentColor" strokeWidth="2"/>
              <circle cx="4" cy="4" r="2" stroke="currentColor" strokeWidth="2"/>
            </svg>
          </div>
        </div>
        <div className="support-item-content">
          <h3>Поддержка</h3>
          <p>Связаться с поддержкой</p>
        </div>
      </div>
    </div>
  )
}

export default SupportPage
