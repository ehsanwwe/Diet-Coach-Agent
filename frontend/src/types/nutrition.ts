export interface DailyGuidelines {
  calories: number | null
  protein_g: number | null
  carbs_g: number | null
  fat_g: number | null
  fiber_g: number | null
  water_liters: number | null
  notes: string | null
}

export interface MealItem {
  id: string | null
  meal_time: string
  name: string
  description: string | null
  calories_estimate: number | null
  protein_g: number | null
  carbs_g: number | null
  fat_g: number | null
  notes: string | null
  order_index: number
}

export interface FoodOption {
  name: string
  description: string | null
  calories_estimate: number | null
  prep_time_minutes: number | null
  tags: string[]
}

export interface NutritionProfileResponse {
  user_id: string
  onboarding_complete: boolean
  risk_level: string
  clinical_review_required: boolean
  profile: {
    height_cm: number | null
    weight_kg: number | null
    target_weight_kg: number | null
    gender: string | null
    age: number | null
    goal_type: string | null
  } | null
  missing_sections: string[]
}

export interface NutritionPlanResponse {
  has_plan: boolean
  plan_id: string | null
  status: string | null
  risk_level: string | null
  summary: string | null
  daily_guidelines: DailyGuidelines | null
  meals: MealItem[]
  warnings: string[]
  provider: string | null
  is_mock: boolean
  generated_at: string | null
}

export interface MealAnalyzeRequest {
  meal_text: string
  meal_time: 'breakfast' | 'lunch' | 'dinner' | 'snack' | 'unknown'
  context?: string
}

export interface MealAnalysisResponse {
  meal_id: string | null
  quality_score: number | null
  analysis_summary: string
  protein: string
  fiber: string
  sugar: string
  balance: string
  portion: string
  suggestions: string[]
  warnings: string[]
  provider: string
  is_mock: boolean
}

export interface WhatToEatNowRequest {
  available_foods: string[]
  hunger_level: 'low' | 'medium' | 'high'
  meal_context?: string
  time_available_minutes?: number
}

export interface WhatToEatNowResponse {
  options: FoodOption[]
  reasoning_summary: string
  warnings: string[]
  provider: string
  is_mock: boolean
}

// ─── Calendar types ───────────────────────────────────────────────────────────

export interface CalendarMeal {
  id: string
  meal_type: string
  title: string
  description: string | null
  portion_guidance: string | null
  alternatives: string[]
  preparation_notes: string | null
}

export interface PlanDay {
  id: string
  plan_date: string
  day_index: number
  title: string
  summary: string | null
  hydration_goal: string | null
  notes: string | null
  warnings: string[]
  meals: CalendarMeal[]
}

export interface CoverageInfo {
  planned_days_count: number
  missing_days_count: number
  next_unplanned_date: string | null
}

export interface RenewalStatus {
  should_prompt_next_week: boolean
  prompt_level: 'none' | 'info' | 'warning'
  current_week_day_number: number | null
  next_week_start_date: string | null
  next_week_end_date: string | null
}

export interface CalendarResponse {
  calendar_id: string | null
  locale: string
  start_date: string | null
  end_date: string | null
  days: PlanDay[]
  coverage: CoverageInfo
  renewal_status: RenewalStatus
}

export interface GenerateWeekResponse {
  locale: string
  generated_days: number
  skipped_days: number
  days: PlanDay[]
}
