import { NavLink } from 'react-router-dom'

const navItems = [
  { to: '/', icon: '◈', label: 'Обзор', end: true },
  { to: '/topics', icon: '◉', label: 'Темы' },
  { to: '/trends', icon: '◈', label: 'Тренды' },
  { to: '/sentiment', icon: '◎', label: 'Тональность' },
  { to: '/documents', icon: '▤', label: 'Документы' },
  { to: '/sources', icon: '◌', label: 'Источники' },
]

export default function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <NavLink to="/" className="logo-mark">
          <div className="logo-icon">
            <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
              <path d="M9 2L16 6V12L9 16L2 12V6L9 2Z" stroke="white" strokeWidth="1.5" fill="none"/>
              <path d="M9 6L12 8V12L9 14L6 12V8L9 6Z" fill="white" opacity="0.6"/>
            </svg>
          </div>
          <div>
            <span className="logo-text">TrendScope</span>
            <span className="logo-sub">Казахстан · Аналитика</span>
          </div>
        </NavLink>
      </div>

      <nav className="sidebar-nav">
        <div className="nav-section-label">Аналитика</div>
        {navItems.map(({ to, icon, label, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            className={({ isActive }) => `nav-item${isActive ? ' active' : ''}`}
          >
            <span className="nav-icon">{icon}</span>
            {label}
          </NavLink>
        ))}
      </nav>

      <div className="sidebar-footer">
        <div className="sidebar-status">
          <span className="status-dot" />
          Backend активен
        </div>
      </div>
    </aside>
  )
}
