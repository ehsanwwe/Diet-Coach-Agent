'use client'

import { ChevronLeft } from 'lucide-react'
import { cn } from '@/lib/cn'
import type { Locale } from '@/lib/i18n'
import { getIconFlipClass } from '@/lib/direction'
import OnboardingProgress from './OnboardingProgress'

interface Props {
  locale: Locale
  currentStep: number
  totalSteps: number
  stepLabels: string[]
  onBack?: () => void
  showBack: boolean
  children: React.ReactNode
}

export default function OnboardingShell({
  locale,
  currentStep,
  totalSteps,
  stepLabels,
  onBack,
  showBack,
  children,
}: Props) {
  return (
    <div className="min-h-dvh bg-surface flex flex-col">
      <div className="app-container flex-1 flex flex-col">
        {/* Header */}
        <div className="flex items-center pt-safe pt-4 px-4 pb-2 min-h-[56px]">
          {showBack && onBack ? (
            <button
              onClick={onBack}
              className="w-10 h-10 flex items-center justify-center rounded-full hover:bg-brand-muted transition-colors"
              aria-label="Back"
            >
              <ChevronLeft
                size={22}
                className={cn('text-ink-2', getIconFlipClass(locale))}
              />
            </button>
          ) : (
            <div className="w-10 h-10" />
          )}
        </div>

        {/* Progress */}
        <OnboardingProgress
          currentStep={currentStep}
          totalSteps={totalSteps}
          stepLabels={stepLabels}
        />

        {/* Content */}
        <div className="flex-1 overflow-hidden relative">
          {children}
        </div>
      </div>
    </div>
  )
}
