'use client'

import { cn } from '@/lib/cn'

interface Props {
  value: number
  onChange: (value: number) => void
  min: number
  max: number
  step?: number
  lowLabel?: string
  highLabel?: string
  className?: string
}

export default function SteppedRangeSlider({
  value,
  onChange,
  min,
  max,
  step = 1,
  lowLabel,
  highLabel,
  className,
}: Props) {
  const steps = Array.from({ length: Math.round((max - min) / step) + 1 }, (_, i) => min + i * step)
  const pct = ((value - min) / (max - min)) * 100

  return (
    <div className={cn('w-full', className)}>
      <div dir="ltr">
        {/* Range input */}
        <div className="relative px-1">
          <input
            type="range"
            min={min}
            max={max}
            step={step}
            value={value}
            onChange={(e) => onChange(Number(e.target.value))}
            aria-valuenow={value}
            aria-valuemin={min}
            aria-valuemax={max}
            className={cn(
              'w-full h-1.5 rounded-full appearance-none cursor-pointer',
              'bg-line [&::-webkit-slider-thumb]:appearance-none',
              '[&::-webkit-slider-thumb]:w-5 [&::-webkit-slider-thumb]:h-5',
              '[&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-brand',
              '[&::-webkit-slider-thumb]:shadow-sm [&::-webkit-slider-thumb]:cursor-pointer',
              '[&::-moz-range-thumb]:w-5 [&::-moz-range-thumb]:h-5',
              '[&::-moz-range-thumb]:rounded-full [&::-moz-range-thumb]:bg-brand',
              '[&::-moz-range-thumb]:border-0 [&::-moz-range-thumb]:cursor-pointer',
            )}
            style={{
              background: `linear-gradient(to right, var(--color-brand) 0%, var(--color-brand) ${pct}%, var(--color-line) ${pct}%, var(--color-line) 100%)`,
            }}
          />
        </div>

        {/* Step dots */}
        <div className="flex justify-between mt-2 px-1">
          {steps.map((s) => (
            <button
              key={s}
              type="button"
              aria-label={String(s)}
              onClick={() => onChange(s)}
              className={cn(
                'w-1.5 h-1.5 rounded-full transition-colors',
                value >= s ? 'bg-brand' : 'bg-line',
              )}
            />
          ))}
        </div>
      </div>

      {(lowLabel || highLabel) && (
        <div className="flex justify-between mt-1.5 px-1">
          <span className="text-xs text-ink-3">{lowLabel}</span>
          <span className="text-xs text-ink-3">{highLabel}</span>
        </div>
      )}
    </div>
  )
}
