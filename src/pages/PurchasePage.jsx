import { useState, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { useApi } from '../contexts/ApiContext'
import { purchaseWithYookassa } from '../api/client'
import AnimatedBackground from '../components/AnimatedBackground'
import './PurchasePage.css'

const DURATION_LABELS = {
  30:  '1 месяц',
  90:  '3 месяца',
  180: '6 месяцев',
  365: '1 год',
}
const MONTHS = { 30: 1, 90: 3, 180: 6, 365: 12 }

function perMonth(price, days) {
  const m = MONTHS[days] || Math.round(days / 30) || 1
  return Math.round(parseFloat(price) / m)
}

export default function PurchasePage() {
  const navigate = useNavigate()
  const { catalog, catalogLoading } = useApi()

  const allPlans = useMemo(() => catalog.flatMap(p => p.plans || []), [catalog])

  const deviceCounts = useMemo(() =>
    [...new Set(allPlans.map(p => p.devices))].sort((a, b) => a - b), [allPlans])

  const durations = useMemo(() =>
    [...new Set(allPlans.map(p => p.duration_days))].sort((a, b) => a - b), [allPlans])

  const [deviceIdx, setDeviceIdx]     = useState(0)
  const [selectedDays, setSelectedDays] = useState(null)
  const [paying, setPaying]           = useState(false)
  const [payError, setPayError]       = useState(null)
  const [showPaySheet, setShowPaySheet] = useState(false)

  const selectedDevices = deviceCounts[deviceIdx] ?? 1

  const activeDays = selectedDays ?? (
    durations.length > 0 ? (durations.includes(180) ? 180 : durations[0]) : 30
  )

  const selectedPlan = allPlans.find(
    p => p.devices === selectedDevices && p.duration_days === activeDays
  )

  const basePlan = allPlans.find(p => p.devices === 1 && p.duration_days === activeDays)

  const discount = useMemo(() => {
    if (!basePlan || selectedDevices <= 1) return null
    const full = parseFloat(basePlan.price) * selectedDevices
    const cur  = parseFloat(selectedPlan?.price || basePlan.price)
    if (full <= 0) return null
    const pct = Math.round((1 - cur / full) * 100)
    return pct > 0 ? pct : null
  }, [basePlan, selectedPlan, selectedDevices])

  const price     = selectedPlan ? parseFloat(selectedPlan.price) : null
  const origPrice = basePlan && selectedDevices > 1
    ? parseFloat(basePlan.price) * selectedDevices : null
  const hasStars  = selectedPlan?.price_stars > 0

  const handlePay = async (method = 'yookassa') => {
    if (!selectedPlan) return
    setPaying(true); setPayError(null); setShowPaySheet(false)
    try {
      if (method === 'yookassa') {
        const res = await purchaseWithYookassa(selectedPlan.id, window.location.href)
        if (res.payment_url) window.location.href = res.payment_url
      } else {
        window.Telegram?.WebApp?.openInvoice?.(`/buy_stars_${selectedPlan.id}`)
      }
    } catch (e) { setPayError(e.message) }
    finally { setPaying(false) }
  }

  const handlePayButton = () => {
    if (!selectedPlan) return
    if (hasStars) { setShowPaySheet(true); return }
    handlePay('yookassa')
  }

  const sliderPct = deviceCounts.length <= 1
    ? 100 : (deviceIdx / (deviceCounts.length - 1)) * 100

  return (
    <div className="pp-root">
      <AnimatedBackground />

      <div className="pp-scroll">
        {/* Back */}
        <button className="pp-back" onClick={() => navigate(-1)}>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
            <path d="M15 18l-6-6 6-6" stroke="currentColor" strokeWidth="2.5"
              strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
        </button>

        {/* Title */}
        <h1 className="pp-title">Покупка<br/>подписки</h1>
        <p className="pp-sub">
          Подключайте больше устройств и пользуйтесь сервисом вместе с друзьями и близкими
        </p>

        {catalogLoading ? (
          <div className="pp-loading">Загрузка планов…</div>
        ) : allPlans.length === 0 ? (
          <div className="pp-loading">Планы не найдены — добавьте через админ-панель</div>
        ) : (<>

          {/* ── Device card ── */}
          <div className="pp-device-card">
            <div className="pp-device-row">
              <div className="pp-device-circle">{selectedDevices}</div>
              <div className="pp-device-info">
                <span className="pp-device-label">Устройств</span>
                <span className="pp-device-sub">Одновременно в подписке</span>
              </div>
              {discount !== null && (
                <span className="pp-device-badge">-{discount}%</span>
              )}
            </div>

            {/* Track */}
            <div className="pp-track-wrap">
              <div className="pp-track">
                <div className="pp-track-fill" style={{ width: `${sliderPct}%` }} />
                {deviceCounts.map((_, i) => {
                  const pos = deviceCounts.length <= 1
                    ? 50 : (i / (deviceCounts.length - 1)) * 100
                  return (
                    <button
                      key={i}
                      className={`pp-dot${i < deviceIdx ? ' passed' : i === deviceIdx ? ' active' : ''}`}
                      style={{ left: `${pos}%` }}
                      onClick={() => { setDeviceIdx(i); setSelectedDays(null) }}
                    />
                  )
                })}
              </div>
            </div>
          </div>

          {/* ── Duration grid ── */}
          <div className="pp-grid">
            {durations.map(days => {
              const plan = allPlans.find(
                p => p.devices === selectedDevices && p.duration_days === days
              )
              const sel   = days === activeDays
              const best  = days === 180
              const pm    = plan ? perMonth(plan.price, days) : null
              const pFull = plan ? Math.round(parseFloat(plan.price)) : null
              const isMonthly = days === 30

              return (
                <button
                  key={days}
                  className={`pp-dur${sel ? ' sel' : ''}`}
                  onClick={() => setSelectedDays(days)}
                >
                  <div className="pp-dur-top">
                    <span className="pp-dur-label">
                      {DURATION_LABELS[days] ?? `${days} дн.`}
                    </span>
                    {best && <span className="pp-dur-star">★</span>}
                  </div>
                  {plan ? (<>
                    <span className="pp-dur-price">{pFull} ₽</span>
                    <span className="pp-dur-pm">
                      {isMonthly ? 'в месяц' : `${pm} ₽ в месяц`}
                    </span>
                  </>) : (
                    <span className="pp-dur-price" style={{opacity:.35}}>—</span>
                  )}
                </button>
              )
            })}
          </div>

          {payError && <p className="pp-error">{payError}</p>}
        </>)}

        {/* spacer so content doesn't hide under button */}
        <div className="pp-spacer" />
      </div>

      {/* ── Pay button ── */}
      {selectedPlan && (
        <div className="pp-bottom">
          <button className="pp-pay" onClick={handlePayButton} disabled={paying}>
            <span className="pp-pay-label">
              {paying ? 'Переход к оплате…' : 'Оплатить подписку'}
            </span>
            {!paying && price !== null && (
              <span className="pp-pay-prices">
                <span className="pp-pay-cur">{Math.round(price)} ₽</span>
                {origPrice && origPrice > price && (
                  <span className="pp-pay-old">{Math.round(origPrice)} ₽</span>
                )}
              </span>
            )}
          </button>
        </div>
      )}

      {/* ── Payment sheet ── */}
      {showPaySheet && (
        <div className="pp-overlay" onClick={() => setShowPaySheet(false)}>
          <div className="pp-sheet" onClick={e => e.stopPropagation()}>
            <p className="pp-sheet-title">Способ оплаты</p>
            <button className="pp-sheet-btn" onClick={() => handlePay('yookassa')}>
              💳 Банковская карта / ЮMoney — {Math.round(price)} ₽
            </button>
            {hasStars && (
              <button className="pp-sheet-btn pp-sheet-stars"
                onClick={() => handlePay('stars')}>
                ⭐ Telegram Stars — {selectedPlan.price_stars} Stars
              </button>
            )}
            <button className="pp-sheet-cancel" onClick={() => setShowPaySheet(false)}>
              Отмена
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
