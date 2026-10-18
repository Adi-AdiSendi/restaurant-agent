import { act, fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, test, vi } from 'vitest'

import MicButton from './MicButton'
import type { Recognition } from './speech'
import { MIC_BLOCKED } from './useVoice'

/** A scripted SpeechRecognition: the test plays what the browser would say. */
class FakeRecognition {
  static last: FakeRecognition | null = null
  lang = ''
  interimResults = false
  continuous = false
  onresult: Recognition['onresult'] = null
  onerror: Recognition['onerror'] = null
  onend: Recognition['onend'] = null
  start = vi.fn()
  stop = vi.fn()
  constructor() {
    FakeRecognition.last = this
  }
  say(transcript: string, isFinal: boolean) {
    this.onresult?.({ resultIndex: 0, results: [{ isFinal, 0: { transcript } }] })
  }
}

function speak(auto = false) {
  localStorage.clear()
  vi.stubGlobal('SpeechRecognition', FakeRecognition)
  const onText = vi.fn()
  const onSend = vi.fn()
  render(<MicButton disabled={false} onText={onText} onSend={onSend} />)
  if (auto) fireEvent.click(screen.getByRole('button', { name: 'Auto' }))
  fireEvent.click(screen.getByRole('button', { name: 'Speak' }))
  const rec = FakeRecognition.last as FakeRecognition
  return { onText, onSend, rec }
}

describe('voice input', () => {
  test('without speech recognition or recording, there is no mic', () => {
    render(<MicButton disabled={false} onText={vi.fn()} onSend={vi.fn()} />)
    expect(screen.queryByRole('button', { name: 'Speak' })).not.toBeInTheDocument()
  })

  test('what the guest says goes into the box, live, in English', () => {
    const { onText, onSend, rec } = speak()
    expect(rec.lang).toBe('en-US')
    expect(rec.start).toHaveBeenCalled()
    expect(screen.getByRole('button', { name: 'Stop listening' })).toHaveAttribute(
      'aria-pressed',
      'true',
    )
    act(() => rec.say('two oat', false))
    act(() => rec.say('two oat lattes please ', true))
    expect(onText).toHaveBeenNthCalledWith(1, 'two oat')
    expect(onText).toHaveBeenLastCalledWith('two oat lattes please')
    expect(onSend).not.toHaveBeenCalled()
    act(() => rec.onend?.())
    expect(screen.getByRole('button', { name: 'Speak' })).toBeInTheDocument()
  })

  test('Auto sends the final words at once; off, they only fill the box', () => {
    const { onText, onSend, rec } = speak(true)
    expect(screen.getByRole('button', { name: 'Auto' })).toHaveAttribute('aria-pressed', 'true')
    act(() => rec.say('two oat', false))
    act(() => rec.say('two oat lattes', true))
    expect(onText).toHaveBeenCalledWith('two oat')
    expect(onSend).toHaveBeenCalledWith('two oat lattes')
  })

  test('a blocked microphone says how to fix it', () => {
    const { rec } = speak()
    act(() => rec.onerror?.({ error: 'not-allowed' }))
    expect(screen.getByRole('alert')).toHaveTextContent(MIC_BLOCKED)
  })
})
