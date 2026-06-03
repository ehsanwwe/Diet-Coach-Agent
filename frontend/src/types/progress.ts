/**
 * Progress & Reports types — mirrors backend/app/schemas/progress.py.
 * PROG-01, PROG-02, PROG-03.
 */

export interface CheckInRequest {
  check_date: string // ISO-8601 date (YYYY-MM-DD)
  weight_kg?: number | null
  hunger_level?: number | null
  sleep_hours?: number | null
  stress_level?: number | null
  activity_minutes?: number | null
  adherence_notes?: string | null
}

export interface CheckInResponse {
  id: string
  check_date: string
  weight_kg: number | null
  hunger_level: number | null
  sleep_hours: number | null
  stress_level: number | null
  activity_minutes: number | null
  adherence_notes: string | null
  created_at: string
}

export interface WeightTrend {
  first: number
  last: number
  delta: number
}

export type BehaviorWinKey =
  | 'sleep'
  | 'activity'
  | 'logging'
  | 'low_stress'
  | 'low_hunger'
  | 'protein'
  | 'fiber'
  | 'hydration'

export interface BehaviorWin {
  key: BehaviorWinKey
  label_key: string
  achieved: boolean
  value: string | null
  tracked: boolean
}

export interface ProgressSummaryResponse {
  has_data: boolean
  recent_checkins: CheckInResponse[]
  weight_series: number[]
  latest_weight_kg: number | null
  weight_trend: WeightTrend | null
  behavior_wins: BehaviorWin[]
  logging_streak: number
  empty_state_message: string | null
}

export interface WeeklyReportData {
  weight_trend: WeightTrend | null
  weight_series: number[]
  avg_hunger: number | null
  avg_sleep: number | null
  avg_stress: number | null
  total_activity_minutes: number
  logging_days: number
  adherence_pct: number
  sleep_stress_note: string | null
  suggested_focus: string
}

export interface WeeklyReportResponse {
  has_report: boolean
  week_start: string | null
  week_end: string | null
  report: WeeklyReportData | null
  empty_state_message: string | null
}
