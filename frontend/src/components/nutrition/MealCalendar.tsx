'use client'

import { useState } from 'react'
import type { CalendarResponse, PlanDay } from '@/types/nutrition'
import type { Dictionary } from '@/dictionaries/fa'

interface Props {
  calendar: CalendarResponse
  dict: Dictionary
  locale: string
  onGenerateNextWeek: () => void
  generating: boolean
}

const MEAL_ICONS: Record<string, string> = {
  breakfast: '🌅',
  lunch: '☀️',
  dinner: '🌙',
  snack: '🍎',
  other: '🍽️',
}

function formatDate(isoDate: string, locale: string): string {
  try {
    const d = new Date(isoDate + 'T00:00:00')
    const localeTag = locale === 'fa' ? 'fa-IR' : locale === 'ar' ? 'ar' : 'en'
    return d.toLocaleDateString(localeTag, { weekday: 'short', month: 'short', day: 'numeric' })
  } catch {
    return isoDate
  }
}

function isToday(isoDate: string): boolean {
  return isoDate === new Date().toISOString().slice(0, 10)
}

function DayCard({ day, dict, locale, isExpanded, onToggle }: {
  day: PlanDay
  dict: Dictionary
  locale: string
  isExpanded: boolean
  onToggle: () => void
}) {
  const today = isToday(day.plan_date)
  const d = dict.calendar

  return (
    <div className={[
      'rounded-2xl bg-elevated shadow-sm overflow-hidden transition-all',
      today ? 'ring-2 ring-brand' : '',
    ].join(' ')}>
      <button
        type="button"
        onClick={onToggle}
        className="w-full flex items-center justify-between px-5 py-4 text-start"
      >
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-0.5">
            {today && (
              <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-brand text-elevated">
                {d.today}
              </span>
            )}
            <span className="text-xs text-ink-3">{formatDate(day.plan_date, locale)}</span>
          </div>
          <p className="text-sm font-semibold text-ink truncate">{day.title}</p>
        </div>
        <span className="text-ink-3 ms-3 shrink-0">{isExpanded ? '▲' : '▼'}</span>
      </button>

      {isExpanded && (
        <div className="px-5 pb-5 space-y-4 border-t border-line">
          {day.summary && (
            <p className="text-xs text-ink-2 leading-relaxed pt-3">{day.summary}</p>
          )}
          {day.hydration_goal && (
            <p className="text-xs text-ink-3">💧 {d.hydrationGoal}: {day.hydration_goal}</p>
          )}
          <div className="space-y-3">
            {day.meals.map((meal) => {
              const icon = MEAL_ICONS[meal.meal_type] ?? '🍽️'
              const mealLabel = d[meal.meal_type as keyof typeof d] ?? meal.meal_type
              return (
                <div key={meal.id} className="flex gap-3 items-start">
                  <span className="text-lg shrink-0 mt-0.5">{icon}</span>
                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-semibold text-brand mb-0.5">{String(mealLabel)}</p>
                    <p className="text-sm font-medium text-ink">{meal.title}</p>
                    {meal.description && (
                      <p className="text-xs text-ink-2 mt-0.5 leading-relaxed">{meal.description}</p>
                    )}
                    {meal.portion_guidance && (
                      <p className="text-xs text-ink-3 mt-1">📏 {d.portionGuidance}: {meal.portion_guidance}</p>
                    )}
                    {meal.alternatives && meal.alternatives.length > 0 && (
                      <p className="text-xs text-ink-3 mt-1">
                        🔄 {d.alternatives}: {meal.alternatives.join('، ')}
                      </p>
                    )}
                  </div>
                </div>
              )
            })}
          </div>
          {day.warnings && day.warnings.length > 0 && (
            <div className="rounded-xl bg-warm-muted border border-warm/20 p-3">
              <p className="text-xs font-semibold text-warm mb-1">{d.warnings}</p>
              {day.warnings.map((w, i) => (
                <p key={i} className="text-xs text-ink-2">• {w}</p>
              ))}
            </div>
          )}
          {day.notes && (
            <p className="text-xs text-ink-3 italic">{d.notes}: {day.notes}</p>
          )}
        </div>
      )}
    </div>
  )
}

export default function MealCalendar({ calendar, dict, locale, onGenerateNextWeek, generating }: Props) {
  const [expandedId, setExpandedId] = useState<string | null>(() => {
    const today = new Date().toISOString().slice(0, 10)
    return calendar.days.find(d => d.plan_date === today)?.id ?? calendar.days[0]?.id ?? null
  })

  const d = dict.calendar
  const renewal = calendar.renewal_status

  return (
    <div className="space-y-4">
      {/* Coverage summary */}
      <div className="rounded-2xl bg-elevated p-4 shadow-sm flex justify-between text-center">
        <div>
          <p className="text-lg font-bold text-ink">{calendar.coverage.planned_days_count}</p>
          <p className="text-xs text-ink-3">{d.plannedDays}</p>
        </div>
        <div className="w-px bg-line" />
        <div>
          <p className="text-lg font-bold text-ink">{calendar.coverage.missing_days_count}</p>
          <p className="text-xs text-ink-3">{d.missingDays}</p>
        </div>
        {calendar.coverage.next_unplanned_date && (
          <>
            <div className="w-px bg-line" />
            <div>
              <p className="text-xs font-bold text-ink">{calendar.coverage.next_unplanned_date}</p>
              <p className="text-xs text-ink-3">{d.nextUnplannedDate}</p>
            </div>
          </>
        )}
      </div>

      {/* Renewal prompt */}
      {renewal.should_prompt_next_week && (
        <div className={[
          'rounded-2xl p-4 space-y-3',
          renewal.prompt_level === 'warning' ? 'bg-warm-muted border border-warm/30' : 'bg-brand-muted border border-brand/20',
        ].join(' ')}>
          <div>
            <p className="text-sm font-semibold text-ink">{d.nextWeekPromptTitle}</p>
            <p className="text-xs text-ink-2 mt-1">{d.nextWeekPromptDescription}</p>
          </div>
          <button
            type="button"
            disabled={generating}
            onClick={onGenerateNextWeek}
            className="w-full py-3 rounded-xl bg-brand text-elevated font-semibold text-sm disabled:opacity-60"
          >
            {generating ? d.generationLoading : d.nextWeekPromptCta}
          </button>
        </div>
      )}

      {/* Day cards */}
      {calendar.days.map((day) => (
        <DayCard
          key={day.id}
          day={day}
          dict={dict}
          locale={locale}
          isExpanded={expandedId === day.id}
          onToggle={() => setExpandedId(expandedId === day.id ? null : day.id)}
        />
      ))}

      {/* Generate next week button (always visible at bottom if days exist) */}
      {!renewal.should_prompt_next_week && calendar.days.length > 0 && (
        <button
          type="button"
          disabled={generating}
          onClick={onGenerateNextWeek}
          className="w-full py-4 rounded-2xl border border-brand text-brand font-semibold text-sm disabled:opacity-60"
        >
          {generating ? d.generationLoading : d.generateNextWeek}
        </button>
      )}
    </div>
  )
}
