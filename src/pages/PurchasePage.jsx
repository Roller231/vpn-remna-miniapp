import { useState, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { useApi } from '../contexts/ApiContext'
import { purchaseWithYookassa } from '../api/client'
import AnimatedBackground from '../components/AnimatedBackground'
import './PurchasePage.css'

const DURATION_LABELS = {
  30: '1 месяц',
  90: '3 месяца',
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
    [...new Set(allPlans.map(p => p.devices))].sort((a, b) => a - b),
    [allPlans]
  )
  const durations = useMemo(() =>
    [...new Set(allPlans.map(p => p.duration_days))].sort((a, b) => a - b),
    [allPlans]
  )

  const [deviceIdx, setDeviceIdx] = useState(0)
  const [selectedDays, setSelectedDays] = useState(null)
  const [paying, setPaying] = useState(false)
  const [payError, setPayError] = useState(null)
  const [showPaySheet, setShowPaySheet] = useState(false)

  const selectedDevices = deviceCounts[deviceIdx] ?? 1

  const activeDays = selectedDays ?? (durations.length > 0
    ? (durations.includes(180) ? 180 : durations[0])
    : 30)

  const selectedPlan = allPlans.find(
    p => p.devices === selectedDevices && p.duration_days === activeDays
  )

  const basePlan = allPlans.find(
    p => p.devices === 1 && p.duration_days === activeDays
  )

  const discount = useMemo(() => {
    if (!basePlan || selectedDevices <= 1) return null
    const full = parseFloat(basePlan.price) * selectedDevices
    const cur  = parseFloat(selectedPlan?.price || basePlan.price)
    if (full <= 0) return null
    const pct = Math.round((1 - cur / full) * 100)
    return pct > 0 ? pct : null
  }, [basePlan, selectedPlan, selectedDevices])

  const price = selectedPlan ? parseFloat(selectedPlan.price) : null
  const origPrice = basePlan && selectedDevices > 1
    ? parseFloat(basePlan.price) * selectedDevices
    : null

  const hasStars = selectedPlan?.price_stars > 0

  const handlePay = async (method = 'yookassa') => {
    if (!selectedPlan) return
    setPaying(true)
    setPayError(null)
    setShowPaySheet(false)
    try {
      if (method === 'yookassa') {
        const res = await purchaseWithYookassa(selectedPlan.id, window.location.href)
        if (res.payment_url) window.location.href = res.payment_url
      } else if (method === 'stars') {
        window.Telegram?.WebApp?.openInvoice?.(`/buy_stars_${selectedPlan.id}`)
      }
    } catch (e) {
      setPayError(e.message)
    } finally {
      setPaying(false)
    }
  }

  const handlePayButton = () => {
    if (!selectedPlan) return
    if (hasStars) { setShowPaySheet(true); return }
    handlePay('yookassa')
  }

  return (
    <div className="purchase-page">
      <AnimatedBackground />
      <button className="purchase-back" onClick={() => navigate(-1)}>
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
          <path d="M15 18l-6-6 6-6" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"/>
        </svg>
      </button>

      <div className="purchase-scroll">
        <h1 className="purchase-title">Покупка<br />подписки</h1>
        <p className="purchase-subtitle">
          Подключайте больше устройств и пользуйтесь<br />
          сервисом вместе с друзьями и близкими
        </p>

        {catalogLoading ? (
          <div className="purchase-loading">Загрузка планов…</div>
        ) : allPlans.length === 0 ? (
          <div className="purchase-loading">Планы не найдены — добавьте их через админ-панель</div>
        ) : (
          <>
            {/* ── Devices selector ── */}
            <div className="device-card">
              <div className="device-card-top">
                <div className="device-count-wrap">
                  <span className="device-number">{selectedDevices}</span>
                  <div className="device-label-wrap">
                    <span className="device-label">Устройства</span>
                    <span className="device-sublabel">Одновременно в подписке</span>
                  </div>
                </div>
                {discount !== null && (
                  <span className="device-discount">-{discount}%</span>
                )}
              </div>
              <div className="device-slider-wrap">
                <input
                  type="range"
                  min={0}
                  max={Math.max(0, deviceCounts.length - 1)}
                  step={1}
                  value={deviceIdx}
                  onChange={e => { setDeviceIdx(Number(e.target.value)); setSelectedDays(null) }}
                  className="device-slider"
                  style={{
                    background: deviceCounts.length <= 1 ? '#85b5dd' :
                      `linear-gradient(to right, #85b5dd ${deviceIdx / (deviceCounts.length - 1) * 100}%, rgba(133,181,221,0.15) ${deviceIdx / (deviceCounts.length - 1) * 100}%)`
                  }}
                />
                <div className="slider-dots">
                  {deviceCounts.map((_, i) => (
                    <span
                      key={i}
                      className={`slider-dot ${i <= deviceIdx ? 'active' : ''}`}
                      onClick={() => { setDeviceIdx(i); setSelectedDays(null) }}
                    />
                  ))}
                </div>
              </div>
            </div>

            {/* ── Duration grid ── */}
            <div className="duration-grid">
              {durations.map(days => {
                const plan = allPlans.find(
                  p => p.devices === selectedDevices && p.duration_days === days
                )
                const isSelected = days === activeDays
                const isBest = days === 180
                return (
                  <button
                    key={days}
                    className={`duration-card ${isSelected ? 'selected' : ''}`}
                    onClick={() => setSelectedDays(days)}
                  >
                    <div className="duration-header">
                      <span className="duration-label">
                        {DURATION_LABELS[days] ?? `${days} дней`}
                      </span>
                      {isBest && <span className="duration-star">★</span>}
                    </div>
                    {plan ? (
                      <>
                        <span className="duration-price">
                          {Math.round(parseFloat(plan.price))} ₽
                        </span>
                        <span className="duration-per-month">
                          {perMonth(plan.price, days)} ₽ в месяц
                        </span>
                      </>
                    ) : (
                      <span className="duration-price" style={{ opacity: 0.4 }}>—</span>
                    )}
                  </button>
                )
              })}
            </div>

            {payError && <p className="purchase-error">{payError}</p>}
          </>
        )}
      </div>

      {/* ── Bottom pay button ── */}
      {selectedPlan && (
        <div className="purchase-bottom">
          <button
            className="pay-button"
            onClick={handlePayButton}
            disabled={paying}
          >
            <span className="pay-label">
              {paying ? 'Переход к оплате…' : 'Оплатить подписку'}
            </span>
            {!paying && price !== null && (
              <span className="pay-price-wrap">
                <span className="pay-price">{Math.round(price)} ₽</span>
                {origPrice && origPrice > price && (
                  <span className="pay-orig">{Math.round(origPrice)} ₽</span>
                )}
              </span>
            )}
          </button>
        </div>
      )}

      {/* ── Payment method sheet ── */}
      {showPaySheet && (
        <div className="pay-sheet-overlay" onClick={() => setShowPaySheet(false)}>
          <div className="pay-sheet" onClick={e => e.stopPropagation()}>
            <p className="pay-sheet-title">Способ оплаты</p>
            <button className="pay-sheet-btn" onClick={() => handlePay('yookassa')}>
              💳 Банковская карта / ЮMoney — {Math.round(price)} ₽
            </button>
            {hasStars && (
              <button className="pay-sheet-btn stars" onClick={() => handlePay('stars')}>
                ⭐ Telegram Stars — {selectedPlan.price_stars} Stars
              </button>
            )}
            <button className="pay-sheet-cancel" onClick={() => setShowPaySheet(false)}>
              Отмена
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
