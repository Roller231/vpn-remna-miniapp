import { useNavigate, useLocation } from 'react-router-dom'
import { useState, useEffect, useRef } from 'react'
import NavItem from './NavItem'
import { navItems } from './navConfig'
import './BottomNav.css'

const BottomNav = () => {
  const navigate = useNavigate()
  const location = useLocation()
  const navRef = useRef(null)
  const [indicatorStyle, setIndicatorStyle] = useState({})

  const activeIndex = navItems.findIndex(item => item.path === location.pathname)

  useEffect(() => {
    const updateIndicator = () => {
      if (navRef.current && activeIndex !== -1) {
        const navContainer = navRef.current
        const buttons = navContainer.querySelectorAll('.nav-item')
        const activeButton = buttons[activeIndex]

        if (activeButton) {
          const containerRect = navContainer.getBoundingClientRect()
          const buttonRect = activeButton.getBoundingClientRect()

          const hInset = 4
          const left = buttonRect.left - containerRect.left + hInset
          const width = Math.max(0, buttonRect.width - hInset * 2)

          setIndicatorStyle({ left: `${left}px`, width: `${width}px` })
        }

        const navEl = navContainer
        if (navEl) {
          const height = Math.ceil(navEl.getBoundingClientRect().height)
          const extra = 20
          document.documentElement.style.setProperty('--bottom-nav-safe', `${height + extra}px`)
        }
      }
    }

    updateIndicator()
    window.addEventListener('resize', updateIndicator)
    window.addEventListener('orientationchange', updateIndicator)
    return () => {
      window.removeEventListener('resize', updateIndicator)
      window.removeEventListener('orientationchange', updateIndicator)
    }
  }, [activeIndex])

  const handleNavigation = (path) => {
    navigate(path)
  }

  return (
    <nav className="bottom-nav">
      <div className="nav-container" ref={navRef}>
        <div 
          className="nav-indicator" 
          style={indicatorStyle}
        ></div>
        {navItems.map((item, index) => (
          <NavItem
            key={item.path}
            item={item}
            isActive={activeIndex === index}
            onClick={() => handleNavigation(item.path)}
          />
        ))}
      </div>
    </nav>
  )
}

export default BottomNav
