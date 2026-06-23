import { api } from './api'
import type {
  BehaviorRequest,
  BehaviorResponse,
  GoalRequest,
  GoalResponse,
  LifestyleRequest,
  LifestyleResponse,
  MedicalRequest,
  MedicalResponse,
  OnboardingCompleteResponse,
  OnboardingStatusResponse,
  PreferencesRequest,
  PreferencesResponse,
  ProfileRequest,
  ProfileResponse,
} from '@/types/onboarding'

const BASE = '/api/v1/onboarding'

export function getOnboardingStatus() {
  return api.get<OnboardingStatusResponse>(`${BASE}/status`, true)
}

export function submitGoals(body: GoalRequest) {
  return api.post<GoalResponse>(`${BASE}/goals`, body, true)
}

export function submitProfile(body: ProfileRequest) {
  return api.post<ProfileResponse>(`${BASE}/profile`, body, true)
}

export function submitMedical(body: MedicalRequest) {
  return api.post<MedicalResponse>(`${BASE}/medical`, body, true)
}

export function submitLifestyle(body: LifestyleRequest) {
  return api.post<LifestyleResponse>(`${BASE}/lifestyle`, body, true)
}

export function submitPreferences(body: PreferencesRequest) {
  return api.post<PreferencesResponse>(`${BASE}/preferences`, body, true)
}

export function submitBehavior(body: BehaviorRequest) {
  return api.post<BehaviorResponse>(`${BASE}/behavior`, body, true)
}

export function completeOnboarding() {
  return api.post<OnboardingCompleteResponse>(`${BASE}/complete`, {}, true)
}
