import './SupportPage.css'

const SupportPage = () => {
  return (
    <div className="support-page">
      <div className="page-header">
        <h1>Поддержка</h1>
      </div>

      <div className="support-content">
        <div className="support-card">
          <div className="support-icon">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M21 15C21 15.5304 20.7893 16.0391 20.4142 16.4142C20.0391 16.7893 19.5304 17 19 17H7L3 21V5C3 4.46957 3.21071 3.96086 3.58579 3.58579C3.96086 3.21071 4.46957 3 5 3H19C19.5304 3 20.0391 3.21071 20.4142 3.58579C20.7893 3.96086 21 4.46957 21 5V15Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </div>
          <h2>Нужна помощь?</h2>
          <p>Наша команда поддержки готова помочь вам 24/7</p>
          <button className="btn-contact">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M21 11.5C21.0034 12.8199 20.6951 14.1219 20.1 15.3C19.3944 16.7118 18.3098 17.8992 16.9674 18.7293C15.6251 19.5594 14.0782 19.9994 12.5 20C11.1801 20.0035 9.87812 19.6951 8.7 19.1L3 21L4.9 15.3C4.30493 14.1219 3.99656 12.8199 4 11.5C4.00061 9.92179 4.44061 8.37488 5.27072 7.03258C6.10083 5.69028 7.28825 4.6056 8.7 3.90003C9.87812 3.30496 11.1801 2.99659 12.5 3.00003H13C15.0843 3.11502 17.053 3.99479 18.5291 5.47089C20.0052 6.94699 20.885 8.91568 21 11V11.5Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
            Написать в поддержку
          </button>
        </div>

        <div className="faq-section">
          <h3>Частые вопросы</h3>
          <div className="faq-item">
            <h4>Как установить VPN?</h4>
            <p>Нажмите на кнопку "Установка и настройка" на главной странице</p>
          </div>
          <div className="faq-item">
            <h4>Как продлить подписку?</h4>
            <p>Перейдите в профиль и нажмите "Пополнить баланс"</p>
          </div>
          <div className="faq-item">
            <h4>Не работает подключение</h4>
            <p>Проверьте настройки и попробуйте переподключиться</p>
          </div>
        </div>

        <div className="contact-info">
          <p>Email: support@vpnremna.com</p>
          <p>Telegram: @ultimavpnbot</p>
        </div>
      </div>
    </div>
  )
}

export default SupportPage
