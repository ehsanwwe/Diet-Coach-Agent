'use client'

import { useState } from 'react'
import type { Dictionary } from '@/dictionaries/fa'
import type { CheckInRequest, CheckInResponse } from '@/types/progress'
import { submitCheckIn } from '@/lib/progress'

interface Props {
  dict: Pick<Dictionary, 'progress' | 'common'>
  onSuccess: (result: CheckInResponse) => void
}

function todayISODate(): string {
  const d = new Date()
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}

function ScaleRow({
  label, value, onChange, ariaLabel,
}: { label: string; value: number | null; onChange: (v: number | null) => void; ariaLabel: string }) {
  return (
    <div>
      <label className="block text-xs font-bold text-ink mb-2">{label}</label>
      <div className="flex gap-2" role="group" aria-label={ariaLabel}>
        {[1, 2, 3, 4, 5].map((n) => {
          const selected = value === n
          return (
            <button
              key={n}
              type="button"
              aria-pressed={selected}
              onClick={() => onChange(selected ? null : n)}
              className={[
                'flex-1 h-11 rounded-xl text-sm font-bold border transition-colors',
                selected ? 'bg-brand text-elevated border-brand' : 'bg-surface border-line text-ink-2',
              ].join(' ')}
            >
              {n}
            </button>
          )
        })}
      </div>
    </div>
  )
}

export default function CheckInForm({ dict, onSuccess }: Props) {
  const [weightKg, setWeightKg] = useState<string>('')
  const [hunger, setHunger] = useState<number | null>(null)
  const [sleepHours, setSleepHours] = useState<string>('')
  const [stress, setStress] = useState<number | null>(null)
  const [activityMinutes, setActivityMinutes] = useState<string>('')
  const [notes, setNotes] = useState<string>('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true)
    setError(null)
    const body: CheckInRequest = {
      check_date: todayISODate(),
      weight_kg: weightKg ? Number(weightKg) : null,
      hunger_level: hunger,
      sleep_hours: sleepHours ? Number(sleepHours) : null,
      stress_level: stress,
      activity_minutes: activityMinutes ? Number(activityMinutes) : null,
      adherence_notes: notes.trim() || null,
    }
    try {
      const result = await submitCheckIn(body)
      onSuccess(result)
    } catch (err) {
      setError(err instanceof Error ? err.message : dict.progress.errSubmitFailed)
    } finally {
      setLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="rounded-2xl bg-elevated p-5 shadow-sm space-y-5">
      <div>
        <h2 className="text-sm font-bold text-ink">{dict.progress.checkInTitle}</h2>
        <p className="text-xs text-ink-2 mt-1 leading-relaxed">{dict.progress.checkInSubtitle}</p>
      </div>

      <div>
        <label htmlFor="ci-weight" className="block text-xs font-bold text-ink mb-2">
          {dict.progress.checkInWeight} <span className="text-ink-3 font-normal">({dict.progress.checkInWeightUnit})</span>
        </label>
        <input
          id="ci-weight"
          type="number"
          inputMode="decimal"
          step="0.1"
          min={20}
          max={300}
          value={weightKg}
          onChange={(e) => setWeightKg(e.target.value)}
          className="w-full px-4 py-3 rounded-2xl bg-surface border border-line text-sm text-ink placeholder:text-ink-3 focus:outline-none focus:border-brand transition-colors"
        />
      </div>

      <ScaleRow
        label={dict.progress.checkInHunger}
        value={hunger}
        onChange={setHunger}
        ariaLabel={dict.progress.checkInHunger}
      />

      <div>
        <label htmlFor="ci-sleep" className="block text-xs font-bold text-ink mb-2">
          {dict.progress.checkInSleep} <span className="text-ink-3 font-normal">({dict.progress.checkInSleepUnit})</span>
        </label>
        <input
          id="ci-sleep"
          type="number"
          inputMode="decimal"
          step="0.5"
          min={0}
          max={24}
          value={sleepHours}
          onChange={(e) => setSleepHours(e.target.value)}
          className="w-full px-4 py-3 rounded-2xl bg-surface border border-line text-sm text-ink placeholder:text-ink-3 focus:outline-none focus:border-brand transition-colors"
        />
      </div>

      <ScaleRow
        label={dict.progress.checkInStress}
        value={stress}
        onChange={setStress}
        ariaLabel={dict.progress.checkInStress}
      />

      <div>
        <label htmlFor="ci-activity" className="block text-xs font-bold text-ink mb-2">
          {dict.progress.checkInActivity} <span className="text-ink-3 font-normal">({dict.progress.checkInActivityUnit})</span>
        </label>
        <input
          id="ci-activity"
          type="number"
          inputMode="numeric"
          step="5"
          min={0}
          max={1440}
          value={activityMinutes}
          onChange={(e) => setActivityMinutes(e.target.value)}
          className="w-full px-4 py-3 rounded-2xl bg-surface border border-line text-sm text-ink placeholder:text-ink-3 focus:outline-none focus:border-brand transition-colors"
        />
      </div>

      <div>
        <label htmlFor="ci-notes" className="block text-xs font-bold text-ink mb-2">
          {dict.progress.checkInNotes}
        </label>
        <textarea
          id="ci-notes"
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          placeholder={dict.progress.checkInNotesPlaceholder}
          rows={3}
          maxLength={2000}
          className="w-full px-4 py-3 rounded-2xl bg-surface border border-line text-sm text-ink placeholder:text-ink-3 resize-none focus:outline-none focus:border-brand transition-colors"
        />
      </div>

      {error && (
        <p className="text-sm text-error bg-error/5 rounded-xl px-4 py-3" role="alert">{error}</p>
      )}

      <button
        type="submit"
        disabled={loading}
        className="w-full py-4 rounded-2xl bg-brand text-elevated font-bold text-sm disabled:opacity-60 transition-opacity"
      >
        {loading ? dict.progress.checkInSubmitting : dict.progress.checkInSubmit}
      </button>
    </form>
  )
}
