'use client'

import type { ReactNode } from 'react'
import type { Dictionary } from '@/dictionaries/fa'
import type { WeeklyReportResponse } from '@/types/progress'

interface Props {
  dict: Pick<Dictionary, 'progress'>
  data: WeeklyReportResponse
}

function MetricRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between gap-4 py-2 border-b border-line last:border-0">
      <span className="text-xs font-bold text-ink-3">{label}</span>
      <span className="text-sm font-bold text-ink text-end">{value}</span>
    </div>
  )
}

function TextCard({ title, children, tone = 'neutral' }: { title: string; children: ReactNode; tone?: 'neutral' | 'brand' | 'warm' }) {
  const classes =
    tone === 'brand'
      ? 'bg-brand-muted'
      : tone === 'warm'
      ? 'bg-warm-muted border border-warm/20'
      : 'bg-elevated shadow-sm'
  return (
    <div className={`rounded-2xl p-5 ${classes}`}>
      {title && <h3 className="text-sm font-semibold text-ink mb-2">{title}</h3>}
      {children}
    </div>
  )
}

function ListCard({ title, items, tone }: { title: string; items?: string[]; tone?: 'neutral' | 'brand' | 'warm' }) {
  if (!items?.length) return null
  return (
    <TextCard title={title} tone={tone}>
      <ul className="space-y-2">
        {items.map((item, i) => (
          <li key={`${title}-${i}`} className="text-sm text-ink-2 flex gap-2 leading-relaxed">
            <span className="text-brand shrink-0">-</span>
            {item}
          </li>
        ))}
      </ul>
    </TextCard>
  )
}

function QualityRows({ rows }: { rows: { label: string; value?: string | null }[] }) {
  const visible = rows.filter((row) => row.value)
  if (visible.length === 0) return null
  return (
    <TextCard title="">
      <div className="space-y-3">
        {visible.map((row) => (
          <div key={row.label}>
            <span className="text-xs font-semibold text-brand">{row.label}</span>
            <p className="text-sm text-ink-2 mt-0.5 leading-relaxed">{row.value}</p>
          </div>
        ))}
      </div>
    </TextCard>
  )
}

