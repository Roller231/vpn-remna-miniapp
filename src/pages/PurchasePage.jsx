import { useState, useMemo, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useApi } from '../contexts/ApiContext'
import { useTelegram } from '../contexts/TelegramContext'
import { purchaseWithYookassa, createStarsInvoice, purchaseFromBalance } from '../api/client'
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
  const { webApp } = useTelegram()

  const allPlans = useMemo(() => catalog.flatMap(p => p.plans || []), [catalog])

  const deviceCounts = useMemo(() =>
    [...new Set(allPlans.map(p => p.devices))].sort((a, b) => a - b), [allPlans])

  const durations = useMemo(() =>
    [...new Set(allPlans.map(p => p.duration_days))].sort((a, b) => a - b), [allPlans])

  const [deviceIdx, setDeviceIdx]       = useState(0)
  const [selectedDays, setSelectedDays] = useState(null)
  const [paying, setPaying]             = useState(false)
  const [payError, setPayError]         = useState(null)
  const [showPaySheet, setShowPaySheet] = useState(false)
  const [payMethod, setPayMethod]       = useState('yookassa')
  const [showMethodPicker, setShowMethodPicker] = useState(false)

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

  const endDate = useMemo(() => {
    if (!selectedPlan) return ''
    const d = new Date()
    d.setDate(d.getDate() + selectedPlan.duration_days)
    return d.toLocaleDateString('ru-RU', { day: 'numeric', month: 'long', year: 'numeric' })
  }, [selectedPlan])

  const payMethods = useMemo(() => [
    { id: 'yookassa', label: 'ЮMoney / Банковская карта', icon: '💳' },
    ...(hasStars ? [{ id: 'stars', label: `Telegram Stars — ${selectedPlan?.price_stars} ★`, icon: '⭐' }] : []),
    { id: 'balance', label: 'Баланс приложения', icon: '👛' },
  ], [hasStars, selectedPlan])

  const currentMethod = payMethods.find(m => m.id === payMethod) ?? payMethods[0]

  const handlePay = async (method = 'yookassa') => {
    if (!selectedPlan) return
    setPaying(true); setPayError(null); setShowPaySheet(false)
    try {
      if (method === 'yookassa') {
        const res = await purchaseWithYookassa(selectedPlan.id, window.location.href)
        if (res.payment_url) window.location.href = res.payment_url
      } else if (method === 'balance') {
        await purchaseFromBalance(selectedPlan.id)
        navigate(-1)
      } else if (method === 'stars') {
        const { invoice_url } = await createStarsInvoice(selectedPlan.id)
        window.Telegram?.WebApp?.openInvoice?.(invoice_url, (invoiceStatus) => {
          if (invoiceStatus === 'paid') setPayError(null)
          else if (invoiceStatus === 'failed') setPayError('Оплата звёздами не прошла')
        })
      }
    } catch (e) { setPayError(e.message) }
    finally { setPaying(false) }
  }

  const handlePayButton = () => {
    if (!selectedPlan) return
    setShowPaySheet(true)
  }

  // THUMB_PX = 26  →  THUMB_R = 13
  // Unified geometry: thumb center and dots share the same formula.
  const THUMB_PX = 26
  const THUMB_R  = THUMB_PX / 2   // 13
  const PILL_H   = 36             // visual pill height

  // Center position of current step (thumb/dot center)
  const centerPos = deviceCounts.length <= 1
    ? '50%'
    : `calc(${deviceIdx} / ${deviceCounts.length - 1} * (100% - ${THUMB_PX}px) + ${THUMB_R}px)`

  // Fill ends slightly past center (by THUMB_R) so its rounded cap sits under thumb edge.
  // Ensure a minimum width = PILL_H to render a perfect circle at the first step.
  const sliderFill = deviceCounts.length <= 1
    ? '100%'
    : `max(calc(${PILL_H}px - 15px), calc(${centerPos} + ${THUMB_R}px))`

  function dotLeft(i, n) {
    if (n <= 1) return '50%'
    return `calc(${i} / ${n - 1} * (100% - ${THUMB_PX}px) + ${THUMB_R}px)`
  }

  return (
    <div className="pp-root">
      <AnimatedBackground />

      <div className="pp-scroll">
        {/* Header back removed — handled by Telegram BackButton */}

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

            {/* Draggable slider */}
            <div className="pp-slider-wrap">
              {/* Visual pill track */}
              <div className="pp-slider-track">
                <div className="pp-slider-fill" style={{ width: sliderFill }} />
                {deviceCounts.map((_, i) => (
                  <span
                    key={i}
                    className={`pp-slider-dot${i === deviceIdx ? ' active' : ''}`}
                    style={{ left: dotLeft(i, deviceCounts.length) }}
                  />
                ))}
              </div>
              {/* Native range — transparent track, styled thumb, handles dragging */}
              <input
                type="range"
                className="pp-range"
                min={0}
                max={Math.max(0, deviceCounts.length - 1)}
                step={1}
                value={deviceIdx}
                onChange={e => { setDeviceIdx(Number(e.target.value)); setSelectedDays(null) }}
              />
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
        <div className="pp-overlay" onClick={() => { setShowPaySheet(false); setShowMethodPicker(false) }}>
          <div className="pp-sheet" onClick={e => e.stopPropagation()}>

            {!showMethodPicker ? (<>
              {/* Header */}
              <div className="pp-sheet-header">
                <h2 className="pp-sheet-heading">Подтверждение<br/>оплаты</h2>
                <button className="pp-sheet-x" onClick={() => setShowPaySheet(false)}>✕</button>
              </div>

              {/* Info card */}
              <div className="pp-sheet-info">
                <div className="pp-sheet-info-row">
                  Подписка до {endDate}, {DURATION_LABELS[activeDays] ?? `${activeDays} дн.`}
                </div>
                <div className="pp-sheet-info-sep" />
                <div className="pp-sheet-info-row">
                  Количество устройств: {selectedDevices}
                </div>
              </div>

              {/* Selected method row */}
              <div className="pp-sheet-method-row">
                <span className="pp-sheet-method-icon">{currentMethod?.icon}</span>
                <span className="pp-sheet-method-label">{currentMethod?.label}</span>
                <button className="pp-sheet-method-dots" onClick={() => setShowMethodPicker(true)}>
                  •••
                </button>
              </div>

              {/* Pay button */}
              <button
                className="pp-sheet-pay"
                onClick={() => handlePay(payMethod)}
                disabled={paying}
              >
                {paying ? 'Оплата…' : (
                  payMethod === 'stars'
                    ? `Оплатить ${selectedPlan.price_stars} ★`
                    : `Оплатить ${Math.round(price)} ₽`
                )}
              </button>
            </>) : (<>
              {/* Method picker sub-screen */}
              <div className="pp-sheet-header">
                <h2 className="pp-sheet-heading">Изменить способ<br/>оплаты</h2>
                <button className="pp-sheet-x" onClick={() => setShowMethodPicker(false)}>✕</button>
              </div>

              {payMethods.map(m => (
                <button
                  key={m.id}
                  className={`pp-sheet-method-item${payMethod === m.id ? ' sel' : ''}`}
                  onClick={() => { setPayMethod(m.id); setShowMethodPicker(false) }}
                >
                  <span className="pp-sheet-method-icon">{m.icon}</span>
                  <span className="pp-sheet-method-label">{m.label}</span>
                  {payMethod === m.id && <span className="pp-sheet-method-check">✓</span>}
                </button>
              ))}
            </>)}

          </div>
        </div>
      )}
    </div>
  )
}
