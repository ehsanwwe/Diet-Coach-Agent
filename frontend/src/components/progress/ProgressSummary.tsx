'use client'

import type { Dictionary } from '@/dictionaries/fa'
import type { BehaviorWin, ProgressSummaryResponse } from '@/types/progress'
import WeightSparkline from './WeightSparkline'

interface Props {
  dict: Pick<Dictionary, 'progress'>
  data: ProgressSummaryResponse
}

function winLabel(dict: Props['dict'], win: BehaviorWin): string {
  const key = win.label_key as keyof Dictionary['progress']
  const value = dict.progress[key]
  return typeof value === 'string' ? value : win.key
}

function WinChip({ dict, win }: { dict: Props['dict']; win: BehaviorWin }) {
  if (!win.tracked) {
    return (
      <span
        role="status"
        aria-label={`${winLabel(dict, win)} — ${dict.progress.winNotTracked}`}
        className="px-3 py-1.5 rounded-full text-xs font-bold bg-surface border border-line text-ink-3"
      >
        — {winLabel(dict, win)}
      </span>
    )
  }
  return (
    <span
      role="status"
      aria-label={`${winLabel(dict, win)} — ${win.achieved ? 'achieved' : 'not achieved'}`}
      className={[
        'px-3 py-1.5 rounded-full text-xs font-bold',
        win.achieved
          ? 'bg-brand-muted text-brand'
          : 'bg-surface border border-line text-ink-3',
      ].join(' ')}
    >
      {win.achieved ? '✓ ' : ''}{winLabel(dict, win)}
      {win.value ? ` · ${win.value}` : ''}
    </span>
  )
}

export default function ProgressSummary({ dict, data }: Props) {
  const delta = data.weight_trend?.delta ?? 0
  const deltaClass =
    delta < 0 ? 'text-success' : delta > 0 ? 'text-warm' : 'text-ink-2'
  const deltaSign = delta > 0 ? '+' : ''

  return (
    <div className="space-y-6">
      {/* Weight card */}
      <div className="rounded-2xl bg-elevated p-5 shadow-sm">
        <h2 className="text-xs font-bold text-ink-2 mb-2">{dict.progress.latestWeight}</h2>
        <div className="flex items-end justify-between gap-4">
          <div>
            <p className="text-2xl font-bold text-ink leading-tight">
              {data.latest_weight_kg !== null ? data.latest_weight_kg.toFixed(1) : '—'}
              <span className="text-sm font-bold text-ink-3 ms-1">{dict.progress.unitKg}</span>
            </p>
            {data.weight_trend && (
              <p className={`text-xs font-bold mt-1 ${deltaClass}`}>
                {deltaSign}{data.weight_trend.delta.toFixed(1)} {dict.progress.unitKg}
              </p>
            )}
          </div>
          {data.weight_series.length >= 2 && (
            <WeightSparkline weights={data.weight_series} />
          )}
        </div>
      </div>

      {/* Behavior wins */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-sm font-bold text-ink">{dict.progress.behaviourWinsTitle}</h2>
          <span className="text-xs font-bold text-ink-3">
            {dict.progress.loggingStreak}: <span className="text-brand">{data.logging_streak}</span> {dict.progress.loggingStreakDays}
          </span>
        </div>
        <div className="flex flex-wrap gap-2">
          {data.behavior_wins.map((w) => (
            <WinChip key={w.key} dict={dict} win={w} />
          ))}
        </div>
      </div>
    </div>
  )
}
