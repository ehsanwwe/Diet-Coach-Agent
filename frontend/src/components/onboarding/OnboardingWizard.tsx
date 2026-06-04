'use client'

import { useEffect, useState, useCallback, useRef } from 'react'
import { useRouter } from 'next/navigation'
import { AnimatePresence, motion } from 'framer-motion'

import type { Dictionary } from '@/dictionaries/fa'
import type { Locale } from '@/lib/i18n'
import { getSlideX } from '@/lib/direction'
import { ApiRequestError } from '@/lib/api'
import {
  getOnboardingStatus,
  submitProfile,
  submitMedical,
  submitLifestyle,
  submitPreferences,
  submitBehavior,
  completeOnboarding,
} from '@/lib/onboarding'
import type { GoalType, OnboardingStatusResponse } from '@/types/onboarding'

import OnboardingShell from './OnboardingShell'
import ProfileStep, { type ProfileFormData } from './steps/ProfileStep'
import GoalStep from './steps/GoalStep'
import MedicalStep, { type MedicalFormData } from './steps/MedicalStep'
import LifestyleStep, { type LifestyleFormData } from './steps/LifestyleStep'
import PreferencesStep, { type PreferencesFormData } from './steps/PreferencesStep'
import BehaviorStep, { type BehaviorFormData } from './steps/BehaviorStep'
import FinalVideoStep from './steps/FinalVideoStep'

import type { ProfileRequest } from '@/types/onboarding'
import type { MedicalRequest } from '@/types/onboarding'
import type { LifestyleRequest } from '@/types/onboarding'
import type { PreferencesRequest } from '@/types/onboarding'
import type { BehaviorRequest } from '@/types/onboarding'

interface Props {
  dict: Dictionary
  locale: Locale
}

const TOTAL_STEPS = 7

function getInitialStep(status: OnboardingStatusResponse): number {
  switch (status.next_step) {
    case 'profile': return 0
    case 'medical': return 2
    case 'lifestyle': return 3
    case 'preferences': return 4
    case 'behavior': return 5
    default: return 6
  }
}

