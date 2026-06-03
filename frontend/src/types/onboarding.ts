export type RiskLevel = 'low' | 'medium' | 'high' | 'clinical_review_required'

export type GoalType =
  | 'weight_loss'
  | 'weight_gain'
  | 'muscle_gain'
  | 'healthy_eating'
  | 'diabetes_support'
  | 'fatty_liver_support'
  | 'pcos_support'
  | 'digestive_support'
  | 'sports_nutrition'
  | 'pregnancy_breastfeeding_caution'
  | 'general_health_companion'

export const ALL_GOALS: GoalType[] = [
  'weight_loss',
  'weight_gain',
  'muscle_gain',
  'healthy_eating',
  'diabetes_support',
  'fatty_liver_support',
  'pcos_support',
  'digestive_support',
  'sports_nutrition',
  'pregnancy_breastfeeding_caution',
  'general_health_companion',
]

export interface OnboardingStatusResponse {
  user_id: string
  is_onboarded: boolean
  completed_steps: string[]
  next_step: string | null
  risk_level: string | null
  profile_exists: boolean
  medical_exists: boolean
  lifestyle_exists: boolean
  preferences_exists: boolean
  behavior_exists: boolean
}

export interface ProfileRequest {
  full_name: string
  gender: 'male' | 'female' | 'other' | 'prefer_not_to_say'
  age: number
  height_cm: number
  current_weight_kg: number
  target_weight_kg?: number | null
  waist_circumference_cm?: number | null
}

export interface ProfileResponse {
  id: string
  user_id: string
  full_name: string | null
  gender: string | null
  height_cm: number | null
  weight_kg: number | null
  target_weight_kg: number | null
  waist_cm: number | null
}

export interface MedicalRequest {
  diabetes: boolean
  kidney_disease: boolean
  liver_disease: boolean
  thyroid_issues: boolean
  high_blood_pressure: boolean
  high_cholesterol: boolean
  pcos: boolean
  pregnancy_breastfeeding: boolean
  eating_disorder_history: boolean
  bariatric_surgery: boolean
  medications: string[]
  allergies: string[]
  warning_symptoms: string[]
}

export interface MedicalResponse {
  flags: Array<{ condition_code: string; has_condition: boolean }>
  medications: string[]
  allergies: string[]
  warning_symptoms: string[]
  risk_level: RiskLevel
  risk_flags: string[]
  clinical_review_required: boolean
}

export interface LifestyleRequest {
  sleep_hours: number
  stress_level: number
  work_schedule: string
  activity_level: string
  exercise_days_per_week: number
  cooking_ability: number
  food_budget: string
  eating_out_frequency: string
  travel_frequency: string
}

export interface LifestyleResponse {
  id: string
  user_id: string
  sleep_hours: number | null
  stress_level: number | null
  work_schedule: string | null
  activity_level: string | null
  exercise_days_per_week: number | null
  cooking_ability: number | null
  food_budget: string | null
  eating_out_frequency: string | null
  travel_frequency: string | null
}

export interface PreferencesRequest {
  likes_iranian_food: boolean
  vegetarian: boolean
  vegan: boolean
  halal: boolean
  disliked_foods: string[]
  favorite_foods: string[]
  breakfast_habit: string
  rice_frequency: string
  bread_frequency: string
  sweets_frequency: string
  tea_frequency: string
  restaurant_frequency: string
}

export interface PreferencesResponse {
  id: string
  user_id: string
  likes_iranian_food: boolean
  vegetarian: boolean
  vegan: boolean
  halal: boolean
  disliked_foods: string[]
  favorite_foods: string[]
  breakfast_habit: string | null
  rice_frequency: string | null
  bread_frequency: string | null
  sweets_frequency: string | null
  tea_frequency: string | null
  restaurant_frequency: string | null
}

export interface BehaviorRequest {
  emotional_eating: boolean
  night_eating: boolean
  meal_skipping: boolean
  cravings: string[]
  binge_history: boolean
  diet_history: string
  previous_failures: string
  hunger_pattern: string
  motivation_level: number
}

export interface BehaviorResponse {
  id: string
  user_id: string
  emotional_eating: boolean
  night_eating: boolean
  meal_skipping: boolean
  cravings: string[]
  binge_history: boolean
  diet_history: string | null
  previous_failures: string | null
  hunger_pattern: string | null
  motivation_level: number | null
}

export interface OnboardingCompleteResponse {
  user_id: string
  is_onboarded: boolean
  risk_level: string
  clinical_review_required: boolean
  risk_flags: string[]
  completed_steps: string[]
  message: string
}
