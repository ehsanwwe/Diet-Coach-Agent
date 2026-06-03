'use client'

import { useEffect, useRef } from 'react'

interface Props {
  analyserNode: AnalyserNode | null
  isActive: boolean
}

export default function AudioWaveform({ analyserNode, isActive }: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const rafRef = useRef<number>(0)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    if (!isActive || !analyserNode) {
      ctx.clearRect(0, 0, canvas.width, canvas.height)
      // Draw flat line when idle
      ctx.strokeStyle = 'rgba(120,120,140,0.3)'
      ctx.lineWidth = 2
      ctx.beginPath()
      ctx.moveTo(0, canvas.height / 2)
      ctx.lineTo(canvas.width, canvas.height / 2)
      ctx.stroke()
      return
    }

    const bufferLength = analyserNode.frequencyBinCount
    const dataArray = new Uint8Array(bufferLength)

    const draw = () => {
      rafRef.current = requestAnimationFrame(draw)
      analyserNode.getByteTimeDomainData(dataArray)

      ctx.clearRect(0, 0, canvas.width, canvas.height)

      ctx.lineWidth = 2
      ctx.strokeStyle = 'rgb(99 102 241)' // indigo-500 approx
      ctx.beginPath()

      const sliceWidth = canvas.width / bufferLength
      let x = 0

      for (let i = 0; i < bufferLength; i++) {
        const v = dataArray[i] / 128.0
        const y = (v * canvas.height) / 2

        if (i === 0) {
          ctx.moveTo(x, y)
        } else {
          ctx.lineTo(x, y)
        }
        x += sliceWidth
      }

      ctx.lineTo(canvas.width, canvas.height / 2)
      ctx.stroke()
    }

    draw()

    return () => {
      cancelAnimationFrame(rafRef.current)
    }
  }, [analyserNode, isActive])

  return (
    <canvas
      ref={canvasRef}
      width={280}
      height={56}
      className="w-full h-14 rounded-xl bg-surface"
      aria-hidden
    />
  )
}
