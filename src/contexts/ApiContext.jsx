import { createContext, useContext, useEffect, useState, useCallback } from 'react'
import { authTelegram, setToken, getToken, fetchMe, fetchCatalog, fetchMySubscriptions } from '../api/client'

const ApiContext = createContext({})

export const ApiProvider = ({ children, webApp }) => {
  const [authState, setAuthState] = useState('idle') // idle | loading | ok | error
  const [apiUser, setApiUser]         = useState(null)
  const [subscription, setSubscription] = useState(null)
  const [catalog, setCatalog]         = useState([])
  const [catalogLoading, setCatalogLoading] = useState(true)
  const [error, setError]             = useState(null)

  // Catalog is public — load immediately without auth
  useEffect(() => {
    setCatalogLoading(true)
    fetchCatalog()
      .then(data => setCatalog(data || []))
      .catch(e => console.error('catalog fetch error', e))
      .finally(() => setCatalogLoading(false))
  }, [])

  const loadUserData = useCallback(async () => {
    try {
      const [me, subs] = await Promise.allSettled([
        fetchMe(),
        fetchMySubscriptions(),
      ])
      if (me.status === 'fulfilled')   setApiUser(me.value)
      if (subs.status === 'fulfilled') {
        const active = subs.value?.find(s => ['active', 'trial'].includes(s.status))
        setSubscription(active || null)
      }
    } catch (e) {
      console.error('loadUserData error', e)
    }
  }, [])

  useEffect(() => {
    if (!webApp) return
    const initData = webApp.initData
    if (!initData) {
      if (getToken()) { setAuthState('ok'); loadUserData() }
      else { setAuthState('error'); setError('No initData') }
      return
    }
    setAuthState('loading')
    authTelegram(initData)
      .then(res => { setToken(res.access_token); setAuthState('ok'); loadUserData() })
      .catch(e  => { setAuthState('error'); setError(e.message) })
  }, [webApp])

  const refresh = useCallback(async () => {
    const [, cat] = await Promise.allSettled([loadUserData(), fetchCatalog()])
    if (cat.status === 'fulfilled') setCatalog(cat.value || [])
  }, [loadUserData])

  return (
    <ApiContext.Provider value={{ authState, apiUser, subscription, catalog, catalogLoading, error, refresh }}>
      {children}
    </ApiContext.Provider>
  )
}

export const useApi = () => useContext(ApiContext)
