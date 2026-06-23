'use client'

import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { ChevronDown, ChevronUp } from 'lucide-react'
import { cn } from '@/lib/cn'
import type { Dictionary } from '@/dictionaries/fa'
import type { ProfileRequest } from '@/types/onboarding'

interface Props {
  dict: Dictionary['onboarding']
  defaultValues?: Partial<ProfileFormData>
  isSubmitting: boolean
  apiError: string | null
  onSubmit: (data: ProfileRequest) => void
  onBack: () => void
}

export interface ProfileFormData {
  full_name: string
  gender: 'male' | 'female' | 'other' | 'prefer_not_to_say'
  age: number
  height_cm: number
  current_weight_kg: number
  target_weight_kg: number | null
  waist_circumference_cm: number | null
  wrist_circumference_cm: number | null
  thigh_circumference_cm: number | null
}

const GENDERS: Array<{ value: ProfileFormData['gender']; labelKey: keyof Dictionary['onboarding'] }> = [
  { value: 'male', labelKey: 'genderMale' },
  { value: 'female', labelKey: 'genderFemale' },
  { value: 'other', labelKey: 'genderOther' },
  { value: 'prefer_not_to_say', labelKey: 'genderPreferNotToSay' },
]

export default function ProfileStep({ dict, defaultValues, isSubmitting, apiError, onSubmit }: Props) {
  const [moreOpen, setMoreOpen] = useState(false)

  const {
    register,
    handleSubmit,
    formState: { errors },
    watch,
  } = useForm<ProfileFormData>({
    defaultValues: {
      full_name: defaultValues?.full_name ?? '',
      gender: defaultValues?.gender,
      age: defaultValues?.age ?? undefined,
      height_cm: defaultValues?.height_cm ?? undefined,
      current_weight_kg: defaultValues?.current_weight_kg ?? undefined,
      target_weight_kg: defaultValues?.target_weight_kg ?? null,
      waist_circumference_cm: defaultValues?.waist_circumference_cm ?? null,
      wrist_circumference_cm: defaultValues?.wrist_circumference_cm ?? null,
      thigh_circumference_cm: defaultValues?.thigh_circumference_cm ?? null,
    },
  })

  const selectedGender = watch('gender')

  function submit(data: ProfileFormData) {
    onSubmit({
      full_name: data.full_name,
      gender: data.gender,
      age: data.age,
      height_cm: data.height_cm,
      current_weight_kg: data.current_weight_kg,
      target_weight_kg: data.target_weight_kg || null,
      waist_circumference_cm: data.waist_circumference_cm || null,
      wrist_circumference_cm: data.wrist_circumference_cm || null,
      thigh_circumference_cm: data.thigh_circumference_cm || null,
    })
  }

  return (
    <form onSubmit={handleSubmit(submit)} className="flex flex-col h-full">
      <div className="flex-1 overflow-y-auto px-6 py-2 space-y-5">
        <div className="mb-2">
          <h1 className="text-xl font-bold text-ink">{dict.profileTitle}</h1>
          <p className="text-sm text-ink-2 mt-1">{dict.profileSubtitle}</p>
        </div>

        {/* Full name */}
        <Field label={dict.fullName} error={errors.full_name?.message}>
          <input
            {...register('full_name', {
              required: dict.nameRequired,
              minLength: { value: 2, message: dict.nameMin },
              maxLength: { value: 200, message: dict.nameMin },
            })}
            type="text"
            placeholder={dict.fullNamePlaceholder}
            className={inputCls(!!errors.full_name)}
          />
        </Field>

        {/* Gender */}
        <div>
          <label className="text-sm font-medium text-ink-2 mb-2 block">{dict.gender}</label>
          <div className="grid grid-cols-2 gap-2">
            {GENDERS.map(({ value, labelKey }) => (
              <label key={value} className="cursor-pointer">
                <input
                  {...register('gender', { required: dict.genderRequired })}
                  type="radio"
                  value={value}
                  className="sr-only"
                />
                <div
                  className={cn(
                    'px-3 py-2.5 rounded-xl border text-sm text-center transition-colors',
                    selectedGender === value
                      ? 'border-brand bg-brand-muted text-brand font-medium'
                      : 'border-line bg-elevated text-ink-2',
                  )}
                >
                  {dict[labelKey] as string}
                </div>
              </label>
            ))}
          </div>
          {errors.gender && <p className="text-xs text-error mt-1.5">{errors.gender.message}</p>}
        </div>

        {/* Age */}
        <Field label={dict.age} error={errors.age?.message}>
          <input
            {...register('age', {
              required: dict.ageRange,
              valueAsNumber: true,
              min: { value: 10, message: dict.ageRange },
              max: { value: 120, message: dict.ageRange },
            })}
            type="number"
            placeholder={dict.agePlaceholder}
            className={inputCls(!!errors.age)}
          />
        </Field>

        {/* Height */}
        <Field label={dict.heightCm} error={errors.height_cm?.message}>
          <input
            {...register('height_cm', {
              required: dict.heightRequired,
              valueAsNumber: true,
              min: { value: 100, message: dict.heightRange },
              max: { value: 250, message: dict.heightRange },
            })}
            type="number"
            placeholder={dict.heightPlaceholder}
            className={inputCls(!!errors.height_cm)}
          />
        </Field>

        {/* Current weight */}
        <Field label={dict.currentWeight} error={errors.current_weight_kg?.message}>
          <input
            {...register('current_weight_kg', {
              required: dict.weightRequired,
              valueAsNumber: true,
              min: { value: 20, message: dict.weightRange },
              max: { value: 300, message: dict.weightRange },
            })}
            type="number"
            step="0.1"
            placeholder={dict.weightPlaceholder}
            className={inputCls(!!errors.current_weight_kg)}
          />
        </Field>

        {/* Target weight (optional) */}
        <Field
          label={`${dict.targetWeight} ${dict.optional}`}
          error={errors.target_weight_kg?.message}
        >
          <input
            {...register('target_weight_kg', {
              valueAsNumber: true,
              min: { value: 20, message: dict.targetWeightRange },
              max: { value: 300, message: dict.targetWeightRange },
            })}
            type="number"
            step="0.1"
            placeholder={dict.targetWeightPlaceholder}
            className={inputCls(!!errors.target_weight_kg)}
          />
        </Field>

        {/* Collapsed "more details" section */}
        <div>
          <button
            type="button"
            onClick={() => setMoreOpen((o) => !o)}
            className="flex items-center gap-2 text-sm font-medium text-brand py-2"
          >
            {moreOpen
              ? <ChevronUp size={16} />
              : <ChevronDown size={16} />}
            {dict.profileMoreDetails}
          </button>

          {moreOpen && (
            <div className="space-y-5 pt-2">
              {/* Waist (optional) */}
              <Field
                label={`${dict.waist} ${dict.optional}`}
                error={errors.waist_circumference_cm?.message}
              >
                <input
                  {...register('waist_circumference_cm', {
                    valueAsNumber: true,
                    min: { value: 40, message: dict.waistRange },
                    max: { value: 200, message: dict.waistRange },
                  })}
                  type="number"
                  step="0.1"
                  placeholder={dict.waistPlaceholder}
                  className={inputCls(!!errors.waist_circumference_cm)}
                />
              </Field>

              {/* Wrist (optional) */}
              <Field
                label={`${dict.wrist} ${dict.optional}`}
                error={errors.wrist_circumference_cm?.message}
              >
                <input
                  {...register('wrist_circumference_cm', {
                    valueAsNumber: true,
                    min: { value: 10, message: dict.wristRange },
                    max: { value: 30, message: dict.wristRange },
                  })}
                  type="number"
                  step="0.1"
                  placeholder={dict.wristPlaceholder}
                  className={inputCls(!!errors.wrist_circumference_cm)}
                />
              </Field>

              {/* Thigh (optional) */}
              <Field
                label={`${dict.thigh} ${dict.optional}`}
                error={errors.thigh_circumference_cm?.message}
              >
                <input
                  {...register('thigh_circumference_cm', {
                    valueAsNumber: true,
                    min: { value: 30, message: dict.thighRange },
                    max: { value: 100, message: dict.thighRange },
                  })}
                  type="number"
                  step="0.1"
                  placeholder={dict.thighPlaceholder}
                  className={inputCls(!!errors.thigh_circumference_cm)}
                />
              </Field>
            </div>
          )}
        </div>

        {apiError && (
          <p className="text-sm text-error bg-error/10 rounded-xl px-4 py-3">{apiError}</p>
        )}
      </div>

      <div className="px-6 pb-safe pb-8 pt-4 border-t border-line">
        <button
          type="submit"
          disabled={isSubmitting}
          className="w-full py-3.5 rounded-2xl bg-brand text-white font-semibold text-base disabled:opacity-60 transition-opacity"
        >
          {isSubmitting ? dict.saving : dict.next}
        </button>
      </div>
    </form>
  )
}

function Field({ label, error, children }: { label: string; error?: string; children: React.ReactNode }) {
  return (
    <div>
      <label className="text-sm font-medium text-ink-2 mb-1.5 block">{label}</label>
      {children}
      {error && <p className="text-xs text-error mt-1.5">{error}</p>}
    </div>
  )
}

function inputCls(hasError: boolean) {
  return cn(
    'w-full px-4 py-3 rounded-xl border bg-elevated text-ink text-sm placeholder:text-ink-3',
    'focus:outline-none focus:border-brand transition-colors',
    hasError ? 'border-error' : 'border-line',
  )
}
