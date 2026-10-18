import { useParams } from 'react-router'

import MenuPage from './MenuPage'

interface Props {
  username: string
  isNew: boolean
  onLogout: () => void
}

/** The restaurant page for the URL's slug, keyed by it, so the tab, search and an open
 * sheet do not carry over to another restaurant, and its chat starts there afresh. */
function MenuRoute(props: Props) {
  const { slug = '' } = useParams()
  return <MenuPage key={slug} slug={slug} {...props} />
}

export default MenuRoute