export default function OnboardingWizard({ dict, locale }: Props) {
  const router = useRouter()
  const d = dict.onboarding

  const [currentStep, setCurrentStep] = useState(0)
  const [direction, setDirection] = useState<'forward' | 'backward'>('forward')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [apiError, setApiError] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [loadError, setLoadError] = useState<string | null>(null)
  const [clinicalReviewRequired, setClinicalReviewRequired] = useState(false)
  const hasNavigatedRef = useRef(false)

  // Preserved form data for back navigation
  const [profileData, setProfileData] = useState<ProfileFormData | null>(null)
  const [goalType, setGoalType] = useState<GoalType | null>(null)
  const [medicalData, setMedicalData] = useState<MedicalFormData | null>(null)
  const [lifestyleData, setLifestyleData] = useState<LifestyleFormData | null>(null)
  const [preferencesData, setPreferencesData] = useState<PreferencesFormData | null>(null)
  const [behaviorData, setBehaviorData] = useState<BehaviorFormData | null>(null)

  useEffect(() => {
    getOnboardingStatus()
      .then((res) => {
        if (res.data.is_onboarded) {
          if (!hasNavigatedRef.current) {
            hasNavigatedRef.current = true
            router.replace(`/${locale}`)
          }
          return
        }
        setCurrentStep(getInitialStep(res.data))
        setIsLoading(false)
      })
      .catch((err) => {
        const msg = err instanceof ApiRequestError
          ? (err.status === 401 ? d.errUnauthorized : d.errLoadFailed)
          : d.errLoadFailed
        setLoadError(msg)
        setIsLoading(false)
      })
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  const goForward = useCallback(() => {
    setDirection('forward')
    setCurrentStep((s) => Math.min(s + 1, TOTAL_STEPS - 1))
    setApiError(null)
  }, [])

  const goBack = useCallback(() => {
    setDirection('backward')
    setCurrentStep((s) => Math.max(s - 1, 0))
    setApiError(null)
  }, [])

  async function withSubmit(fn: () => Promise<void>) {
    setIsSubmitting(true)
    setApiError(null)
    try {
      await fn()
    } catch (err) {
      const msg = err instanceof ApiRequestError
        ? (err.status === 401 ? d.errUnauthorized : err.message || d.errSubmitFailed)
        : d.errSubmitFailed
      setApiError(msg)
    } finally {
      setIsSubmitting(false)
    }
  }

  // ── Step handlers ──────────────────────────────────────────────────────────

  async function handleProfileSubmit(data: ProfileRequest) {
    await withSubmit(async () => {
      await submitProfile(data)
      setProfileData(data as unknown as ProfileFormData)
      goForward()
    })
  }

  function handleGoalSubmit(goal: GoalType) {
    setGoalType(goal)
    goForward()
  }

  async function handleMedicalSubmit(data: MedicalRequest) {
    await withSubmit(async () => {
      const res = await submitMedical(data)
      setMedicalData(data as unknown as MedicalFormData)
      if (res.data.clinical_review_required) {
        setClinicalReviewRequired(true)
      }
      goForward()
    })
  }

  async function handleLifestyleSubmit(data: LifestyleRequest) {
    await withSubmit(async () => {
      await submitLifestyle(data)
      setLifestyleData(data as unknown as LifestyleFormData)
      goForward()
    })
  }

  async function handlePreferencesSubmit(data: PreferencesRequest) {
    await withSubmit(async () => {
      await submitPreferences(data)
      setPreferencesData(data as unknown as PreferencesFormData)
      goForward()
    })
  }

  async function handleBehaviorSubmit(data: BehaviorRequest) {
    await withSubmit(async () => {
      await submitBehavior(data)
      setBehaviorData(data as unknown as BehaviorFormData)
      goForward()
    })
  }

  async function handleComplete() {
    await withSubmit(async () => {
      const res = await completeOnboarding()
      if (!hasNavigatedRef.current) {
        hasNavigatedRef.current = true
        if (res.data.clinical_review_required) {
          router.replace(`/${locale}?onboarded=1&clinical=1`)
        } else {
          router.replace(`/${locale}?onboarded=1`)
        }
      }
    })
  }

  // ── Step labels ────────────────────────────────────────────────────────────
  const stepLabels = [
    d.step1, d.step2, d.step3, d.step4, d.step5, d.step6, d.step7,
  ]

  // ── Slide animation ────────────────────────────────────────────────────────
  const enterX = getSlideX(locale, direction)
  const exitX = -enterX

  const variants = {
    enter: { x: enterX * 3, opacity: 0 },
    center: { x: 0, opacity: 1 },
    exit: { x: exitX * 3, opacity: 0 },
  }

  // ── Loading / error states ─────────────────────────────────────────────────
  if (isLoading) {
    return (
      <div className="min-h-dvh bg-surface flex items-center justify-center">
        <div className="w-8 h-8 rounded-full border-2 border-brand border-t-transparent animate-spin" />
      </div>
    )
  }

  if (loadError) {
    return (
      <div className="min-h-dvh bg-surface flex items-center justify-center px-8">
        <div className="text-center space-y-4">
          <p className="text-sm text-error">{loadError}</p>
          <button
            onClick={() => window.location.reload()}
            className="px-6 py-2.5 rounded-xl bg-brand text-white text-sm font-medium"
          >
            {dict.common.retry}
          </button>
        </div>
      </div>
    )
  }

  // ── Render current step ────────────────────────────────────────────────────
  function renderStep() {
    switch (currentStep) {
      case 0:
        return (
          <ProfileStep
            dict={d}
            defaultValues={profileData ?? undefined}
            isSubmitting={isSubmitting}
            apiError={apiError}
            onSubmit={handleProfileSubmit}
            onBack={goBack}
          />
        )
      case 1:
        return (
          <GoalStep
            dict={d}
            defaultValue={goalType}
            onSubmit={handleGoalSubmit}
            onBack={goBack}
          />
        )
      case 2:
        return (
          <MedicalStep
            dict={d}
            defaultValues={medicalData ?? undefined}
            isSubmitting={isSubmitting}
            apiError={apiError}
            onSubmit={handleMedicalSubmit}
            onBack={goBack}
          />
        )
      case 3:
        return (
          <LifestyleStep
            dict={d}
            defaultValues={lifestyleData ?? undefined}
            isSubmitting={isSubmitting}
            apiError={apiError}
            onSubmit={handleLifestyleSubmit}
            onBack={goBack}
          />
        )
      case 4:
        return (
          <PreferencesStep
            dict={d}
            defaultValues={preferencesData ?? undefined}
            isSubmitting={isSubmitting}
            apiError={apiError}
            onSubmit={handlePreferencesSubmit}
            onBack={goBack}
          />
        )
      case 5:
        return (
          <BehaviorStep
            dict={d}
            defaultValues={behaviorData ?? undefined}
            isSubmitting={isSubmitting}
            apiError={apiError}
            onSubmit={handleBehaviorSubmit}
            onBack={goBack}
          />
        )
      case 6:
        return (
          <FinalVideoStep
            dict={d}
            audioDict={dict.audio}
            isSubmitting={isSubmitting}
            apiError={apiError}
            clinicalReviewRequired={clinicalReviewRequired}
            onComplete={handleComplete}
            onBack={goBack}
          />
        )
      default:
        return null
    }
  }

  return (
    <OnboardingShell
      locale={locale}
      currentStep={currentStep}
      totalSteps={TOTAL_STEPS}
      stepLabels={stepLabels}
      onBack={currentStep > 0 ? goBack : undefined}
      showBack={currentStep > 0}
    >
      <AnimatePresence mode="wait" custom={direction} initial={false}>
        <motion.div
          key={currentStep}
          variants={variants}
          initial="enter"
          animate="center"
          exit="exit"
          transition={{ duration: 0.28, ease: [0.32, 0, 0.67, 0] }}
          className="absolute inset-0 flex flex-col overflow-hidden"
        >
          {renderStep()}
        </motion.div>
      </AnimatePresence>
    </OnboardingShell>
  )
}
