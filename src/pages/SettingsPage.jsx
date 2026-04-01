import './SettingsPage.css'

const SettingsPage = () => {
  return (
    <div className="settings-page">
      <div className="page-header">
        <h1>Настройки</h1>
      </div>
      
      <div className="settings-content">
        <div className="settings-section">
          <h2>Общие настройки</h2>
          <div className="setting-item">
            <span>Автоподключение</span>
            <label className="toggle">
              <input type="checkbox" />
              <span className="slider"></span>
            </label>
          </div>
          <div className="setting-item">
            <span>Уведомления</span>
            <label className="toggle">
              <input type="checkbox" defaultChecked />
              <span className="slider"></span>
            </label>
          </div>
        </div>

        <div className="settings-section">
          <h2>Протокол</h2>
          <div className="setting-item">
            <span>WireGuard</span>
            <input type="radio" name="protocol" defaultChecked />
          </div>
          <div className="setting-item">
            <span>OpenVPN</span>
            <input type="radio" name="protocol" />
          </div>
        </div>
      </div>
    </div>
  )
}

export default SettingsPage
