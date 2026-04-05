import { useNavigate } from 'react-router-dom'
import { useApi } from '../contexts/ApiContext'
import './BalancePage.css'

export default function BalancePage() {
  const navigate = useNavigate()
  const { apiUser, subscription } = useApi()

  const balance  = (apiUser?.balance ?? 0).toFixed(2)
  const cashback = (apiUser?.total_cashback_earned ?? 0).toFixed(2)

  return (
    <div className="balance-page">

      {/* Header card */}
      <div className="bl-header-card">
        <div className="bl-header-icon">
          <svg width="28" height="28" viewBox="0 0 24 24" fill="none">
            <rect x="2" y="4" width="20" height="16" rx="2" stroke="currentColor" strokeWidth="2"/>
            <path d="M7 15h10M7 11h4" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
          </svg>
        </div>
        <h1 className="bl-header-title">Баланс и оплата</h1>
        <p className="bl-header-sub">
          Ваш текущий баланс и доступные способы оплаты подписки
        </p>
      </div>

      {/* Balance info card */}
      <div className="bl-card">
        <div className="bl-card-row">
          <span className="bl-card-label">Текущий баланс</span>
          <span className="bl-card-value">{balance} ₽</span>
        </div>
        <div className="bl-card-sep" />
        <div className="bl-card-row">
          <span className="bl-card-label">Кэшбэк получено</span>
          <span className="bl-card-value green">+{cashback} ₽</span>
        </div>
      </div>

      {/* Payment methods */}
      <div className="bl-card">
        <div className="bl-method">
          <div className="bl-method-icon-wrap">💳</div>
          <div className="bl-method-info">
            <span className="bl-method-name">ЮMoney / Банковская карта</span>
            <span className="bl-method-sub">Оплата через YooKassa</span>
          </div>
        </div>
        <div className="bl-card-sep" />
        <div className="bl-method">
          <div className="bl-method-icon-wrap">⭐</div>
          <div className="bl-method-info">
            <span className="bl-method-name">Telegram Stars</span>
            <span className="bl-method-sub">Для планов с поддержкой Stars</span>
          </div>
        </div>
        <div className="bl-card-sep" />
        <div className="bl-method">
          <div className="bl-method-icon-wrap">👛</div>
          <div className="bl-method-info">
            <span className="bl-method-name">Баланс приложения</span>
            <span className="bl-method-sub">{balance} ₽ доступно</span>
          </div>
        </div>
      </div>

      {/* Auto-renewal toggle */}
      {subscription && (
        <button
          className="bl-toggle-btn"
          onClick={() => {/* TODO: toggle auto-renewal */}}
        >
          {subscription.is_auto_renewal ? 'Отключить автопродление' : 'Включить автопродление'}
        </button>
      )}

    </div>
  )
}
