import './NavItem.css'

const NavItem = ({ item, isActive, onClick }) => {
  return (
    <button
      className={`nav-item ${isActive ? 'active' : ''}`}
      onClick={onClick}
    >
      <div className="nav-icon">{item.icon}</div>
      <span className="nav-label">{item.label}</span>
    </button>
  )
}

export default NavItem
