import { useEffect, useRef } from 'react'
import { useLocation } from 'react-router-dom'
import './AnimatedBackground.css'

const AnimatedBackground = () => {
  const location = useLocation()
  const containerRef = useRef(null)
  const animationSpeedRef = useRef(1)

  useEffect(() => {
    animationSpeedRef.current = 3
    const timer = setTimeout(() => {
      animationSpeedRef.current = 1
    }, 800)

    if (containerRef.current) {
      containerRef.current.style.setProperty('--animation-speed', '3')
      setTimeout(() => {
        if (containerRef.current) {
          containerRef.current.style.setProperty('--animation-speed', '1')
        }
      }, 800)
    }

    return () => clearTimeout(timer)
  }, [location.pathname])

  return (
    <div className="animated-background" ref={containerRef}>
      <div className="gradient-blob blob-1"></div>
      <div className="gradient-blob blob-2"></div>
      <div className="gradient-blob blob-3"></div>
      <div className="gradient-blob blob-4"></div>
      <div className="gradient-blob blob-5"></div>
    </div>
  )
}

export default AnimatedBackground
