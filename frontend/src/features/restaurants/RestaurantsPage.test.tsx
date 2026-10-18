import { fireEvent, render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router'
import { describe, expect, test } from 'vitest'

import { mockFetch } from '../../test/fetchMock'
import { restaurants } from '../../test/restaurants'
import RestaurantsPage from './RestaurantsPage'

function renderPage() {
  render(
    <MemoryRouter>
      <RestaurantsPage />
    </MemoryRouter>,
  )
}

describe('RestaurantsPage', () => {
  test('every restaurant links to its own page', async () => {
    mockFetch(restaurants)
    renderPage()
    const dragon = await screen.findByRole('link', { name: /Golden Dragon/ })
    expect(dragon).toHaveAttribute('href', '/r/golden-dragon')
    expect(screen.getByRole('link', { name: /Corner Table/ })).toHaveAttribute(
      'href',
      '/r/corner-table',
    )
  })

  test('restaurants are listed one per row, each with its storefront sign', async () => {
    mockFetch(restaurants)
    const { container } = render(
      <MemoryRouter>
        <RestaurantsPage />
      </MemoryRouter>,
    )
    await screen.findByRole('link', { name: /Golden Dragon/ })
    const rows = screen.getAllByRole('listitem')
    expect(rows).toHaveLength(2)
    const signs = [...container.querySelectorAll('img')].map((img) => img.getAttribute('src'))
    expect(signs).toEqual([
      '/storefronts/corner-table-1440.webp',
      '/storefronts/golden-dragon-1440.webp',
    ])
  })

  test('placeholders show while the list loads, then the restaurants', async () => {
    mockFetch(restaurants)
    renderPage()
    expect(screen.getByRole('status', { name: 'Loading the restaurants' })).toBeInTheDocument()
    expect(await screen.findByRole('link', { name: /Golden Dragon/ })).toBeInTheDocument()
    expect(screen.queryByRole('status')).not.toBeInTheDocument()
  })

  test('a failed list shows Retry, which loads it again', async () => {
    mockFetch({
      'GET /api/restaurants': [
        { status: 503, body: { detail: 'Busy.' } },
        restaurants['GET /api/restaurants'],
      ],
    })
    renderPage()
    expect(await screen.findByRole('alert')).toHaveTextContent('Busy.')
    fireEvent.click(screen.getByRole('button', { name: 'Retry' }))
    expect(await screen.findByRole('link', { name: /Golden Dragon/ })).toBeInTheDocument()
  })

  test('an empty list says so', async () => {
    mockFetch({ 'GET /api/restaurants': { body: [] } })
    renderPage()
    expect(await screen.findByRole('alert')).toHaveTextContent('No restaurants are set up yet.')
  })
})
