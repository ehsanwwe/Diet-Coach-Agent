'use client'

import { useEffect, useRef, useState } from 'react'
import { Play, Pause, RotateCcw } from 'lucide-react'
import { cn } from '@/lib/cn'
import { formatDuration } from '@/lib/media'

interface Props {
  blob: Blob
  labelPlay: string
  labelPause: string
  labelReset: string
}

export default function AudioPreview({ blob, labelPlay, labelPause, labelReset }: Props) {
  const audioRef = useRef<HTMLAudioElement | null>(null)
  const urlRef = useRef<string | null>(null)
  const [playing, setPlaying] = useState(false)
  const [currentTime, setCurrentTime] = useState(0)
  const [duration, setDuration] = useState(0)

  useEffect(() => {
    const url = URL.createObjectURL(blob)
    urlRef.current = url
    const audio = new Audio(url)
    audioRef.current = audio

    audio.onloadedmetadata = () => {
      setDuration(audio.duration && isFinite(audio.duration) ? audio.duration : 0)
    }
    audio.ontimeupdate = () => setCurrentTime(audio.currentTime)
    audio.onended = () => {
      setPlaying(false)
      setCurrentTime(0)
    }

    return () => {
      audio.pause()
      URL.revokeObjectURL(url)
    }
  }, [blob])

  const toggle = () => {
    const audio = audioRef.current
    if (!audio) return
    if (playing) {
      audio.pause()
      setPlaying(false)
    } else {
      audio.play().then(() => setPlaying(true)).catch(() => setPlaying(false))
    }
  }

  const restart = () => {
    const audio = audioRef.current
    if (!audio) return
    audio.currentTime = 0
    setCurrentTime(0)
    if (playing) {
      audio.pause()
      setPlaying(false)
    }
  }

  const progress = duration > 0 ? (currentTime / duration) * 100 : 0

  return (
    <div className="flex items-center gap-3 rounded-2xl bg-surface border border-line px-4 py-3">
      <button
        type="button"
        onClick={toggle}
        aria-label={playing ? labelPause : labelPlay}
        className={cn(
          'flex-shrink-0 w-9 h-9 rounded-full flex items-center justify-center transition-colors',
          'bg-brand text-white hover:bg-brand/90',
        )}
      >
        {playing ? <Pause size={16} /> : <Play size={16} />}
      </button>

      <div className="flex-1 min-w-0">
        <div className="w-full h-1.5 rounded-full bg-line overflow-hidden">
          <div
            className="h-full rounded-full bg-brand transition-all duration-200"
            style={{ width: `${progress}%` }}
          />
        </div>
        <p className="text-xs text-ink-3 mt-1">
          {formatDuration(currentTime)}
          {duration > 0 && ` / ${formatDuration(duration)}`}
        </p>
      </div>

      <button
        type="button"
        onClick={restart}
        aria-label={labelReset}
        className="flex-shrink-0 w-7 h-7 rounded-full flex items-center justify-center text-ink-3 hover:text-ink transition-colors"
      >
        <RotateCcw size={14} />
      </button>
    </div>
  )
}
