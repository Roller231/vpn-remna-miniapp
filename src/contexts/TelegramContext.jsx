import { createContext, useContext, useEffect, useState } from 'react'

const TelegramContext = createContext({})

export const TelegramProvider = ({ children }) => {
  const [webApp, setWebApp] = useState(null)
  const [user, setUser] = useState(null)

  useEffect(() => {
    const tg = window.Telegram?.WebApp

    if (tg) {
      tg.ready()
      tg.expand()
      // Prevent accidental app dismiss by swipe and ask confirm on close
      if (typeof tg.disableVerticalSwipes === 'function') tg.disableVerticalSwipes()
      if (typeof tg.enableClosingConfirmation === 'function') tg.enableClosingConfirmation()
      setWebApp(tg)
      
      if (tg.initDataUnsafe?.user) {
        setUser(tg.initDataUnsafe.user)
      }

      tg.setHeaderColor('#1a3a4a')
      tg.setBackgroundColor('#0d1f2d')
    }
  }, [])

  const value = {
    webApp,
    user,
    unsafeData: webApp?.initDataUnsafe,
  }

  return (
    <TelegramContext.Provider value={value}>
      {children}
    </TelegramContext.Provider>
  )
}

export const useTelegram = () => {
  const context = useContext(TelegramContext)
  if (context === undefined) {
    throw new Error('useTelegram must be used within TelegramProvider')
  }
  return context
}
