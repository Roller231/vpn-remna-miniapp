import BottomNav from './BottomNav/index'
import './Layout.css'

const Layout = ({ children }) => {
  return (
    <div className="layout">
      <main className="main-content">
        {children}
      </main>
      <BottomNav />
    </div>
  )
}

export default Layout
