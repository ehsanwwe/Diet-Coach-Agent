'use client'

import { useCallback, useEffect, useRef, useState } from 'react'
import { getSupportedMimeType, isMediaRecorderSupported, isMicrophoneAvailable } from '@/lib/media'

export type RecorderState =
  | 'idle'
  | 'requesting'
  | 'recording'
  | 'stopped'
  | 'error'

export interface RecorderError {
  kind: 'unsupported' | 'permission_denied' | 'no_microphone' | 'unknown'
  message: string
}

export interface UseAudioRecorderReturn {
  state: RecorderState
  error: RecorderError | null
  elapsedSeconds: number
  audioBlob: Blob | null
  mimeType: string
  analyserNode: AnalyserNode | null
  startRecording: () => Promise<void>
  stopRecording: () => void
  cancelRecording: () => void
  reset: () => void
}

export function useAudioRecorder(): UseAudioRecorderReturn {
  const [state, setState] = useState<RecorderState>('idle')
  const [error, setError] = useState<RecorderError | null>(null)
  const [elapsedSeconds, setElapsedSeconds] = useState(0)
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null)
  const [analyserNode, setAnalyserNode] = useState<AnalyserNode | null>(null)

  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const streamRef = useRef<MediaStream | null>(null)
  const audioCtxRef = useRef<AudioContext | null>(null)
  const chunksRef = useRef<Blob[]>([])
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const mimeTypeRef = useRef<string>('audio/webm')

  const cleanupStream = useCallback(() => {
    if (timerRef.current) {
      clearInterval(timerRef.current)
      timerRef.current = null
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((t) => t.stop())
      streamRef.current = null
    }
    if (audioCtxRef.current) {
      audioCtxRef.current.close().catch(() => {})
      audioCtxRef.current = null
    }
    setAnalyserNode(null)
  }, [])

  const reset = useCallback(() => {
    cleanupStream()
    chunksRef.current = []
    setState('idle')
    setError(null)
    setElapsedSeconds(0)
    setAudioBlob(null)
  }, [cleanupStream])

  const startRecording = useCallback(async () => {
    if (!isMediaRecorderSupported()) {
      setError({ kind: 'unsupported', message: 'MediaRecorder not supported in this browser' })
      setState('error')
      return
    }
    if (!isMicrophoneAvailable()) {
      setError({ kind: 'no_microphone', message: 'No microphone available' })
      setState('error')
      return
    }

    setState('requesting')
    setError(null)

    let stream: MediaStream
    try {
      stream = await navigator.mediaDevices.getUserMedia({ audio: true })
    } catch (err) {
      const isDenied =
        err instanceof DOMException &&
        (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError')
      setError(
        isDenied
          ? { kind: 'permission_denied', message: 'Microphone permission denied' }
          : { kind: 'unknown', message: 'Failed to access microphone' },
      )
      setState('error')
      return
    }

    streamRef.current = stream
    chunksRef.current = []

    // Web Audio AnalyserNode for waveform
    const audioCtx = new AudioContext()
    audioCtxRef.current = audioCtx
    const source = audioCtx.createMediaStreamSource(stream)
    const analyser = audioCtx.createAnalyser()
    analyser.fftSize = 256
    source.connect(analyser)
    setAnalyserNode(analyser)

    const mimeType = getSupportedMimeType() ?? 'audio/webm'
    mimeTypeRef.current = mimeType

    const recorder = new MediaRecorder(stream, { mimeType })
    mediaRecorderRef.current = recorder

    recorder.ondataavailable = (e) => {
      if (e.data && e.data.size > 0) {
        chunksRef.current.push(e.data)
      }
    }

    recorder.onstop = () => {
      const blob = new Blob(chunksRef.current, { type: mimeType })
      setAudioBlob(blob)
      cleanupStream()
      setState('stopped')
    }

    recorder.start(100)
    setState('recording')
    setElapsedSeconds(0)

    timerRef.current = setInterval(() => {
      setElapsedSeconds((s) => s + 1)
    }, 1000)
  }, [cleanupStream])

  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop()
    }
    if (timerRef.current) {
      clearInterval(timerRef.current)
      timerRef.current = null
    }
  }, [])

  const cancelRecording = useCallback(() => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.ondataavailable = null
      mediaRecorderRef.current.onstop = null
      mediaRecorderRef.current.stop()
    }
    cleanupStream()
    chunksRef.current = []
    setState('idle')
    setAudioBlob(null)
    setElapsedSeconds(0)
  }, [cleanupStream])

  // Clean up on unmount
  useEffect(() => {
    return () => {
      cleanupStream()
    }
  }, [cleanupStream])

  return {
    state,
    error,
    elapsedSeconds,
    audioBlob,
    mimeType: mimeTypeRef.current,
    analyserNode,
    startRecording,
    stopRecording,
    cancelRecording,
    reset,
  }
}
