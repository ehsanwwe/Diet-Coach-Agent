'use client'

import { cn } from '@/lib/cn'

interface Props {
  value: number
  onChange: (value: number) => void
  min: number
  max: number
  lowLabel?: string
  highLabel?: string
  className?: string
}

export default function SteppedScale({ value, onChange, min, max, lowLabel, highLabel, className }: Props) {
  const steps = Array.from({ length: max - min + 1 }, (_, i) => min + i)

  return (
    <div className={cn('w-full', className)}>
      <div className="flex gap-1" dir="ltr">
        {steps.map((step) => (
          <button
            key={step}
            type="button"
            onClick={() => onChange(step)}
            aria-label={String(step)}
            aria-pressed={value === step}
            className={cn(
              'flex-1 flex flex-col items-center gap-1 py-2 rounded-xl border text-xs font-semibold transition-colors',
              value === step
                ? 'bg-brand border-brand text-white'
                : value > step
                  ? 'bg-brand/15 border-brand/30 text-brand'
                  : 'bg-elevated border-line text-ink-3',
            )}
          >
            <span className="leading-none">{step}</span>
          </button>
        ))}
      </div>
      {(lowLabel || highLabel) && (
        <div className="flex justify-between mt-1.5 px-0.5">
          <span className="text-xs text-ink-3">{lowLabel}</span>
          <span className="text-xs text-ink-3">{highLabel}</span>
        </div>
      )}
    </div>
  )
}
