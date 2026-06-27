'use client'

import { useState } from 'react'
import type { CalendarResponse, PlanDay } from '@/types/nutrition'
import type { Dictionary } from '@/dictionaries/fa'
import AppIcon, { type AppIconName } from '@/components/ui/AppIcon'

interface Props {
  calendar: CalendarResponse
  dict: Dictionary
  locale: string
  onGenerateNextWeek: () => void
  generating: boolean
}

const MEAL_SLOT_ORDER: Record<string, number> = {
  breakfast: 1,
  morning_snack: 2,
  lunch: 3,
  pre_workout: 4,
  post_workout: 5,
  afternoon_snack: 6,
  dinner: 7,
  optional_evening_snack: 8,
  snack: 9,
  other: 10,
}

function sortMeals(meals: import('@/types/nutrition').CalendarMeal[]): import('@/types/nutrition').CalendarMeal[] {
  return [...meals].sort((a, b) => {
    // 1. Canonical slot/type order is always primary.
    // Persisted meal_order may be stale from older generated plans, so the UI
    // uses canonical slot order first and treats meal_order only as a last resort.
    const aOrd = MEAL_SLOT_ORDER[a.meal_slot ?? a.meal_type] ?? 99
    const bOrd = MEAL_SLOT_ORDER[b.meal_slot ?? b.meal_type] ?? 99
    if (aOrd !== bOrd) return aOrd - bOrd
    // 2. time_window_start (when same slot)
    if (a.time_window_start && b.time_window_start) {
      return a.time_window_start.localeCompare(b.time_window_start)
    }
    if (a.time_window_start) return -1
    if (b.time_window_start) return 1
    // 3. meal_order as final stable fallback only (may be stale)
    if (a.meal_order != null && b.meal_order != null) return a.meal_order - b.meal_order
    return 0
  })
}

