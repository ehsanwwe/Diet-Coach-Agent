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
  description?: string | null
  calories_estimate?: number | null
  prep_time_minutes?: number | null
  tags?: string[]
  option_type?: 'best_goal_aligned' | 'fastest' | 'flexible' | 'general' | null
  household_portions?: string | null
  why_it_fits_goal?: string | null
  safety_note?: string | null
  substitutions?: string[]
}

export interface CoachingOption {
  title: string
  description?: string | null
  household_portions?: string | null
  why_it_helps?: string | null
  substitutions?: string[]
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
  current_goal?: string
  hunger_level_1_10?: number
  eaten_at?: string
}

export interface MealAnalysisResponse {
  meal_id: string | null
  quality_score: number | null
  analysis_summary: string
  likely_meal?: string | null
  uncertainties?: string[]
  protein: string
  fiber: string
  sugar: string
  balance: string
  portion: string
  protein_quality?: string | null
  fiber_vegetable_quality?: string | null
  carbohydrate_quality?: string | null
  fat_quality?: string | null
  simple_sugar_quality?: string | null
  portion_volume_assessment?: string | null
  satiety_assessment?: string | null
  likely_goal_effect?: string | null
  one_small_correction?: string | null
  next_meal_suggestion?: string | null
  no_extreme_compensation_note?: string | null
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
  current_place?: string
  location_context?: string
  last_meal_time?: string
  last_meal_summary?: string
  current_goal?: string
  hunger_level_1_10?: number
  cooking_access?: string
  budget_context?: string
  medical_constraints?: string
  user_preference_note?: string
}

export interface WhatToEatNowResponse {
  options: FoodOption[]
  best_goal_aligned_option?: FoodOption | null
  fastest_option?: FoodOption | null
  flexible_option?: FoodOption | null
  reasoning_summary: string
  warnings: string[]
  provider: string
  is_mock: boolean
}

export interface CravingSupportRequest {
  craving_food?: string | null
  craving_intensity_1_10?: number | null
  hunger_level_1_10?: number | null
  last_meal_time?: string | null
  last_meal_summary?: string | null
  sleep_quality?: number | null
  stress_level?: number | null
  emotion?: string | null
  current_place?: string | null
  available_foods?: string[]
  time_of_day?: string | null
  user_note?: string | null
}

export interface CravingSupportResponse {
  calming_message: string
  likely_triggers: string[]
  hunger_vs_craving_assessment?: string | null
  immediate_options: CoachingOption[]
  better_choice?: CoachingOption | null
  flexible_choice?: CoachingOption | null
  prevention_tip?: string | null
  follow_up_question?: string | null
  safety_notes: string[]
  requires_human_review: boolean
  provider: string
  is_mock: boolean
}

export interface SlipRecoveryRequest {
  what_happened?: string | null
  foods_eaten?: string[]
  approximate_amount?: string | null
  emotion_before?: string | null
  emotion_after?: string | null
  hunger_before_1_10?: number | null
  stress_level?: number | null
  sleep_quality?: number | null
  restriction_before_slip?: boolean | null
  last_meal_time?: string | null
  user_note?: string | null
}

export interface SlipRecoveryResponse {
  calming_message: string
  data_not_failure_message: string
  likely_trigger_questions: string[]
  pattern_hypothesis?: string | null
  one_small_adjustment?: string | null
  next_meal_plan?: string | null
  tomorrow_reset_note?: string | null
  no_extreme_compensation_note?: string | null
  safety_notes: string[]
  requires_human_review: boolean
  provider: string
  is_mock: boolean
}

export interface ContextGuidanceRequest {
  context_type: 'restaurant' | 'party' | 'travel' | 'work' | 'mixed'
  available_options?: string[]
  preferred_option?: string | null
  current_goal?: string | null
  hunger_level_1_10?: number | null
  meal_timing?: string | null
  budget_context?: string | null
  medical_constraints?: string | null
  user_note?: string | null
}

export interface ContextGuidanceResponse {
  best_available_choice?: string | null
  flexible_choice?: string | null
  portion_strategy?: string | null
  plate_balance_tip?: string | null
  drink_tip?: string | null
  dessert_or_snack_strategy?: string | null
  if_user_chooses_high_calorie_option?: string | null
  next_meal_adjustment?: string | null
  safety_notes: string[]
  requires_human_review: boolean
  provider: string
  is_mock: boolean
}

export interface AdaptPlanRequest {
  reason: string
  recent_hunger?: string | null
  recent_sleep?: string | null
  recent_stress?: string | null
  recent_adherence?: string | null
  notes?: string | null
}

export interface AdaptPlanResponse {
  plan_id?: string | null
  changes: string[]
  updated_guidelines?: DailyGuidelines | null
  warnings: string[]
  revision_applied: boolean
  revision_scope: 'none' | 'next_meal' | 'today' | 'remaining_day' | 'week' | 'guidance_only'
  revised_date?: string | null
  changed_items: string[]
  reason_for_changes?: string | null
  safety_notes: string[]
  requires_human_review: boolean
  fallback_reason?: string | null
  provider: string
  is_mock: boolean
}

// ─── Calendar types ───────────────────────────────────────────────────────────

export interface FoodItem {
  name: string
  amount: string | null
  unit: string | null
  calories_estimate: number | null
  protein_g?: number | null
  carbs_g?: number | null
  fat_g?: number | null
}

export interface DailyMacros {
  protein_g: number | null
  carbs_g: number | null
  fat_g: number | null
  fiber_g: number | null
}

export interface CalendarMeal {
  id: string
  meal_type: string
  title: string
  description: string | null
  portion_guidance: string | null
  alternatives: string[]
  preparation_notes: string | null
  meal_slot: string | null
  meal_order: number | null
  time_window_start: string | null
  time_window_end: string | null
  calories_estimate: number | null
  protein_g: number | null
  carbs_g: number | null
  fat_g: number | null
  food_items: FoodItem[]
  workout_relation: string | null
  rest_day_note: string | null
  drink_guidance: string | null
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
  diet_type: string | null
  diet_goal: string | null
  difficulty_level: string | null
  daily_calories: number | null
  daily_macros: DailyMacros | null
  day_type: string | null
  training_guidance: string | null
  sleep_wake_guidance: string | null
  wake_time: string | null
  sleep_time: string | null
  dinner_to_sleep_gap: string | null
  hydration_plan: string | null
  drinks_plan: string | null
  cheat_meal_guidance: string | null
  allowed_foods: string[]
  limited_foods: string[]
  forbidden_foods: string[]
  medical_warnings: string[]
  restaurant_party_travel_guidance: string | null
  supplements_vitamins_guidance: string | null
  progress_tracking_guidance: string | null
  adjustment_rules: string | null
  budget_tier: string | null
  budget_guidance: string | null
  shopping_notes: string | null
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
