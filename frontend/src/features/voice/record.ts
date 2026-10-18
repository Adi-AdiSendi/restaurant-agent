// Records a short clip for the server to transcribe, where the browser cannot recognize
// speech itself (Firefox, Safari). Ported from Aviation-Services/site/concierge/record.mjs.

const MAX_MS = 20_000 // a forgotten mic stops by itself

export const isRecordingSupported = () =>
  typeof MediaRecorder !== 'undefined' && !!navigator.mediaDevices?.getUserMedia

function mimeType(): string {
  const types = ['audio/webm;codecs=opus', 'audio/webm', 'audio/ogg;codecs=opus', 'audio/mp4']
  return types.find((t) => MediaRecorder.isTypeSupported(t)) ?? ''
}

export interface Recorder {
  start: () => Promise<void>
  stop: () => void
}

/** One clip: `onStop` gets the audio; `onError` a denied or missing microphone. */
export function createRecorder(onStop: (audio: Blob) => void, onError: () => void): Recorder {
  let recorder: MediaRecorder | null = null
  let stream: MediaStream | null = null
  let timer: ReturnType<typeof setTimeout> | undefined
  const chunks: Blob[] = []
  const release = () => {
    stream?.getTracks().forEach((track) => track.stop())
    stream = null
  }

  const self: Recorder = {
    async start() {
      try {
        stream = await navigator.mediaDevices.getUserMedia({ audio: true })
        const type = mimeType()
        recorder = type ? new MediaRecorder(stream, { mimeType: type }) : new MediaRecorder(stream)
      } catch {
        release()
        onError()
        return
      }
      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) chunks.push(event.data)
      }
      recorder.onstop = () => {
        clearTimeout(timer)
        release()
        onStop(new Blob(chunks, { type: recorder?.mimeType || 'audio/webm' }))
        chunks.length = 0
      }
      recorder.start()
      timer = setTimeout(() => self.stop(), MAX_MS)
    },
    stop() {
      clearTimeout(timer)
      if (recorder && recorder.state !== 'inactive') recorder.stop()
      else release()
    },
  }
  return self
}
