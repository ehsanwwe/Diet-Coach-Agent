'use client'

import { Mic, Square, X, Send, AlertCircle } from 'lucide-react'
import { cn } from '@/lib/cn'
import { formatDuration, isMediaRecorderSupported } from '@/lib/media'
import { useAudioRecorder } from '@/hooks/useAudioRecorder'
import AudioWaveform from './AudioWaveform'
import AudioPreview from './AudioPreview'

interface AudioDict {
  startRecording: string
  stopRecording: string
  cancelRecording: string
  sendAudio: string
  recording: string
  uploading: string
  permissionDenied: string
  unsupportedBrowser: string
  noMicrophone: string
  audioPreview: string
  recordingDuration: string
  uploadFailed: string
  labelPlay: string
  labelPause: string
  labelReset: string
}

interface Props {
  dict: AudioDict
  onSend: (blob: Blob, mimeType: string, durationSeconds: number) => Promise<void>
  isUploading: boolean
  uploadError: string | null
  disabled?: boolean
}

export default function AudioRecorder({
  dict,
  onSend,
  isUploading,
  uploadError,
  disabled = false,
}: Props) {
  const {
    state,
    error,
    elapsedSeconds,
    audioBlob,
    mimeType,
    analyserNode,
    startRecording,
    stopRecording,
    cancelRecording,
    reset,
  } = useAudioRecorder()

  if (!isMediaRecorderSupported()) {
    return (
      <div className="flex items-center gap-2 rounded-2xl bg-surface border border-line px-4 py-3 text-sm text-ink-2">
        <AlertCircle size={16} className="flex-shrink-0 text-warning" />
        <span>{dict.unsupportedBrowser}</span>
      </div>
    )
  }

  if (error) {
    const msg =
      error.kind === 'permission_denied'
        ? dict.permissionDenied
        : error.kind === 'no_microphone'
          ? dict.noMicrophone
          : dict.unsupportedBrowser

    return (
      <div className="flex items-center justify-between rounded-2xl bg-surface border border-line px-4 py-3 gap-2">
        <div className="flex items-center gap-2 text-sm text-error">
          <AlertCircle size={16} className="flex-shrink-0" />
          <span>{msg}</span>
        </div>
        <button
          type="button"
          onClick={reset}
          className="text-xs text-brand hover:underline flex-shrink-0"
        >
          {dict.cancelRecording}
        </button>
      </div>
    )
  }

  if (state === 'stopped' && audioBlob) {
    return (
      <div className="space-y-2">
        <p className="text-xs text-ink-3 px-1">{dict.audioPreview}</p>
        <AudioPreview
          blob={audioBlob}
          labelPlay={dict.labelPlay}
          labelPause={dict.labelPause}
          labelReset={dict.labelReset}
        />
        {uploadError && (
          <p className="text-xs text-error px-1">{dict.uploadFailed}</p>
        )}
        <div className="flex gap-2">
          <button
            type="button"
            onClick={cancelRecording}
            disabled={isUploading}
            className={cn(
              'flex-1 py-2.5 rounded-2xl border border-line text-sm text-ink-2 flex items-center justify-center gap-1.5 transition-colors',
              isUploading ? 'opacity-50 cursor-not-allowed' : 'hover:bg-surface',
            )}
          >
            <X size={14} />
            {dict.cancelRecording}
          </button>
          <button
            type="button"
            disabled={isUploading}
            onClick={async () => {
              await onSend(audioBlob, mimeType, elapsedSeconds)
              reset()
            }}
            className={cn(
              'flex-1 py-2.5 rounded-2xl text-sm font-medium flex items-center justify-center gap-1.5 transition-colors',
              isUploading
                ? 'bg-line text-ink-3 cursor-not-allowed'
                : 'bg-brand text-white hover:bg-brand/90',
            )}
          >
            <Send size={14} />
            {isUploading ? dict.uploading : dict.sendAudio}
          </button>
        </div>
      </div>
    )
  }

  if (state === 'recording') {
    return (
      <div className="space-y-2">
        <div className="flex items-center justify-between px-1">
          <span className="text-xs text-brand font-medium flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-error animate-pulse" />
            {dict.recording}
          </span>
          <span className="text-xs text-ink-3 tabular-nums">
            {formatDuration(elapsedSeconds)}
          </span>
        </div>
        <AudioWaveform analyserNode={analyserNode} isActive />
        <div className="flex gap-2">
          <button
            type="button"
            onClick={cancelRecording}
            className="flex-1 py-2.5 rounded-2xl border border-line text-sm text-ink-2 flex items-center justify-center gap-1.5 hover:bg-surface transition-colors"
          >
            <X size={14} />
            {dict.cancelRecording}
          </button>
          <button
            type="button"
            onClick={stopRecording}
            className="flex-1 py-2.5 rounded-2xl bg-error/10 text-error text-sm font-medium flex items-center justify-center gap-1.5 hover:bg-error/20 transition-colors"
          >
            <Square size={14} />
            {dict.stopRecording}
          </button>
        </div>
      </div>
    )
  }

  // idle / requesting
  return (
    <button
      type="button"
      onClick={startRecording}
      disabled={disabled || state === 'requesting'}
      className={cn(
        'w-full py-2.5 rounded-2xl border border-dashed text-sm flex items-center justify-center gap-2 transition-colors',
        disabled || state === 'requesting'
          ? 'border-line text-ink-3 cursor-not-allowed'
          : 'border-brand/40 text-brand hover:bg-brand/5',
      )}
    >
      <Mic size={16} />
      {state === 'requesting' ? '...' : dict.startRecording}
    </button>
  )
}
