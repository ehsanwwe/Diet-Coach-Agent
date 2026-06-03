'use client'

import { useState } from 'react'
import { Shield } from 'lucide-react'
import { cn } from '@/lib/cn'
import type { Dictionary } from '@/dictionaries/fa'
import type { MedicalRequest } from '@/types/onboarding'
import TagInput from '../TagInput'

interface Props {
  dict: Dictionary['onboarding']
  defaultValues?: Partial<MedicalFormData>
  isSubmitting: boolean
  apiError: string | null
  onSubmit: (data: MedicalRequest) => void
  onBack: () => void
}

export interface MedicalFormData {
  diabetes: boolean
  kidney_disease: boolean
  liver_disease: boolean
  thyroid_issues: boolean
  high_blood_pressure: boolean
  high_cholesterol: boolean
  pcos: boolean
  pregnancy_breastfeeding: boolean
  eating_disorder_history: boolean
  bariatric_surgery: boolean
  medications: string[]
  allergies: string[]
  warning_symptoms: string[]
}

type ConditionKey = keyof Omit<MedicalFormData, 'medications' | 'allergies' | 'warning_symptoms'>

const CONDITIONS: Array<{ key: ConditionKey; labelKey: keyof Dictionary['onboarding'] }> = [
  { key: 'diabetes', labelKey: 'medDiabetes' },
  { key: 'kidney_disease', labelKey: 'medKidney' },
  { key: 'liver_disease', labelKey: 'medLiver' },
  { key: 'thyroid_issues', labelKey: 'medThyroid' },
  { key: 'high_blood_pressure', labelKey: 'medBloodPressure' },
  { key: 'high_cholesterol', labelKey: 'medCholesterol' },
  { key: 'pcos', labelKey: 'medPcos' },
  { key: 'pregnancy_breastfeeding', labelKey: 'medPregnancy' },
  { key: 'eating_disorder_history', labelKey: 'medEatingDisorder' },
  { key: 'bariatric_surgery', labelKey: 'medBariatric' },
]

const WARNING_SYMPTOMS: Array<{ value: string; labelKey: keyof Dictionary['onboarding'] }> = [
  { value: 'chest_pain', labelKey: 'medSymChestPain' },
  { value: 'severe_dizziness', labelKey: 'medSymDizziness' },
  { value: 'extreme_fatigue', labelKey: 'medSymFatigue' },
  { value: 'rapid_weight_loss', labelKey: 'medSymWeightLoss' },
  { value: 'fainting', labelKey: 'medSymFainting' },
]

const defaultMedical: MedicalFormData = {
  diabetes: false,
  kidney_disease: false,
  liver_disease: false,
  thyroid_issues: false,
  high_blood_pressure: false,
  high_cholesterol: false,
  pcos: false,
  pregnancy_breastfeeding: false,
  eating_disorder_history: false,
  bariatric_surgery: false,
  medications: [],
  allergies: [],
  warning_symptoms: [],
}

