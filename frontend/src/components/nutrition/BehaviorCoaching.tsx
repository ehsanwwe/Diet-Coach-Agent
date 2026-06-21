'use client'

import { useState } from 'react'
import type { FormEvent } from 'react'
import { useRouter } from 'next/navigation'
import type { Dictionary } from '@/dictionaries/fa'
import type { Locale } from '@/lib/i18n'
import type {
  ContextGuidanceResponse,
  CravingSupportResponse,
  SlipRecoveryResponse,
} from '@/types/nutrition'
import { getContextGuidance, getCravingSupport, getSlipRecovery } from '@/lib/nutrition'

type Mode = 'craving' | 'slip' | 'context'
type Result =
  | { mode: 'craving'; data: CravingSupportResponse }
  | { mode: 'slip'; data: SlipRecoveryResponse }
  | { mode: 'context'; data: ContextGuidanceResponse }

interface Props {
  dict: Pick<Dictionary, 'behaviorCoaching'>
  locale: Locale
}

function Field({
  id,
  label,
  value,
  onChange,
  placeholder,
  type = 'text',
  min,
  max,
  step,
  inputMode,
}: {
  id: string
  label: string
  value: string
  onChange: (value: string) => void
  placeholder?: string
  type?: 'text' | 'number'
  min?: number
  max?: number
  step?: number
  inputMode?: 'text' | 'numeric' | 'decimal'
}) {
  return (
    <div>
      <label htmlFor={id} className="block text-xs font-bold text-ink mb-2">
        {label}
      </label>
      <input
        id={id}
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        min={min}
        max={max}
        step={step}
        inputMode={inputMode ?? (type === 'number' ? 'numeric' : undefined)}
        className="w-full px-3 py-3 rounded-2xl bg-surface border border-line text-sm text-ink placeholder:text-ink-3 focus:outline-none focus:border-brand transition-colors"
      />
    </div>
  )
}

function TextBlock({ label, value }: { label: string; value?: string | null }) {
  if (!value) return null
  return (
    <div>
      <span className="text-xs font-semibold text-brand">{label}</span>
      <p className="text-sm text-ink-2 leading-relaxed mt-0.5">{value}</p>
    </div>
  )
}

function ListBlock({ label, items }: { label: string; items?: string[] }) {
  if (!items?.length) return null
  return (
    <div>
      <span className="text-xs font-semibold text-brand">{label}</span>
      <ul className="mt-2 space-y-1">
        {items.map((item, i) => (
          <li key={`${label}-${i}`} className="text-sm text-ink-2 flex gap-2">
            <span className="text-brand shrink-0">-</span>
            {item}
          </li>
        ))}
      </ul>
    </div>
  )
}

function CoachingOptions({
  label,
  options,
}: {
  label: string
  options?: { title: string; description?: string | null; household_portions?: string | null }[]
}) {
  if (!options?.length) return null
  return (
    <div>
      <span className="text-xs font-semibold text-brand">{label}</span>
      <div className="mt-2 space-y-2">
        {options.map((option, i) => (
          <div key={`${option.title}-${i}`} className="rounded-xl bg-surface p-3">
            <p className="text-sm font-bold text-ink">{option.title}</p>
            {option.description && <p className="text-sm text-ink-2 mt-1">{option.description}</p>}
            {option.household_portions && <p className="text-xs text-ink-3 mt-1">{option.household_portions}</p>}
          </div>
        ))}
      </div>
    </div>
  )
}