const MEAL_ICONS: Record<string, AppIconName> = {
  breakfast: 'sunrise',
  lunch: 'lunch',
  dinner: 'dinner',
  snack: 'snack',
  morning_snack: 'snack',
  afternoon_snack: 'snack',
  optional_evening_snack: 'snack',
  pre_workout: 'activity',
  post_workout: 'activity',
  other: 'meal',
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
        <AppIcon
          name={isExpanded ? 'chevronUp' : 'chevronDown'}
          className="text-ink-3 ms-3 shrink-0"
          size={18}
        />
      </button>

      {isExpanded && (
        <div className="px-5 pb-5 space-y-4 border-t border-line">
          {day.summary && (
            <p className="text-xs text-ink-2 leading-relaxed pt-3">{day.summary}</p>
          )}

          {/* Day metadata row */}
          {(day.daily_calories ?? day.day_type ?? day.difficulty_level) && (
            <div className="flex flex-wrap gap-2 pt-1">
              {day.day_type && (
                <span className="text-xs px-2 py-0.5 rounded-full bg-brand-muted text-brand font-medium">
                  {day.day_type === 'training_day' ? d.dayTypeTraining
                    : day.day_type === 'rest_day' ? d.dayTypeRest
                    : d.dayTypeLight}
                </span>
              )}
              {day.daily_calories != null && (
                <span className="text-xs px-2 py-0.5 rounded-full bg-elevated border border-line text-ink-2">
                  {day.daily_calories} {locale === 'en' ? 'kcal' : 'کیلوکالری'}
                </span>
              )}
              {day.difficulty_level && (
                <span className="text-xs px-2 py-0.5 rounded-full bg-elevated border border-line text-ink-3">
                  {d.difficulty}: {day.difficulty_level}
                </span>
              )}
            </div>
          )}

          {day.hydration_goal && (
            <p className="text-xs text-ink-3 flex items-center gap-1.5">
              <AppIcon name="water" size={14} />
              <span>{d.hydrationGoal}: {day.hydration_goal}</span>
            </p>
          )}
          <div className="space-y-3">
            {sortMeals(day.meals).map((meal) => {
              const slotKey = meal.meal_slot ?? meal.meal_type
              const icon = MEAL_ICONS[slotKey] ?? 'meal'
              const mealLabel = d[slotKey as keyof typeof d] ?? meal.meal_type
              return (
                <div key={meal.id} className="flex gap-3 items-start">
                  <AppIcon name={icon} className="text-brand shrink-0 mt-0.5" size={18} />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-0.5 flex-wrap">
                      <p className="text-xs font-semibold text-brand">{String(mealLabel)}</p>
                      {meal.time_window_start && meal.time_window_end && (
                        <span className="text-xs text-ink-3">
                          {meal.time_window_start}–{meal.time_window_end}
                        </span>
                      )}
                      {meal.calories_estimate != null && (
                        <span className="text-xs text-ink-3">
                          {meal.calories_estimate} {locale === 'en' ? 'kcal' : 'ککال'}
                        </span>
                      )}
                    </div>
                    <p className="text-sm font-medium text-ink">{meal.title}</p>
                    {meal.description && (
                      <p className="text-xs text-ink-2 mt-0.5 leading-relaxed">{meal.description}</p>
                    )}
                    {meal.portion_guidance && (
                      <p className="text-xs text-ink-3 mt-1 flex items-center gap-1.5">
                        <AppIcon name="portion" size={13} />
                        <span>{d.portionGuidance}: {meal.portion_guidance}</span>
                      </p>
                    )}
                    {meal.drink_guidance && (
                      <p className="text-xs text-ink-3 mt-1 flex items-center gap-1.5">
                        <AppIcon name="water" size={13} />
                        <span>{meal.drink_guidance}</span>
                      </p>
                    )}
                    {meal.alternatives && meal.alternatives.length > 0 && (
                      <p className="text-xs text-ink-3 mt-1 flex items-center gap-1.5">
                        <AppIcon name="refresh" size={13} />
                        <span>{d.alternatives}: {meal.alternatives.join('، ')}</span>
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

          {/* Guidance section */}
          {(day.training_guidance ?? day.medical_warnings?.length ?? day.sleep_wake_guidance ?? day.cheat_meal_guidance ?? day.hydration_plan) && (
            <div className="space-y-2 border-t border-line pt-3">
              {day.medical_warnings && day.medical_warnings.length > 0 && (
                <div className="rounded-xl bg-warm-muted border border-warm/20 p-3">
                  <p className="text-xs font-semibold text-warm mb-1">{d.medicalWarnings}</p>
                  {day.medical_warnings.map((w, i) => (
                    <p key={i} className="text-xs text-ink-2">• {w}</p>
                  ))}
                </div>
              )}
              {day.training_guidance && (
                <p className="text-xs text-ink-2 flex items-start gap-1.5">
                  <AppIcon name="activity" size={13} className="mt-0.5 shrink-0" />
                  <span><span className="font-semibold">{d.trainingGuidance}:</span> {day.training_guidance}</span>
                </p>
              )}
              {day.sleep_wake_guidance && (
                <p className="text-xs text-ink-2">
                  <span className="font-semibold">{d.sleepWakeGuidance}:</span> {day.sleep_wake_guidance}
                </p>
              )}
              {day.cheat_meal_guidance && (
                <p className="text-xs text-ink-2">
                  <span className="font-semibold">{d.cheatMealGuidance}:</span> {day.cheat_meal_guidance}
                </p>
              )}
              {day.hydration_plan && day.hydration_plan !== day.hydration_goal && (
                <p className="text-xs text-ink-2 flex items-start gap-1.5">
                  <AppIcon name="water" size={13} className="mt-0.5 shrink-0" />
                  <span><span className="font-semibold">{d.hydrationPlan}:</span> {day.hydration_plan}</span>
                </p>
              )}
            </div>
          )}

          {/* Budget section */}
          {(day.budget_tier ?? day.budget_guidance ?? day.shopping_notes) && (
            <div className="space-y-1 border-t border-line pt-3">
              {day.budget_tier && (
                <span className={[
                  'inline-block text-xs font-medium px-2 py-0.5 rounded-full',
                  day.budget_tier === 'economic' ? 'bg-green-100 text-green-700' :
                  day.budget_tier === 'premium' ? 'bg-purple-100 text-purple-700' :
                  'bg-gray-100 text-gray-600',
                ].join(' ')}>
                  {day.budget_tier === 'economic' ? d.budgetEconomic
                    : day.budget_tier === 'premium' ? d.budgetPremium
                    : d.budgetStandard}
                </span>
              )}
              {day.budget_guidance && (
                <p className="text-xs text-ink-2 leading-relaxed">{day.budget_guidance}</p>
              )}
              {day.shopping_notes && (
                <p className="text-xs text-ink-3 leading-relaxed">{day.shopping_notes}</p>
              )}
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
