import { useState } from 'react'

import styles from './DishPhoto.module.css'

interface Props {
  /** `<restaurant>/<name>` from the database, or null for the icon. */
  photo: string | null
  /** Shown when there is no photo, or it fails to load. */
  icon: string
  /** `card` fills the width at 4:3; `thumb` is a small square for lists. */
  size?: 'card' | 'thumb'
}

/** A dish or cover photo (ADR 0024). Decorative: the name next to it says what it is. */
function DishPhoto({ photo, icon, size = 'card' }: Props) {
  const [failed, setFailed] = useState(false)
  const className = size === 'card' ? styles.card : styles.thumb
  if (!photo || failed) {
    return (
      <div className={`${className} ${styles.icon}`} aria-hidden="true">
        {icon}
      </div>
    )
  }
  const base = `/menu/${photo}`
  return (
    <img
      className={className}
      src={`${base}-${size === 'card' ? 640 : 320}.webp`}
      srcSet={`${base}-320.webp 320w, ${base}-640.webp 640w`}
      sizes={size === 'card' ? '(max-width: 600px) 100vw, 320px' : '64px'}
      alt=""
      loading="lazy"
      decoding="async"
      onError={() => setFailed(true)}
    />
  )
}

export default DishPhoto