export default function BehaviorCoaching({ dict, locale }: Props) {
  const router = useRouter()
  const [mode, setMode] = useState<Mode>('craving')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<Result | null>(null)

  const [cravingFood, setCravingFood] = useState('')
  const [cravingIntensity, setCravingIntensity] = useState('')
  const [hunger, setHunger] = useState('')
  const [stress, setStress] = useState('')
  const [sleepQuality, setSleepQuality] = useState('')
  const [place, setPlace] = useState('')
  const [timeOfDay, setTimeOfDay] = useState('')
  const [note, setNote] = useState('')

  const [whatHappened, setWhatHappened] = useState('')
  const [foods, setFoods] = useState('')
  const [amount, setAmount] = useState('')

  const [contextType, setContextType] = useState<'restaurant' | 'party' | 'travel' | 'work' | 'mixed'>('restaurant')
  const [availableOptions, setAvailableOptions] = useState('')
  const [preferredOption, setPreferredOption] = useState('')

  const tabs: { mode: Mode; label: string }[] = [
    { mode: 'craving', label: dict.behaviorCoaching.cravingTab },
    { mode: 'slip', label: dict.behaviorCoaching.slipTab },
    { mode: 'context', label: dict.behaviorCoaching.contextTab },
  ]

  function validateScale(value: string, min: number, max: number): boolean {
    if (value === '') return true
    const n = Number(value)
    return Number.isInteger(n) && n >= min && n <= max
  }

  async function submit(e: FormEvent) {
    e.preventDefault()
    setError(null)

    if (!validateScale(cravingIntensity, 1, 10) || !validateScale(hunger, 1, 10)) {
      setError(dict.behaviorCoaching.scaleError10)
      return
    }
    if (!validateScale(stress, 1, 5) || !validateScale(sleepQuality, 1, 5)) {
      setError(dict.behaviorCoaching.scaleError5)
      return
    }

    setLoading(true)
    try {
      if (mode === 'craving') {
        const data = await getCravingSupport({
          craving_food: cravingFood.trim() || null,
          craving_intensity_1_10: cravingIntensity ? Number(cravingIntensity) : null,
          hunger_level_1_10: hunger ? Number(hunger) : null,
          stress_level: stress ? Number(stress) : null,
          sleep_quality: sleepQuality ? Number(sleepQuality) : null,
          current_place: place.trim() || null,
          time_of_day: timeOfDay.trim() || null,
          user_note: note.trim() || null,
        })
        setResult({ mode, data })
      } else if (mode === 'slip') {
        const data = await getSlipRecovery({
          what_happened: whatHappened.trim() || null,
          foods_eaten: foods.split(',').map((f) => f.trim()).filter(Boolean),
          approximate_amount: amount.trim() || null,
          stress_level: stress ? Number(stress) : null,
          sleep_quality: sleepQuality ? Number(sleepQuality) : null,
          user_note: note.trim() || null,
        })
        setResult({ mode, data })
      } else {
        const data = await getContextGuidance({
          context_type: contextType,
          available_options: availableOptions.split(',').map((f) => f.trim()).filter(Boolean),
          preferred_option: preferredOption.trim() || null,
          hunger_level_1_10: hunger ? Number(hunger) : null,
          user_note: note.trim() || null,
        })
        setResult({ mode, data })
      }
    } catch (err) {
      if (err instanceof Error && err.message === 'UNAUTHORIZED') {
        router.replace(`/${locale}/login`)
        return
      }
      setError(dict.behaviorCoaching.error)
    } finally {
      setLoading(false)
    }
  }

  const submitLabel =
    mode === 'craving'
      ? loading ? dict.behaviorCoaching.submittingCraving : dict.behaviorCoaching.submitCraving
      : mode === 'slip'
      ? loading ? dict.behaviorCoaching.submittingSlip : dict.behaviorCoaching.submitSlip
      : loading ? dict.behaviorCoaching.submittingContext : dict.behaviorCoaching.submitContext

  return (
    <section className="rounded-2xl bg-elevated p-5 shadow-sm space-y-4">
      <div>
        <h2 className="text-sm font-semibold text-ink">{dict.behaviorCoaching.title}</h2>
        <p className="text-xs text-ink-2 mt-1 leading-relaxed">{dict.behaviorCoaching.subtitle}</p>
      </div>

      <div className="flex gap-2" role="tablist">
        {tabs.map((tab) => (
          <button
            key={tab.mode}
            type="button"
            role="tab"
            aria-selected={mode === tab.mode}
            onClick={() => {
              setMode(tab.mode)
              setResult(null)
              setError(null)
            }}
            className={[
              'flex-1 py-2 rounded-xl text-xs font-bold border transition-colors',
              mode === tab.mode ? 'bg-brand text-elevated border-brand' : 'bg-surface border-line text-ink-2',
            ].join(' ')}
          >
            {tab.label}
          </button>
        ))}
      </div>

      <form onSubmit={submit} className="space-y-3">
        {mode === 'craving' && (
          <>
            <Field id="coach-craving-food" label={dict.behaviorCoaching.cravingFoodLabel} value={cravingFood} onChange={setCravingFood} placeholder={dict.behaviorCoaching.cravingFoodPlaceholder} />
            <div className="grid grid-cols-2 gap-3">
              <Field id="coach-craving-intensity" type="number" min={1} max={10} step={1} label={dict.behaviorCoaching.cravingIntensityLabel} value={cravingIntensity} onChange={setCravingIntensity} />
              <Field id="coach-hunger" type="number" min={1} max={10} step={1} label={dict.behaviorCoaching.hungerScaleLabel} value={hunger} onChange={setHunger} />
            </div>
          </>
        )}

        {mode === 'slip' && (
          <>
            <Field id="coach-slip-happened" label={dict.behaviorCoaching.slipWhatHappenedLabel} value={whatHappened} onChange={setWhatHappened} placeholder={dict.behaviorCoaching.slipWhatHappenedPlaceholder} />
            <div className="grid grid-cols-2 gap-3">
              <Field id="coach-slip-foods" label={dict.behaviorCoaching.slipFoodsLabel} value={foods} onChange={setFoods} placeholder={dict.behaviorCoaching.slipFoodsPlaceholder} />
              <Field id="coach-slip-amount" label={dict.behaviorCoaching.slipAmountLabel} value={amount} onChange={setAmount} placeholder={dict.behaviorCoaching.slipAmountPlaceholder} />
            </div>
          </>
        )}

        {mode === 'context' && (
          <>
            <div>
              <label htmlFor="coach-context-type" className="block text-xs font-bold text-ink mb-2">
                {dict.behaviorCoaching.contextTypeLabel}
              </label>
              <select
                id="coach-context-type"
                value={contextType}
                onChange={(e) => setContextType(e.target.value as typeof contextType)}
                className="w-full px-3 py-3 rounded-2xl bg-surface border border-line text-sm text-ink focus:outline-none focus:border-brand transition-colors"
              >
                <option value="restaurant">{dict.behaviorCoaching.contextRestaurant}</option>
                <option value="party">{dict.behaviorCoaching.contextParty}</option>
                <option value="travel">{dict.behaviorCoaching.contextTravel}</option>
                <option value="work">{dict.behaviorCoaching.contextWork}</option>
                <option value="mixed">{dict.behaviorCoaching.contextMixed}</option>
              </select>
            </div>
            <Field id="coach-options" label={dict.behaviorCoaching.availableOptionsLabel} value={availableOptions} onChange={setAvailableOptions} placeholder={dict.behaviorCoaching.availableOptionsPlaceholder} />
            <Field id="coach-preferred" label={dict.behaviorCoaching.preferredOptionLabel} value={preferredOption} onChange={setPreferredOption} placeholder={dict.behaviorCoaching.preferredOptionPlaceholder} />
          </>
        )}

        <div className="grid grid-cols-2 gap-3">
          <Field id="coach-stress" type="number" min={1} max={5} step={1} label={dict.behaviorCoaching.stressLabel} value={stress} onChange={setStress} />
          <Field id="coach-sleep" type="number" min={1} max={5} step={1} label={dict.behaviorCoaching.sleepQualityLabel} value={sleepQuality} onChange={setSleepQuality} />
        </div>

        {mode !== 'slip' && (
          <div className="grid grid-cols-2 gap-3">
            <Field id="coach-place" label={dict.behaviorCoaching.currentPlaceLabel} value={place} onChange={setPlace} />
            <Field id="coach-time" label={dict.behaviorCoaching.timeOfDayLabel} value={timeOfDay} onChange={setTimeOfDay} />
          </div>
        )}

        <Field id="coach-note" label={dict.behaviorCoaching.noteLabel} value={note} onChange={setNote} placeholder={dict.behaviorCoaching.notePlaceholder} />

        {error && <p role="alert" className="text-sm text-error bg-error/5 rounded-xl px-4 py-3">{error}</p>}

        <button
          type="submit"
          disabled={loading}
          className="w-full py-3 rounded-2xl bg-brand text-elevated font-bold text-sm disabled:opacity-60"
        >
          {submitLabel}
        </button>
      </form>

      {result && (
        <div className="rounded-2xl bg-brand-muted p-4 space-y-3">
          {result.mode === 'craving' && (
            <>
              <TextBlock label={dict.behaviorCoaching.calmingMessage} value={result.data.calming_message} />
              <ListBlock label={dict.behaviorCoaching.likelyTriggers} items={result.data.likely_triggers} />
              <TextBlock label={dict.behaviorCoaching.hungerVsCraving} value={result.data.hunger_vs_craving_assessment} />
              <CoachingOptions label={dict.behaviorCoaching.immediateOptions} options={result.data.immediate_options} />
              <TextBlock label={dict.behaviorCoaching.preventionTip} value={result.data.prevention_tip} />
              <TextBlock label={dict.behaviorCoaching.followUpQuestion} value={result.data.follow_up_question} />
            </>
          )}
          {result.mode === 'slip' && (
            <>
              <TextBlock label={dict.behaviorCoaching.calmingMessage} value={result.data.calming_message} />
              <TextBlock label={dict.behaviorCoaching.dataNotFailure} value={result.data.data_not_failure_message} />
              <ListBlock label={dict.behaviorCoaching.triggerQuestions} items={result.data.likely_trigger_questions} />
              <TextBlock label={dict.behaviorCoaching.patternHypothesis} value={result.data.pattern_hypothesis} />
              <TextBlock label={dict.behaviorCoaching.oneSmallAdjustment} value={result.data.one_small_adjustment} />
              <TextBlock label={dict.behaviorCoaching.nextMealPlan} value={result.data.next_meal_plan} />
              <TextBlock label={dict.behaviorCoaching.tomorrowReset} value={result.data.tomorrow_reset_note} />
              <TextBlock label={dict.behaviorCoaching.noExtremeCompensation} value={result.data.no_extreme_compensation_note} />
            </>
          )}
          {result.mode === 'context' && (
            <>
              <TextBlock label={dict.behaviorCoaching.bestAvailableChoice} value={result.data.best_available_choice} />
              <TextBlock label={dict.behaviorCoaching.flexibleChoice} value={result.data.flexible_choice} />
              <TextBlock label={dict.behaviorCoaching.portionStrategy} value={result.data.portion_strategy} />
              <TextBlock label={dict.behaviorCoaching.plateBalanceTip} value={result.data.plate_balance_tip} />
              <TextBlock label={dict.behaviorCoaching.drinkTip} value={result.data.drink_tip} />
              <TextBlock label={dict.behaviorCoaching.dessertStrategy} value={result.data.dessert_or_snack_strategy} />
              <TextBlock label={dict.behaviorCoaching.highCalorieChoice} value={result.data.if_user_chooses_high_calorie_option} />
              <TextBlock label={dict.behaviorCoaching.nextMealAdjustment} value={result.data.next_meal_adjustment} />
            </>
          )}
          <ListBlock label={dict.behaviorCoaching.safetyNotes} items={result.data.safety_notes} />
          {result.data.requires_human_review && (
            <p className="text-sm text-warm font-bold">{dict.behaviorCoaching.humanReview}</p>
          )}
        </div>
      )}
    </section>
  )
}
