import { NavLink, Outlet } from 'react-router'

import styles from './AppShell.module.css'

interface Props {
  username: string
  onLogout: () => void
}

const navClass = ({ isActive }: { isActive: boolean }) =>
  isActive ? `${styles.link} ${styles.active}` : styles.link

/** The header on every page after login, and the page below it. */
function AppShell({ username, onLogout }: Props) {
  return (
    <div className={styles.shell}>
      <header className={styles.header}>
        <div className={styles.brand}>
          <img className={styles.logo} src="/foodics-logo.svg" alt="Foodics" />
          <span className={styles.name}>Foodics Order Assistant</span>
        </div>
        <nav className={styles.nav} aria-label="Main">
          <NavLink to="/" end className={navClass}>
            Restaurants
          </NavLink>
          <NavLink to="/orders" className={navClass}>
            Orders
          </NavLink>
        </nav>
        <div className={styles.user}>
          <span className={styles.hello}>Hi, {username}</span>
          <button className={styles.logout} type="button" onClick={onLogout}>
            Log out
          </button>
        </div>
      </header>
      <div className={styles.page}>
        <Outlet />
      </div>
    </div>
  )
}

export default AppShell
