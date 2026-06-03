import type { Dictionary } from './fa'

const en: Dictionary = {
  common: {
    appName: 'Diet Coach',
    loading: 'Loading...',
    error: 'Something went wrong',
    retry: 'Try again',
    back: 'Back',
    next: 'Next',
    save: 'Save',
    cancel: 'Cancel',
    confirm: 'Confirm',
    close: 'Close',
    yes: 'Yes',
    no: 'No',
    or: 'or',
  },
  splash: {
    tagline: 'Your Smart Nutrition Coach',
    subtitle: 'Daily health and nutrition guidance',
    description:
      'Get a personalized meal plan with your AI nutrition coach, rooted in your culture and health needs.',
    getStarted: 'Get Started',
    comingSoon: 'Coming Soon',
  },
  nav: {
    home: 'Home',
    chat: 'Chat',
    progress: 'Progress',
    settings: 'Settings',
  },
  language: {
    select: 'Select Language',
    fa: 'فارسی',
    en: 'English',
    ar: 'العربية',
    current: 'Current language',
    change: 'Change language',
  },
  errors: {
    notFound: 'Page not found',
    offline: 'No internet connection',
    generic: 'Something went wrong. Please try again.',
  },
  auth: {
    loginTitle: 'Sign in to Diet Coach',
    loginSubtitle: 'Enter your phone number to continue',
    phonePlaceholder: '09123456789',
    phoneLabel: 'Phone number',
    phoneError: 'Enter a valid phone number',
    sendOtp: 'Send verification code',
    otpTitle: 'Verification code',
    otpSubtitle: 'Enter the 6-digit code we sent you',
    otpLabel: 'Verification code',
    otpPlaceholder: '123456',
    otpError: 'Code must be 6 digits',
    otpExpired: 'Code expired. Please request a new one.',
    verify: 'Verify',
    resend: 'Resend code',
    resendIn: 'Resend in {seconds}s',
    invalidOtp: 'Incorrect code. Please try again.',
    loginSuccess: 'Signed in successfully',
    logoutSuccess: 'Signed out successfully',
    networkError: 'Network error. Please try again.',
  },
}

export default en
