import { useState, useEffect } from 'react'
import { fetchLoginLink } from '../api/client'
import { useTelegramBackButton } from '../hooks/useTelegramBackButton'
import './SaveAccessPage.css'

const CHANNEL_URL = import.meta.env.VITE_TELEGRAM_CHANNEL_URL || ''

export default function SaveAccessPage() {
  useTelegramBackButton()

  const [loginUrl, setLoginUrl]   = useState(null)
  const [copied, setCopied]       = useState(false)
  const [loading, setLoading]     = useState(true)

  useEffect(() => {
    fetchLoginLink()
      .then(data => {
        if (data?.login_token) setLoginUrl(`${window.location.origin}/?token=${data.login_token}`)
        else if (data?.login_url) setLoginUrl(data.login_url)
      })
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  const handleCopy = () => {
    if (!loginUrl) return
    navigator.clipboard.writeText(loginUrl).then(() => {
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    })
  }

  const handleChannel = () => {
    if (!CHANNEL_URL) return
    window.Telegram?.WebApp?.openLink?.(CHANNEL_URL) ?? window.open(CHANNEL_URL, '_blank')
  }

  return (
    <div className="sa-page">

      {/* Header card */}
      <div className="sa-header-card">
        <div className="sa-header-icon">
          <svg width="26" height="26" viewBox="0 0 24 24" fill="none">
            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"
              stroke="currentColor" strokeWidth="2" strokeLinejoin="round"/>
            <path d="M9 12l2 2 4-4" stroke="currentColor" strokeWidth="2"
              strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
        </div>
        <h1 className="sa-header-title">Сохранение доступа</h1>
        <p className="sa-header-sub">
          Для сохранения доступа в случае блокировки Telegram рекомендуем выполнить несколько простых шагов
        </p>
      </div>

      {/* Telegram channel */}
      <div className="sa-step-card">
        <div className="sa-step-top">
          <div className="sa-step-icon">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
              <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2"/>
              <path d="M12 16v-4M12 8h.01" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
            </svg>
          </div>
          <div>
            <p className="sa-step-title">Подпишитесь на Telegram-канал</p>
            <p className="sa-step-sub">Для получения важной информации</p>
          </div>
        </div>
        <button
          className="sa-btn"
          onClick={handleChannel}
          disabled={!CHANNEL_URL}
        >
          Подписаться на канал
        </button>
      </div>

      {/* Login link */}
      <div className="sa-link-section">
        <p className="sa-link-title">Сохраните ссылку на личный кабинет</p>
        <p className="sa-link-sub">
          С помощью этой ссылки вы можете получить доступ к личному кабинету через браузер
        </p>
        <button className="sa-link-card" onClick={handleCopy} disabled={loading || !loginUrl}>
          <span className="sa-link-content">
            <span className="sa-link-text">
              {loading ? 'Загрузка…' : (loginUrl ?? 'Ссылка недоступна')}
            </span>
            <span className="sa-link-sublabel">Ссылка на личный кабинет</span>
          </span>
          <span className="sa-link-copy">
            {copied
              ? <svg width="18" height="18" viewBox="0 0 24 24" fill="none"><path d="M20 6L9 17l-5-5" stroke="#2bb86a" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"/></svg>
              : <svg width="18" height="18" viewBox="0 0 24 24" fill="none"><rect x="9" y="9" width="13" height="13" rx="2" stroke="currentColor" strokeWidth="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" stroke="currentColor" strokeWidth="2"/></svg>
            }
          </span>
        </button>
      </div>

    </div>
  )
}
