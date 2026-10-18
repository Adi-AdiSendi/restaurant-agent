import { useParams } from 'react-router'

import OrderView from './OrderView'

/** The order in the URL, keyed by its id, so another order starts from a clean state. */
function OrderPage() {
  const { id = '' } = useParams()
  return <OrderView key={id} id={Number(id)} />
}

export default OrderPage
