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

// ─── Numeric input sanitization ───────────────────────────────────────────────
//
// type="number" permits e / E / + / - and scientific notation in many browsers.
// We use type="text" + inputMode instead, and enforce constraints via three layers:
//  1. onKeyDown  — blocks individual invalid keystrokes before the DOM is updated
//  2. onChange   — strips any residual bad characters and clamps to max
//  3. onPaste    — sanitizes clipboard content before it reaches RHF state

interface NumericConfig {
  allowDecimal: boolean
  max?: number
}

function makeNumericHandlers({ allowDecimal, max }: NumericConfig) {
  /** Remove invalid chars and collapse duplicate dots; clamp to max when complete. */
  function sanitize(raw: string): string {
    let s = raw.replace(allowDecimal ? /[^\d.]/g : /[^\d]/g, '')
    if (allowDecimal) {
      const di = s.indexOf('.')
      if (di !== -1) {
        // Keep only the first decimal separator
        s = s.slice(0, di + 1) + s.slice(di + 1).replace(/\./g, '')
      }
    }
    // Clamp to max — but not while the user is still typing after a dot ("70.")
    if (max !== undefined && s && s !== '.' && !s.endsWith('.')) {
      const n = parseFloat(s)
      if (!isNaN(n) && n > max) s = String(max)
    }
    return s
  }

  function onKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    const { key, ctrlKey, metaKey } = e
    // Always allow browser shortcuts: Ctrl/Cmd+A/C/V/X/Z etc.
    if (ctrlKey || metaKey) return
    // Always allow navigation and editing keys
    if (['Backspace', 'Delete', 'Tab', 'ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(key)) return
    // Allow digits
    if (/^\d$/.test(key)) return
    // Allow the first decimal separator for decimal fields
    if (allowDecimal && key === '.' && !e.currentTarget.value.includes('.')) return
    // Block everything else: e, E, +, -, letters, symbols
    e.preventDefault()
  }

  function makeOnChange(rhfOnChange: React.ChangeEventHandler<HTMLInputElement>) {
    return (e: React.ChangeEvent<HTMLInputElement>) => {
      const cleaned = sanitize(e.target.value)
      // Mutate the input element so RHF reads the sanitized value
      if (e.target.value !== cleaned) e.target.value = cleaned
      rhfOnChange(e)
    }
  }

  function makeOnPaste(rhfOnChange: React.ChangeEventHandler<HTMLInputElement>) {
    return (e: React.ClipboardEvent<HTMLInputElement>) => {
      e.preventDefault()
      const pasted = e.clipboardData.getData('text/plain')
      const el = e.currentTarget
      const s0 = el.selectionStart ?? 0
      const s1 = el.selectionEnd ?? 0
      // Build what the combined value would be, then sanitize it
      el.value = sanitize(el.value.slice(0, s0) + pasted + el.value.slice(s1))
      // RHF reads el.value via the registered ref — pass el as target
      rhfOnChange({ target: el } as unknown as React.ChangeEvent<HTMLInputElement>)
    }
  }

  return { onKeyDown, makeOnChange, makeOnPaste }
}

// ─── Component ────────────────────────────────────────────────────────────────

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

  // Destructure RHF's onChange for every numeric field so we can wrap it.
  // valueAsNumber: true works for type="text" — RHF calls parseFloat(ref.value).
  const { onChange: onChangeAge, ...regAge } = register('age', {
    required: dict.ageRange,
    valueAsNumber: true,
    min: { value: 8, message: dict.ageRange },
    max: { value: 120, message: dict.ageRange },
  })
  const { onChange: onChangeHeight, ...regHeight } = register('height_cm', {
    required: dict.heightRequired,
    valueAsNumber: true,
    min: { value: 80, message: dict.heightRange },
    max: { value: 230, message: dict.heightRange },
  })
  const { onChange: onChangeCW, ...regCurrentWeight } = register('current_weight_kg', {
    required: dict.weightRequired,
    valueAsNumber: true,
    min: { value: 20, message: dict.weightRange },
    max: { value: 300, message: dict.weightRange },
  })
  const { onChange: onChangeTW, ...regTargetWeight } = register('target_weight_kg', {
    valueAsNumber: true,
    min: { value: 20, message: dict.targetWeightRange },
    max: { value: 300, message: dict.targetWeightRange },
  })
  const { onChange: onChangeWaist, ...regWaist } = register('waist_circumference_cm', {
    valueAsNumber: true,
    min: { value: 40, message: dict.waistRange },
    max: { value: 200, message: dict.waistRange },
  })
  const { onChange: onChangeWrist, ...regWrist } = register('wrist_circumference_cm', {
    valueAsNumber: true,
    min: { value: 8, message: dict.wristRange },
    max: { value: 35, message: dict.wristRange },
  })
  const { onChange: onChangeThigh, ...regThigh } = register('thigh_circumference_cm', {
    valueAsNumber: true,
    min: { value: 30, message: dict.thighRange },
    max: { value: 100, message: dict.thighRange },
  })

  // Per-field handler sets (integer vs decimal, with respective max)
  const ageH    = makeNumericHandlers({ allowDecimal: false, max: 120 })
  const heightH = makeNumericHandlers({ allowDecimal: true,  max: 230 })
  const cwH     = makeNumericHandlers({ allowDecimal: true,  max: 300 })
  const twH     = makeNumericHandlers({ allowDecimal: true,  max: 300 })
  const waistH  = makeNumericHandlers({ allowDecimal: true,  max: 200 })
  const wristH  = makeNumericHandlers({ allowDecimal: true,  max: 35  })
  const thighH  = makeNumericHandlers({ allowDecimal: true,  max: 100 })

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
      <div className="flex-1 overflow-y-auto min-h-0 px-6 py-2 space-y-5">
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

        {/* Age — integer, max 120 */}
        <Field label={dict.age} error={errors.age?.message}>
          <input
            {...regAge}
            type="text"
            inputMode="numeric"
            onKeyDown={ageH.onKeyDown}
            onChange={ageH.makeOnChange(onChangeAge)}
            onPaste={ageH.makeOnPaste(onChangeAge)}
            placeholder={dict.agePlaceholder}
            className={inputCls(!!errors.age)}
          />
        </Field>

        {/* Height — decimal, max 230 */}
        <Field label={dict.heightCm} error={errors.height_cm?.message}>
          <input
            {...regHeight}
            type="text"
            inputMode="decimal"
            onKeyDown={heightH.onKeyDown}
            onChange={heightH.makeOnChange(onChangeHeight)}
            onPaste={heightH.makeOnPaste(onChangeHeight)}
            placeholder={dict.heightPlaceholder}
            className={inputCls(!!errors.height_cm)}
          />
        </Field>

        {/* Current weight — decimal, max 300 */}
        <Field label={dict.currentWeight} error={errors.current_weight_kg?.message}>
          <input
            {...regCurrentWeight}
            type="text"
            inputMode="decimal"
            onKeyDown={cwH.onKeyDown}
            onChange={cwH.makeOnChange(onChangeCW)}
            onPaste={cwH.makeOnPaste(onChangeCW)}
            placeholder={dict.weightPlaceholder}
            className={inputCls(!!errors.current_weight_kg)}
          />
        </Field>

        {/* Target weight (optional) — decimal, max 300 */}
        <Field
          label={`${dict.targetWeight} ${dict.optional}`}
          error={errors.target_weight_kg?.message}
        >
          <input
            {...regTargetWeight}
            type="text"
            inputMode="decimal"
            onKeyDown={twH.onKeyDown}
            onChange={twH.makeOnChange(onChangeTW)}
            onPaste={twH.makeOnPaste(onChangeTW)}
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
            {moreOpen ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
            {dict.profileMoreDetails}
          </button>

          {moreOpen && (
            <div className="space-y-5 pt-2">
              {/* Waist (optional) — decimal, max 200 */}
              <Field
                label={`${dict.waist} ${dict.optional}`}
                error={errors.waist_circumference_cm?.message}
              >
                <input
                  {...regWaist}
                  type="text"
                  inputMode="decimal"
                  onKeyDown={waistH.onKeyDown}
                  onChange={waistH.makeOnChange(onChangeWaist)}
                  onPaste={waistH.makeOnPaste(onChangeWaist)}
                  placeholder={dict.waistPlaceholder}
                  className={inputCls(!!errors.waist_circumference_cm)}
                />
              </Field>

              {/* Wrist (optional) — decimal, max 35 */}
              <Field
                label={`${dict.wrist} ${dict.optional}`}
                error={errors.wrist_circumference_cm?.message}
              >
                <input
                  {...regWrist}
                  type="text"
                  inputMode="decimal"
                  onKeyDown={wristH.onKeyDown}
                  onChange={wristH.makeOnChange(onChangeWrist)}
                  onPaste={wristH.makeOnPaste(onChangeWrist)}
                  placeholder={dict.wristPlaceholder}
                  className={inputCls(!!errors.wrist_circumference_cm)}
                />
              </Field>

              {/* Thigh (optional) — decimal, max 100 */}
              <Field
                label={`${dict.thigh} ${dict.optional}`}
                error={errors.thigh_circumference_cm?.message}
              >
                <input
                  {...regThigh}
                  type="text"
                  inputMode="decimal"
                  onKeyDown={thighH.onKeyDown}
                  onChange={thighH.makeOnChange(onChangeThigh)}
                  onPaste={thighH.makeOnPaste(onChangeThigh)}
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
