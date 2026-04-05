import { useState, useEffect } from 'react'
import { fetchReferralStats, fetchReferralRewards } from '../api/client'
import { useTelegramBackButton } from '../hooks/useTelegramBackButton'
import './ReferralPage.css'

function formatDate(iso) {
  return new Date(iso).toLocaleDateString('ru-RU', {
    day: 'numeric', month: 'short', year: 'numeric',
  })
}

export default function ReferralPage() {
  useTelegramBackButton()

  const [stats, setStats]     = useState(null)
  const [rewards, setRewards] = useState([])
  const [total, setTotal]     = useState(0)
  const [loading, setLoading] = useState(true)
  const [copied, setCopied]   = useState(false)

  useEffect(() => {
    Promise.allSettled([fetchReferralStats(), fetchReferralRewards(1, 20)])
      .then(([s, r]) => {
        if (s.status === 'fulfilled') setStats(s.value)
        if (r.status === 'fulfilled') {
          setRewards(r.value.items || [])
          setTotal(r.value.total || 0)
        }
      })
      .finally(() => setLoading(false))
  }, [])

  const handleCopy = () => {
    if (!stats?.referral_link) return
    navigator.clipboard.writeText(stats.referral_link).then(() => {
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    })
  }

  const percent = stats?.cashback_percent ?? 0

  return (
    <div className="ref-page">

      {/* Header card */}
      <div className="ref-header-card">
        <div className="ref-header-icon">
          <svg width="26" height="26" viewBox="0 0 24 24" fill="none">
            <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"
              stroke="currentColor" strokeWidth="2" strokeLinejoin="round"/>
          </svg>
        </div>
        <h1 className="ref-header-title">Реферальная программа</h1>
        <p className="ref-header-sub">
          Приглашайте друзей и получайте кэшбэк с каждого их платежа
        </p>
      </div>

      {/* Stats row */}
      <div className="ref-stats-row">
        <div className="ref-stat-card">
          <span className="ref-stat-num">{loading ? '—' : (stats?.total_invitees ?? 0)}</span>
          <span className="ref-stat-label">Приглашено</span>
        </div>
        <div className="ref-stat-card">
          <span className="ref-stat-num">
            {loading ? '—' : `${parseFloat(stats?.total_earned ?? 0).toFixed(0)} ₽`}
          </span>
          <span className="ref-stat-label">Получено</span>
        </div>
      </div>

      {/* Info card */}
      <div className="ref-info-card">
        <svg className="ref-info-icon" width="18" height="18" viewBox="0 0 24 24" fill="none">
          <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2"/>
          <path d="M12 16v-4M12 8h.01" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
        </svg>
        <p className="ref-info-text">
          За каждого приглашённого друга вы получаете <strong>{percent}%</strong> кэшбэка
          со всех его оплат подписки. Кэшбэк зачисляется на баланс приложения.
        </p>
      </div>

      {/* Rewards list */}
      {loading ? (
        <div className="ref-empty-card">
          <p className="ref-empty-text">Загрузка…</p>
        </div>
      ) : rewards.length === 0 ? (
        <div className="ref-empty-card">
          <svg className="ref-empty-icon" width="40" height="40" viewBox="0 0 24 24" fill="none">
            <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"
              stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round"/>
          </svg>
          <p className="ref-empty-text">Еще нет записей</p>
        </div>
      ) : (
        <div className="ref-list">
          {rewards.map(r => (
            <div key={r.id} className="ref-reward-item">
              <div className="ref-reward-info">
                <span className="ref-reward-label">Кэшбэк от реферала</span>
                <span className="ref-reward-date">{formatDate(r.created_at)}</span>
              </div>
              <div className="ref-reward-right">
                <span className="ref-reward-amount">+{parseFloat(r.amount).toFixed(2)} ₽</span>
                <span className={`ref-reward-status ${r.is_credited ? 'credited' : 'pending'}`}>
                  {r.is_credited ? 'Зачислено' : 'Ожидание'}
                </span>
              </div>
            </div>
          ))}
          {rewards.length < total && (
            <p className="ref-list-more">Показано {rewards.length} из {total}</p>
          )}
        </div>
      )}

      {/* Referral link bar — above bottom nav, same style as ProfilePage sub-url-bar */}
      {stats?.referral_link && (
        <div className="sub-url-bar">
          <button className="sub-url-card" onClick={handleCopy}>
            <div className="sub-url-content">
              <div className="sub-url-text">{stats.referral_link}</div>
              <div className="sub-url-label">Ваша реферальная ссылка</div>
            </div>
            <div className="sub-url-copy">
              {copied
                ? <svg width="18" height="18" viewBox="0 0 24 24" fill="none"><path d="M20 6L9 17l-5-5" stroke="#2bb86a" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"/></svg>
                : <svg width="18" height="18" viewBox="0 0 24 24" fill="none"><rect x="9" y="9" width="13" height="13" rx="2" stroke="currentColor" strokeWidth="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" stroke="currentColor" strokeWidth="2"/></svg>
              }
            </div>
          </button>
        </div>
      )}
    </div>
  )
}