export default function MedicalStep({ dict, defaultValues, isSubmitting, apiError, onSubmit }: Props) {
  const [form, setForm] = useState<MedicalFormData>({ ...defaultMedical, ...defaultValues })

  function toggleCondition(key: ConditionKey) {
    setForm((f) => ({ ...f, [key]: !f[key] }))
  }

  function toggleSymptom(value: string) {
    setForm((f) => ({
      ...f,
      warning_symptoms: f.warning_symptoms.includes(value)
        ? f.warning_symptoms.filter((s) => s !== value)
        : [...f.warning_symptoms, value],
    }))
  }

  function handleSubmit() {
    onSubmit(form)
  }

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-y-auto px-6 py-2 space-y-6">
        <div>
          <h1 className="text-xl font-bold text-ink">{dict.medicalTitle}</h1>
          <p className="text-sm text-ink-2 mt-1">{dict.medicalSubtitle}</p>
        </div>

        {/* Safety notice */}
        <div className="flex gap-2 p-3 rounded-xl bg-brand-muted">
          <Shield size={16} className="text-brand shrink-0 mt-0.5" />
          <p className="text-xs text-ink-2 leading-relaxed">{dict.medicalSafetyNotice}</p>
        </div>

        {/* Conditions */}
        <section>
          <p className="text-sm font-semibold text-ink mb-3">{dict.medConditions}</p>
          <div className="space-y-1 rounded-2xl bg-elevated border border-line overflow-hidden">
            {CONDITIONS.map(({ key, labelKey }, i) => (
              <label
                key={key}
                className={cn(
                  'flex items-center justify-between px-4 py-3 cursor-pointer',
                  i < CONDITIONS.length - 1 && 'border-b border-line',
                )}
              >
                <span className="text-sm text-ink">{dict[labelKey] as string}</span>
                <Toggle checked={form[key]} onToggle={() => toggleCondition(key)} />
              </label>
            ))}
          </div>
        </section>

        {/* Medications */}
        <section>
          <p className="text-sm font-semibold text-ink mb-2">{dict.medMedications}</p>
          <TagInput
            value={form.medications}
            onChange={(v) => setForm((f) => ({ ...f, medications: v }))}
            placeholder={dict.medMedicationsPlaceholder}
            addLabel={dict.medAddItem}
          />
        </section>

        {/* Allergies */}
        <section>
          <p className="text-sm font-semibold text-ink mb-2">{dict.medAllergies}</p>
          <TagInput
            value={form.allergies}
            onChange={(v) => setForm((f) => ({ ...f, allergies: v }))}
            placeholder={dict.medAllergiesPlaceholder}
            addLabel={dict.medAddItem}
          />
        </section>

        {/* Warning symptoms */}
        <section>
          <p className="text-sm font-semibold text-ink mb-3">{dict.medWarningSymptoms}</p>
          <div className="space-y-2">
            {WARNING_SYMPTOMS.map(({ value, labelKey }) => (
              <label
                key={value}
                className={cn(
                  'flex items-center gap-3 px-4 py-3 rounded-xl border cursor-pointer transition-colors',
                  form.warning_symptoms.includes(value)
                    ? 'border-warm bg-warm-muted'
                    : 'border-line bg-elevated',
                )}
              >
                <div
                  className={cn(
                    'w-4.5 h-4.5 rounded border flex items-center justify-center transition-colors shrink-0',
                    form.warning_symptoms.includes(value)
                      ? 'bg-warm border-warm text-white'
                      : 'border-line',
                  )}
                >
                  {form.warning_symptoms.includes(value) && (
                    <svg width="10" height="8" viewBox="0 0 10 8" fill="none">
                      <path d="M1 4L3.5 6.5L9 1" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                    </svg>
                  )}
                </div>
                <span className="text-sm text-ink">{dict[labelKey] as string}</span>
                <input
                  type="checkbox"
                  checked={form.warning_symptoms.includes(value)}
                  onChange={() => toggleSymptom(value)}
                  className="sr-only"
                />
              </label>
            ))}
          </div>
        </section>

        {apiError && (
          <p className="text-sm text-error bg-error/10 rounded-xl px-4 py-3">{apiError}</p>
        )}
      </div>

      <div className="px-6 pb-safe pb-8 pt-4 border-t border-line">
        <button
          type="button"
          onClick={handleSubmit}
          disabled={isSubmitting}
          className="w-full py-3.5 rounded-2xl bg-brand text-white font-semibold text-base disabled:opacity-60 transition-opacity"
        >
          {isSubmitting ? dict.saving : dict.next}
        </button>
      </div>
    </div>
  )
}

function Toggle({ checked, onToggle }: { checked: boolean; onToggle: () => void }) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      onClick={onToggle}
      className={cn(
        'relative w-11 h-6 rounded-full transition-colors duration-200 shrink-0',
        checked ? 'bg-brand' : 'bg-line',
      )}
    >
      <span
        dir="ltr"
        className={cn(
          'absolute top-0.5 h-5 w-5 rounded-full bg-white shadow-sm transition-transform duration-200',
          checked ? 'translate-x-5' : 'translate-x-0.5',
        )}
      />
    </button>
  )
}
