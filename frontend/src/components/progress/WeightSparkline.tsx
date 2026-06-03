interface Props {
  weights: number[]
  width?: number
  height?: number
}

/**
 * Inline SVG sparkline for weight series.
 * Renders nothing when fewer than 2 data points exist.
 * Always reads left-to-right (time progression) regardless of locale.
 * PROG-05: weight trend shown as a chart, not just a number.
 */
export default function WeightSparkline({ weights, width = 120, height = 40 }: Props) {
  if (weights.length < 2) return null

  const min = Math.min(...weights)
  const max = Math.max(...weights)
  const range = max - min || 1

  const points = weights.map((w, i) => {
    const x = (i / (weights.length - 1)) * width
    const y = height - ((w - min) / range) * height
    return `${x.toFixed(1)},${y.toFixed(1)}`
  })
  const d = `M ${points.join(' L ')}`

  return (
    <svg
      width={width}
      height={height}
      viewBox={`0 0 ${width} ${height}`}
      aria-hidden="true"
      role="presentation"
    >
      <path
        d={d}
        fill="none"
        stroke="var(--color-brand)"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  )
}
