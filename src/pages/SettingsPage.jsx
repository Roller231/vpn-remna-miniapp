import './SettingsPage.css'

const SettingsPage = () => {
  const handleStartSetup = () => {
    console.log('Start setup on this device')
  }

  const handleSetupOtherDevice = () => {
    console.log('Setup on other device')
  }

  return (
    <div className="settings-page">
      <div className="setup-header">
        <h1 className="setup-title">Настройка на iOS</h1>
        <p className="setup-subtitle">
          Настройка VPN происходит в 3 шага<br />
          и занимает пару минут
        </p>
      </div>

      <div className="setup-animation-section">
        <div className="setup-circle">
          <div className="expanding-circles">
            <div className="circle-wave circle-wave-1"></div>
            <div className="circle-wave circle-wave-2"></div>
            <div className="circle-wave circle-wave-3"></div>
            <div className="circle-wave circle-wave-4"></div>
          </div>
          <div className="static-circle">
            <div className="plug-icon">
              <img src="/img/rozet.png" alt="Rozet" className="rozet-logo" />
            </div>
          </div>
        </div>
      </div>

      <div className="setup-buttons">
        <button className="btn-primary" onClick={handleStartSetup}>
          Начать настройку на этом устройстве
        </button>

        <button className="btn-secondary" onClick={handleSetupOtherDevice}>
          Установить на другом устройстве
        </button>
      </div>
    </div>
  )
}

export default SettingsPage
