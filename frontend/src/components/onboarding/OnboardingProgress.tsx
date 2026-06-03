'use client'

import { cn } from '@/lib/cn'

interface Props {
  currentStep: number
  totalSteps: number
  stepLabels: string[]
}

export default function OnboardingProgress({ currentStep, totalSteps, stepLabels }: Props) {
  return (
    <div className="px-6 py-4">
      {/* Step label */}
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs font-medium text-ink-2">
          {stepLabels[currentStep] ?? ''}
        </span>
        <span className="text-xs text-ink-3">
          {currentStep + 1} / {totalSteps}
        </span>
      </div>

      {/* Progress bar */}
      <div className="h-1 bg-line rounded-full overflow-hidden">
        <div
          className="h-full bg-brand rounded-full transition-all duration-400 ease-out"
          style={{ width: `${((currentStep + 1) / totalSteps) * 100}%` }}
        />
      </div>

      {/* Dot indicators */}
      <div className="flex justify-center gap-1.5 mt-3">
        {Array.from({ length: totalSteps }).map((_, i) => (
          <div
            key={i}
            className={cn(
              'h-1 rounded-full transition-all duration-300',
              i === currentStep
                ? 'w-4 bg-brand'
                : i < currentStep
                  ? 'w-1.5 bg-brand opacity-40'
                  : 'w-1.5 bg-line',
            )}
          />
        ))}
      </div>
    </div>
  )
}
