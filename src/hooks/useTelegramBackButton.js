import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'

/**
 * Shows the Telegram native BackButton while the component is mounted.
 * Hides it on unmount. Pressing it calls navigate(-1) by default,
 * or a custom onBack callback if provided.
 */
export function useTelegramBackButton(onBack = null) {
  const navigate = useNavigate()

  useEffect(() => {
    const tg = window.Telegram?.WebApp
    if (!tg) return

    const handler = onBack ?? (() => navigate(-1))

    try { tg.BackButton.show() } catch {}
    tg.onEvent('backButtonClicked', handler)

    return () => {
      tg.offEvent('backButtonClicked', handler)
      try { tg.BackButton.hide() } catch {}
    }
  }, [navigate, onBack])
}
