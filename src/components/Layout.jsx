import { useEffect } from 'react'
import { useLocation } from 'react-router-dom'
import BottomNav from './BottomNav/index'
import AnimatedBackground from './AnimatedBackground'
import './Layout.css'

const Layout = ({ children }) => {
  const location = useLocation()

  useEffect(() => {
    // Scroll to top when route changes
    const mainContent = document.querySelector('.main-content')
    if (mainContent) {
      mainContent.scrollTop = 0
    }
    window.scrollTo(0, 0)
  }, [location.pathname])

  return (
    <div className="layout">
      <AnimatedBackground />
      <main className="main-content">
        {children}
      </main>
      <BottomNav />
    </div>
  )
}

export default Layout
