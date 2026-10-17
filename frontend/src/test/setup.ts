import '@testing-library/jest-dom/vitest'
import { cleanup } from '@testing-library/react'
import { afterEach, vi } from 'vitest'

// Vitest runs without globals, so Testing Library does not clean up on its own.
afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
})
