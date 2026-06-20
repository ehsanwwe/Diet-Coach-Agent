/**
 * Progress & Reports types — mirrors backend/app/schemas/progress.py.
 * PROG-01, PROG-02, PROG-03.
 */

export interface CheckInRequest {
  check_date: string // ISO-8601 date (YYYY-MM-DD)
  weight_kg?: number | null
  waist_cm?: number | null
  hunger_level?: number | null
  hunger_level_1_10?: number | null
  sleep_hours?: number | null
  sleep_quality?: number | null
  energy_level?: number | null
  stress_level?: number | null
  activity_minutes?: number | null
  cravings?: string | null
  craving_type?: string | null
  eating_location?: string | null
  planned_eating_out?: boolean | null
  adherence_level?: number | null
  symptoms?: string | null
  adherence_notes?: string | null
}

export interface CheckInResponse {
  id: string
  check_date: string
  weight_kg: number | null
  waist_cm?: number | null
  hunger_level: number | null
  hunger_level_1_10?: number | null
  sleep_hours: number | null
  sleep_quality?: number | null
  energy_level?: number | null
  stress_level: number | null
  activity_minutes: number | null
  cravings?: string | null
  craving_type?: string | null
  eating_location?: string | null
  planned_eating_out?: boolean | null
  adherence_level?: number | null
  symptoms?: string | null
  adherence_notes: string | null
  adaptation_hint?: boolean
  human_review_recommended?: boolean
  safety_notes?: string[]
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
  avg_energy_level?: number | null
  avg_hunger_level_1_10?: number | null
  craving_summary?: string | null
  eating_location_summary?: string | null
  symptom_summary?: string | null
  adaptation_hint?: boolean
  human_review_recommended?: boolean
  behavior_wins: BehaviorWin[]
  logging_streak: number
  empty_state_message: string | null
}

export interface DataCompleteness {
  checkin_days: number
  expected_days: number
  checkin_pct: number
  weight_points: number
  waist_points: number
  meal_entries: number
  has_sleep_data: boolean
  has_stress_data: boolean
  has_hunger_data: boolean
  has_adherence_data: boolean
}

export interface WeeklyReportData {
  summary?: string | null
  date_range?: { start: string; end: string } | null
  weight_trend: WeightTrend | null
  waist_trend?: WeightTrend | null
  weight_series: number[]
  waist_series?: number[]
  avg_hunger: number | null
  avg_hunger_level_1_10?: number | null
  avg_sleep: number | null
  avg_sleep_quality?: number | null
  avg_energy_level?: number | null
  avg_stress: number | null
  avg_adherence_level?: number | null
  total_activity_minutes: number
  logging_days: number
  adherence_pct: number
  adherence_summary?: string | null
  risky_meals?: string[]
  risky_time_windows?: string[]
  craving_patterns?: string[]
  craving_summary?: string | null
  eating_location_summary?: string | null
  eating_out_pattern?: string | null
  symptom_summary?: string | null
  protein_quality?: string | null
  fiber_quality?: string | null
  hydration_quality?: string | null
  simple_sugar_quality?: string | null
  sleep_food_relationship?: string | null
  stress_food_relationship?: string | null
  behavior_pattern_summary?: string | null
  three_strengths?: string[]
  two_small_adjustments?: string[]
  next_week_small_goal?: string | null
  monitoring_notes?: string | null
  safety_notes?: string[]
  requires_human_review?: boolean
  generated_from_data_points?: Record<string, number>
  data_completeness?: DataCompleteness | null
  confidence_level?: string | null
  adaptation_hint?: boolean
  human_review_recommended?: boolean
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
