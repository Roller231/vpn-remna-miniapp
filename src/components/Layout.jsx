import BottomNav from './BottomNav/index'
import AnimatedBackground from './AnimatedBackground'
import './Layout.css'

const Layout = ({ children }) => {
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
