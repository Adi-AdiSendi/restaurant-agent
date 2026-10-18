import { useState } from 'react'

import styles from './Storefront.module.css'

/** The restaurant's sign as a 3:1 banner (supplied by the project owner, never cropped).
 * Decorative: the name is also in text. If it fails to load, an accent band shows. */
function Storefront({ slug }: { slug: string }) {
  const [failed, setFailed] = useState(false)
  if (failed) return <div className={styles.signFallback} aria-hidden="true" />
  const base = `/storefronts/${slug}`
  return (
    <img
      className={styles.sign}
      src={`${base}-1440.webp`}
      srcSet={`${base}-720.webp 720w, ${base}-1440.webp 1440w`}
      sizes="(max-width: 860px) 100vw, 820px"
      alt=""
      loading="lazy"
      decoding="async"
      onError={() => setFailed(true)}
    />
  )
}

export default Storefront
