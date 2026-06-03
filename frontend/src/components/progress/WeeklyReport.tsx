'use client'

import type { Dictionary } from '@/dictionaries/fa'
import type { WeeklyReportResponse } from '@/types/progress'

interface Props {
  dict: Pick<Dictionary, 'progress'>
  data: WeeklyReportResponse
}

function MetricRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between py-2 border-b border-line last:border-0">
      <span className="text-xs font-bold text-ink-3">{label}</span>
      <span className="text-sm font-bold text-ink">{value}</span>
    </div>
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
      {/* Period & adherence headline */}
      <div className="rounded-2xl bg-elevated p-5 shadow-sm">
        <p className="text-xs font-bold text-ink-3">{dict.progress.weeklyPeriod}</p>
        <p className="text-sm font-bold text-ink mt-1">
          {data.week_start} — {data.week_end}
        </p>
        <div className="mt-4 text-center">
          <p className="text-2xl font-bold text-brand">{r.adherence_pct}{dict.progress.unitPercent}</p>
          <p className="text-xs font-bold text-ink-3 mt-1">{dict.progress.weeklyAdherence}</p>
        </div>
      </div>

      {/* Metrics */}
      <div className="rounded-2xl bg-elevated p-5 shadow-sm">
        {r.weight_trend && (
          <MetricRow
            label={dict.progress.weeklyWeightDelta}
            value={`${r.weight_trend.delta > 0 ? '+' : ''}${r.weight_trend.delta.toFixed(1)} ${dict.progress.unitKg}`}
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
          <MetricRow
            label={dict.progress.weeklyAvgStress}
            value={r.avg_stress.toFixed(1)}
          />
        )}
        {r.avg_hunger !== null && (
          <MetricRow
            label={dict.progress.weeklyAvgHunger}
            value={r.avg_hunger.toFixed(1)}
          />
        )}
        <MetricRow
          label={dict.progress.weeklyTotalActivity}
          value={`${r.total_activity_minutes} ${dict.progress.unitMinutes}`}
        />
      </div>

      {/* Sleep/stress note */}
      {r.sleep_stress_note && (
        <div className="rounded-xl bg-warm-muted p-4 text-sm text-ink-2 leading-relaxed">
          {r.sleep_stress_note}
        </div>
      )}

      {/* Suggested focus */}
      <div className="rounded-xl bg-brand-muted p-4">
        <p className="text-xs font-bold text-brand mb-1">{dict.progress.weeklyFocusTitle}</p>
        <p className="text-sm text-ink-2 leading-relaxed">{r.suggested_focus}</p>
      </div>
    </div>
  )
}
