'use client'

/**
 * Browser MediaRecorder MIME type detection.
 * Prefers audio/webm;codecs=opus (Chrome/Firefox), falls back to audio/mp4 (iOS Safari).
 */

const PREFERRED_TYPES = [
  'audio/webm;codecs=opus',
  'audio/webm',
  'audio/ogg;codecs=opus',
  'audio/ogg',
  'audio/mp4',
]

export function getSupportedMimeType(): string | undefined {
  if (typeof window === 'undefined' || !window.MediaRecorder) return undefined
  for (const type of PREFERRED_TYPES) {
    if (MediaRecorder.isTypeSupported(type)) return type
  }
  return undefined
}

export function isMediaRecorderSupported(): boolean {
  return typeof window !== 'undefined' && typeof window.MediaRecorder !== 'undefined'
}

export function isMicrophoneAvailable(): boolean {
  return (
    typeof window !== 'undefined' &&
    typeof navigator !== 'undefined' &&
    typeof navigator.mediaDevices !== 'undefined' &&
    typeof navigator.mediaDevices.getUserMedia === 'function'
  )
}

export function formatDuration(seconds: number): string {
  const m = Math.floor(seconds / 60)
  const s = Math.floor(seconds % 60)
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
}