export default function WeeklyReport({ dict, data }: Props) {
  if (!data.has_report || !data.report) {
    return (
      <div className="rounded-2xl bg-elevated p-6 shadow-sm text-center space-y-2">
        <h2 className="text-base font-bold text-ink">{dict.progress.emptyWeeklyTitle}</h2>
        <p className="text-sm text-ink-2 leading-relaxed">
          {data.empty_state_message ?? dict.progress.emptyWeeklyDesc}
        </p>
      </div>
    )
  }

  const r = data.report

  return (
    <div className="space-y-4">
      <div className="rounded-2xl bg-elevated p-5 shadow-sm">
        <p className="text-xs font-bold text-ink-3">{dict.progress.weeklyPeriod}</p>
        <p className="text-sm font-bold text-ink mt-1">
          {data.week_start} - {data.week_end}
        </p>
        <div className="mt-4 text-center">
          <p className="text-2xl font-bold text-brand">
            {r.adherence_pct}{dict.progress.unitPercent}
          </p>
          <p className="text-xs font-bold text-ink-3 mt-1">{dict.progress.weeklyAdherence}</p>
        </div>
      </div>

      {r.summary && (
        <TextCard title={dict.progress.weeklySummaryTitle} tone="brand">
          <p className="text-sm text-ink-2 leading-relaxed">{r.summary}</p>
        </TextCard>
      )}

      {(r.requires_human_review || r.human_review_recommended) && (
        <TextCard title={dict.progress.weeklyHumanReview} tone="warm">
          <p className="text-sm text-ink-2 leading-relaxed">
            {dict.progress.weeklyHumanReview}
          </p>
        </TextCard>
      )}

      <div className="rounded-2xl bg-elevated p-5 shadow-sm">
        {r.weight_trend && (
          <MetricRow
            label={dict.progress.weeklyWeightDelta}
            value={`${r.weight_trend.delta > 0 ? '+' : ''}${r.weight_trend.delta.toFixed(1)} ${dict.progress.unitKg}`}
          />
        )}
        {r.waist_trend && (
          <MetricRow
            label={dict.progress.weeklyWaistDelta}
            value={`${r.waist_trend.delta > 0 ? '+' : ''}${r.waist_trend.delta.toFixed(1)} ${dict.progress.checkInWaistUnit}`}
          />
        )}
        <MetricRow
          label={dict.progress.weeklyLoggingDays}
          value={`${r.logging_days} ${dict.progress.loggingStreakDays}`}
        />
        {r.avg_sleep !== null && (
          <MetricRow
            label={dict.progress.weeklyAvgSleep}
            value={`${r.avg_sleep.toFixed(1)} ${dict.progress.unitHours}`}
          />
        )}
        {r.avg_stress !== null && (
          <MetricRow label={dict.progress.weeklyAvgStress} value={r.avg_stress.toFixed(1)} />
        )}
        {r.avg_hunger !== null && (
          <MetricRow label={dict.progress.weeklyAvgHunger} value={r.avg_hunger.toFixed(1)} />
        )}
        {r.avg_hunger_level_1_10 != null && (
          <MetricRow label={dict.progress.checkInHunger10} value={r.avg_hunger_level_1_10.toFixed(1)} />
        )}
        <MetricRow
          label={dict.progress.weeklyTotalActivity}
          value={`${r.total_activity_minutes} ${dict.progress.unitMinutes}`}
        />
        {r.confidence_level && (
          <MetricRow label={dict.progress.weeklyConfidence} value={r.confidence_level} />
        )}
      </div>

      {r.adherence_summary && (
        <TextCard title={dict.progress.weeklyAdherenceSummary}>
          <p className="text-sm text-ink-2 leading-relaxed">{r.adherence_summary}</p>
        </TextCard>
      )}

      <ListCard title={dict.progress.weeklyStrengths} items={r.three_strengths} tone="brand" />
      <ListCard title={dict.progress.weeklyAdjustments} items={r.two_small_adjustments} />

      {r.next_week_small_goal && (
        <TextCard title={dict.progress.weeklyNextGoal} tone="brand">
          <p className="text-sm text-ink-2 leading-relaxed">{r.next_week_small_goal}</p>
        </TextCard>
      )}

      <ListCard title={dict.progress.weeklyRiskyMeals} items={r.risky_meals} />
      <ListCard title={dict.progress.weeklyRiskyWindows} items={r.risky_time_windows} />
      <ListCard title={dict.progress.weeklyCravingPatterns} items={r.craving_patterns} />

      <div className="space-y-3">
        <h3 className="text-sm font-semibold text-ink">{dict.progress.weeklyQualityTitle}</h3>
        <QualityRows
          rows={[
            { label: dict.progress.weeklyProteinQuality, value: r.protein_quality },
            { label: dict.progress.weeklyFiberQuality, value: r.fiber_quality },
            { label: dict.progress.weeklyHydrationQuality, value: r.hydration_quality },
            { label: dict.progress.weeklySimpleSugarQuality, value: r.simple_sugar_quality },
          ]}
        />
      </div>

      <QualityRows
        rows={[
          { label: dict.progress.weeklySleepFood, value: r.sleep_food_relationship ?? r.sleep_stress_note },
          { label: dict.progress.weeklyStressFood, value: r.stress_food_relationship },
          { label: dict.progress.weeklyEatingOut, value: r.eating_out_pattern },
          { label: dict.progress.weeklyBehaviorPattern, value: r.behavior_pattern_summary },
          { label: dict.progress.weeklyMonitoringNotes, value: r.monitoring_notes },
        ]}
      />

      <ListCard title={dict.progress.weeklySafetyNotes} items={r.safety_notes} tone="warm" />

      <TextCard title={dict.progress.weeklyFocusTitle} tone="brand">
        <p className="text-sm text-ink-2 leading-relaxed">{r.suggested_focus}</p>
      </TextCard>
    </div>
  )
}
