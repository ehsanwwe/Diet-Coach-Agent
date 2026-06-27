/**
 * Dictionary interface + Persian (Farsi) translations.
 * fa.ts is the source-of-truth for the Dictionary shape.
 * All other dictionary files must conform to this interface.
 */

export interface Dictionary {
  audio: {
    // Chat section labels
    chatSectionTitle: string
    chatSectionSubtitle: string
    // Text input
    textPlaceholder: string
    sendText: string
    // Recording controls
    startRecording: string
    stopRecording: string
    cancelRecording: string
    sendAudio: string
    // States
    recording: string
    processing: string
    uploading: string
    // Errors / feedback
    permissionDenied: string
    unsupportedBrowser: string
    noMicrophone: string
    uploadFailed: string
    uploadSuccess: string
    // Preview
    audioPreview: string
    recordingDuration: string
    labelPlay: string
    labelPause: string
    labelReset: string
    // History
    historyEmpty: string
    transcriptionPending: string
    transcriptionNotConfigured: string
  }
  common: {
    appName: string
    loading: string
    error: string
    retry: string
    back: string
    next: string
    save: string
    cancel: string
    confirm: string
    close: string
    yes: string
    no: string
    or: string
  }
  splash: {
    tagline: string
    subtitle: string
    description: string
    getStarted: string
    comingSoon: string
  }
  nav: {
    home: string
    chat: string
    progress: string
    settings: string
  }
  language: {
    select: string
    fa: string
    en: string
    ar: string
    current: string
    change: string
    backToSettings: string
  }
  errors: {
    notFound: string
    offline: string
    generic: string
  }
  settings: {
    title: string
    languageSection: string
    profileSection: string
    accountSection: string
    currentLanguage: string
    changeLanguage: string
    displayName: string
    phoneNumber: string
    logoutBtn: string
    logoutConfirm: string
    logoutCancel: string
    appVersion: string
  }
  auth: {
    loginTitle: string
    loginSubtitle: string
    phonePlaceholder: string
    phoneLabel: string
    phoneError: string
    sendOtp: string
    otpTitle: string
    otpSubtitle: string
    otpLabel: string
    otpPlaceholder: string
    otpError: string
    otpExpired: string
    verify: string
    resend: string
    resendIn: string
    invalidOtp: string
    loginSuccess: string
    logoutSuccess: string
    networkError: string
    countryLabel: string
    countrySearch: string
    phoneInvalidForCountry: string
  }
  onboarding: {
    // Step labels for progress bar
    step1: string
    step2: string
    step3: string
    step4: string
    step5: string
    step6: string
    step7: string
    // Navigation
    back: string
    next: string
    complete: string
    saving: string
    optional: string
    // ── Profile step ──────────────────────────────────────────
    profileTitle: string
    profileSubtitle: string
    fullName: string
    fullNamePlaceholder: string
    gender: string
    genderMale: string
    genderFemale: string
    genderOther: string
    genderPreferNotToSay: string
    age: string
    agePlaceholder: string
    heightCm: string
    heightPlaceholder: string
    currentWeight: string
    weightPlaceholder: string
    targetWeight: string
    targetWeightPlaceholder: string
    waist: string
    waistPlaceholder: string
    profileMoreDetails: string
    wrist: string
    wristPlaceholder: string
    wristRange: string
    thigh: string
    thighPlaceholder: string
    thighRange: string
    // Profile validation
    nameRequired: string
    nameMin: string
    genderRequired: string
    ageRange: string
    heightRequired: string
    heightRange: string
    weightRequired: string
    weightRange: string
    targetWeightRange: string
    waistRange: string
    // ── Goal step ─────────────────────────────────────────────
    goalTitle: string
    goalSubtitle: string
    goalSelectPrompt: string
    goalWeightLoss: string
    goalWeightGain: string
    goalMuscleGain: string
    goalHealthyEating: string
    goalDiabetes: string
    goalFattyLiver: string
    goalPcos: string
    goalDigestive: string
    goalSports: string
    goalPregnancy: string
    goalGeneral: string
    // ── Medical step ──────────────────────────────────────────
    medicalTitle: string
    medicalSubtitle: string
    medicalSafetyNotice: string
    medConditions: string
    medDiabetes: string
    medKidney: string
    medLiver: string
    medThyroid: string
    medBloodPressure: string
    medCholesterol: string
    medPcos: string
    medPregnancy: string
    medEatingDisorder: string
    medBariatric: string
    medMedications: string
    medMedicationsPlaceholder: string
    medAllergies: string
    medAllergiesPlaceholder: string
    medHasAllergy: string
    medAllergyNo: string
    medAllergyYes: string
    medAllergyPresetGluten: string
    medAllergyPresetLactose: string
    medAllergyPresetPeanut: string
    medAllergyPresetEggplant: string
    medWarningSymptoms: string
    medSymChestPain: string
    medSymDizziness: string
    medSymFatigue: string
    medSymWeightLoss: string
    medSymFainting: string
    medAddItem: string
    medRemoveItem: string
    // ── Lifestyle step ────────────────────────────────────────
    lifestyleTitle: string
    lifestyleSubtitle: string
    lifeSleep: string
    lifeSleepUnit: string
    lifeStress: string
    lifeStressLow: string
    lifeStressHigh: string
    lifeWork: string
    lifeWorkRegular: string
    lifeWorkShift: string
    lifeWorkFreelance: string
    lifeWorkStudent: string
    lifeWorkHomemaker: string
    lifeWorkRetired: string
    lifeWorkOther: string
    lifeActivity: string
    lifeActSedentary: string
    lifeActLight: string
    lifeActModerate: string
    lifeActActive: string
    lifeActVeryActive: string
    lifeExercise: string
    lifeExerciseUnit: string
    lifeCooking: string
    lifeCookingLow: string
    lifeCookingHigh: string
    lifeBudget: string
    lifeBudgetLow: string
    lifeBudgetMedium: string
    lifeBudgetHigh: string
    lifeEatingOut: string
    lifeTravel: string
    freqNever: string
    freqRarely: string
    freqFewWeekly: string
    freqDaily: string
    freqSeveralDaily: string
    // Lifestyle validation
    lifeRequired: string
    sleepRange: string
    stressRange: string
    exerciseRange: string
    outOf10: string
    daysUnit: string
    // ── Preferences step ──────────────────────────────────────
    prefTitle: string
    prefSubtitle: string
    prefIranianFood: string
    prefVegetarian: string
    prefVegan: string
    prefHalal: string
    prefDisliked: string
    prefDislikedPlaceholder: string
    prefFavorite: string
    prefFavoritePlaceholder: string
    prefBreakfast: string
    prefBreakfastSkip: string
    prefBreakfastLight: string
    prefBreakfastFull: string
    prefBreakfastVaries: string
    prefRice: string
    prefBread: string
    prefSweets: string
    prefTea: string
    prefRestaurant: string
    consumNever: string
    consumRarely: string
    consumFewWeekly: string
    consumDaily: string
    consumSeveralDaily: string
    prefAddFood: string
    // ── Behavior step ─────────────────────────────────────────
    behavTitle: string
    behavSubtitle: string
    behavEmotional: string
    behavNight: string
    behavSkipping: string
    behavBinge: string
    behavCravings: string
    behavCravSweet: string
    behavCravSalty: string
    behavCravFried: string
    behavCravBread: string
    behavCravChocolate: string
    behavCravOther: string
    behavCravOtherPlaceholder: string
    behavDietHistory: string
    behavDietHistoryPlaceholder: string
    behavPreviousFails: string
    behavPreviousFailsPlaceholder: string
    behavHunger: string
    behavHungerHint: string
    behavHungerMorning: string
    behavHungerAfternoon: string
    behavHungerEvening: string
    behavHungerNight: string
    behavHungerRandom: string
    behavMotivation: string
    behavMotivationLow: string
    behavMotivationHigh: string
    behavAddCraving: string
    // ── Final step ────────────────────────────────────────────
    finalTitle: string
    finalSubtitle: string
    finalVideoLabel: string
    finalVideoComingSoon: string
    finalVideoLoadError: string
    finalWatchFirst: string
    finalMarkWatched: string
    finalWatchedBadge: string
    finalComplete: string
    finalCompleting: string
    // ── Clinical review notice ────────────────────────────────
    clinicalTitle: string
    clinicalMessage: string
    clinicalDisclaimer: string
    // ── Completion screen ─────────────────────────────────────
    doneTitle: string
    doneMessage: string
    doneClinicalTitle: string
    doneClinicalMessage: string
    doneContinue: string
    // ── Errors ────────────────────────────────────────────────
    errApiError: string
    errProfileRequired: string
    errUnauthorized: string
    errSubmitFailed: string
    errLoadFailed: string
  }
  dashboard: {
    title: string
    greetingGeneric: string
    greetingName: string
    subtitle: string
    quickActionsTitle: string
    generatePlan: string
    analyzeMeal: string
    whatToEatNow: string
    openChat: string
    noPlanTitle: string
    noPlanDesc: string
    noPlanCta: string
    currentPlanLabel: string
    noOnboarding: string
    noOnboardingCta: string
    riskLow: string
    riskMedium: string
    riskHigh: string
    riskClinical: string
    providerMock: string
    providerLive: string
    clinicalAlertTitle: string
    clinicalAlertDesc: string
    behaviorGuide: string
    calendarPlanDesc: string
  }
  plan: {
    title: string
    subtitle: string
    generateBtn: string
    regenerateBtn: string
    generating: string
    noPlanTitle: string
    noPlanDesc: string
    noPlanCta: string
    generatedAt: string
    summary: string
    dailyGuidelinesTitle: string
    calories: string
    protein: string
    carbs: string
    fat: string
    fiber: string
    water: string
    notes: string
    mealsTitle: string
    breakfast: string
    lunch: string
    dinner: string
    snack: string
    unknown: string
    warnings: string
    mockBadge: string
    liveBadge: string
    unitGrams: string
    unitLiters: string
    unitKcal: string
    unitMin: string
  }
  mealAnalysis: {
    title: string
    subtitle: string
    mealDescLabel: string
    mealDescPlaceholder: string
    mealTimeLabel: string
    contextLabel: string
    contextPlaceholder: string
    analyzeBtn: string
    analyzing: string
    newAnalysisBtn: string
    resultTitle: string
    qualityScore: string
    outOf10: string
    protein: string
    fiber: string
    sugar: string
    balance: string
    portion: string
    suggestionsTitle: string
    warningsTitle: string
    noWarnings: string
    breakfast: string
    lunch: string
    dinner: string
    snack: string
    unknown: string
    mockBadge: string
    likelyMeal: string
    uncertainties: string
    nutritionQualityTitle: string
    proteinQuality: string
    fiberVegetableQuality: string
    carbohydrateQuality: string
    fatQuality: string
    simpleSugarQuality: string
    portionVolumeAssessment: string
    satietyAssessment: string
    goalEffect: string
    smallCorrection: string
    nextMealSuggestion: string
    noExtremeCompensation: string
  }
  whatToEat: {
    title: string
    subtitle: string
    availableFoodsLabel: string
    availableFoodsPlaceholder: string
    availableFoodsHint: string
    removeFoodAriaLabel: string
    addFood: string
    hungerLevelLabel: string
    hungerLow: string
    hungerMedium: string
    hungerHigh: string
    mealContextLabel: string
    mealContextPlaceholder: string
    timeAvailableLabel: string
    timeAvailablePlaceholder: string
    askBtn: string
    asking: string
    optionsTitle: string
    calories: string
    prepTime: string
    reasoningTitle: string
    warningsTitle: string
    tryAgainBtn: string
    mockBadge: string
    optionalDetails: string
    currentPlaceLabel: string
    currentPlacePlaceholder: string
    lastMealLabel: string
    lastMealPlaceholder: string
    hungerScaleLabel: string
    cookingAccessLabel: string
    cookingAccessPlaceholder: string
    budgetContextLabel: string
    budgetContextPlaceholder: string
    preferenceNoteLabel: string
    preferenceNotePlaceholder: string
    bestAligned: string
    fastest: string
    flexible: string
    householdPortions: string
    whyFitsGoal: string
    substitutions: string
    safetyNote: string
  }
  behaviorCoaching: {
    title: string
    subtitle: string
    cravingTab: string
    slipTab: string
    contextTab: string
    cravingFoodLabel: string
    cravingFoodPlaceholder: string
    cravingIntensityLabel: string
    hungerScaleLabel: string
    stressLabel: string
    sleepQualityLabel: string
    currentPlaceLabel: string
    timeOfDayLabel: string
    noteLabel: string
    notePlaceholder: string
    submitCraving: string
    submittingCraving: string
    slipWhatHappenedLabel: string
    slipWhatHappenedPlaceholder: string
    slipFoodsLabel: string
    slipFoodsPlaceholder: string
    slipAmountLabel: string
    slipAmountPlaceholder: string
    submitSlip: string
    submittingSlip: string
    contextTypeLabel: string
    contextRestaurant: string
    contextParty: string
    contextTravel: string
    contextWork: string
    contextMixed: string
    availableOptionsLabel: string
    availableOptionsPlaceholder: string
    preferredOptionLabel: string
    preferredOptionPlaceholder: string
    submitContext: string
    submittingContext: string
    calmingMessage: string
    likelyTriggers: string
    hungerVsCraving: string
    immediateOptions: string
    betterChoice: string
    flexibleChoice: string
    preventionTip: string
    followUpQuestion: string
    dataNotFailure: string
    triggerQuestions: string
    patternHypothesis: string
    oneSmallAdjustment: string
    nextMealPlan: string
    tomorrowReset: string
    noExtremeCompensation: string
    bestAvailableChoice: string
    portionStrategy: string
    plateBalanceTip: string
    drinkTip: string
    dessertStrategy: string
    highCalorieChoice: string
    nextMealAdjustment: string
    safetyNotes: string
    humanReview: string
    error: string
    scaleError10: string
    scaleError5: string
  }
  adaptPlan: {
    revisionApplied: string
    revisionNotApplied: string
    revisionScope: string
    revisedDate: string
    changedItems: string
    reasonForChanges: string
    safetyNotes: string
    humanReview: string
    fallbackReason: string
  }
  companionChat: {
    title: string
    subtitle: string
    startChat: string
    inputPlaceholder: string
    sendBtn: string
    sending: string
    emptyTitle: string
    emptyDesc: string
    loadError: string
    sendError: string
    mockBadge: string
    you: string
    coach: string
    typingIndicator: string
    clearMemory: string
    clearMemoryConfirmTitle: string
    clearMemoryConfirm: string
    clearMemoryCancel: string
    memoryCleared: string
  }
  safety: {
    clinicalTitle: string
    clinicalMessage: string
    clinicalDisclaimer: string
    highRiskTitle: string
    highRiskMessage: string
    notADoctorNote: string
  }
  calendar: {
    title: string
    subtitle: string
    noPlanTitle: string
    noPlanDesc: string
    generateInitialWeek: string
    generateNextWeek: string
    nextWeekPromptTitle: string
    nextWeekPromptDescription: string
    nextWeekPromptCta: string
    plannedDays: string
    missingDays: string
    nextUnplannedDate: string
    breakfast: string
    lunch: string
    dinner: string
    snack: string
    today: string
    day: string
    week: string
    planDate: string
    generationLoading: string
    generationSuccess: string
    generationError: string
    warnings: string
    hydrationGoal: string
    notes: string
    alternatives: string
    prepNotes: string
    portionGuidance: string
    dietType: string
    difficulty: string
    dailyCalories: string
    protein: string
    carbs: string
    fat: string
    fiber: string
    dayTypeTraining: string
    dayTypeRest: string
    dayTypeLight: string
    trainingGuidance: string
    sleepWakeGuidance: string
    hydrationPlan: string
    cheatMealGuidance: string
    medicalWarnings: string
    mealTimeWindow: string
    mealCalories: string
    morningSnack: string
    afternoonSnack: string
    eveningSnack: string
    preWorkout: string
    postWorkout: string
    drinkGuidance: string
    foodItems: string
  }
  progress: {
    title: string
    subtitle: string
    tabSummary: string
    tabWeekly: string
    checkInTitle: string
    checkInSubtitle: string
    checkInWeight: string
    checkInWeightUnit: string
    checkInHunger: string
    checkInSleep: string
    checkInSleepUnit: string
    checkInStress: string
    checkInActivity: string
    checkInActivityUnit: string
    checkInNotes: string
    checkInNotesPlaceholder: string
    checkInSubmit: string
    checkInSubmitting: string
    checkInSuccess: string
    checkInAlreadyToday: string
    checkInTodayMissing: string
    summaryTitle: string
    latestWeight: string
    weightTrend: string
    behaviourWinsTitle: string
    loggingStreak: string
    loggingStreakDays: string
    winSleep: string
    winActivity: string
    winLogging: string
    winLowStress: string
    winLowHunger: string
    winHydration: string
    winProtein: string
    winFiber: string
    winNotTracked: string
    weeklyTitle: string
    weeklyPeriod: string
    weeklyAdherence: string
    weeklyAvgSleep: string
    weeklyAvgStress: string
    weeklyAvgHunger: string
    weeklyTotalActivity: string
    weeklyWeightDelta: string
    weeklySleepStressNote: string
    weeklyFocusTitle: string
    weeklyLoggingDays: string
    emptyTitle: string
    emptyDesc: string
    emptyCheckinCta: string
    emptyWeeklyTitle: string
    emptyWeeklyDesc: string
    errSubmitFailed: string
    errLoadFailed: string
    unitKg: string
    unitHours: string
    unitMinutes: string
    unitPercent: string
    checkInWaist: string
    checkInWaistUnit: string
    checkInHunger10: string
    checkInSleepQuality: string
    checkInEnergy: string
    checkInCravings: string
    checkInCravingsPlaceholder: string
    checkInCravingType: string
    checkInCravingTypePlaceholder: string
    checkInEatingLocation: string
    checkInEatingLocationPlaceholder: string
    checkInPlannedEatingOut: string
    checkInAdherence: string
    checkInSymptoms: string
    checkInSymptomsPlaceholder: string
    weeklySummaryTitle: string
    weeklyWaistDelta: string
    weeklyAdherenceSummary: string
    weeklyRiskyMeals: string
    weeklyRiskyWindows: string
    weeklyCravingPatterns: string
    weeklyQualityTitle: string
    weeklyProteinQuality: string
    weeklyFiberQuality: string
    weeklyHydrationQuality: string
    weeklySimpleSugarQuality: string
    weeklySleepFood: string
    weeklyStressFood: string
    weeklyEatingOut: string
    weeklyBehaviorPattern: string
    weeklyStrengths: string
    weeklyAdjustments: string
    weeklyNextGoal: string
    weeklyMonitoringNotes: string
    weeklySafetyNotes: string
    weeklyHumanReview: string
    weeklyConfidence: string
  }
}

const fa: Dictionary = {
  audio: {
    chatSectionTitle: 'گفتگوی عادت‌سازی',
    chatSectionSubtitle: 'سوالی درباره برنامه غذایی دارید؟ پیام دهید یا صدای خود را ارسال کنید.',
    textPlaceholder: 'پیام بنویسید...',
    sendText: 'ارسال',
    startRecording: 'شروع ضبط صدا',
    stopRecording: 'توقف ضبط',
    cancelRecording: 'لغو',
    sendAudio: 'ارسال صدا',
    recording: 'در حال ضبط',
    processing: 'در حال پردازش',
    uploading: 'در حال بارگذاری...',
    permissionDenied: 'دسترسی به میکروفون رد شد. لطفاً در تنظیمات مرورگر اجازه دهید.',
    unsupportedBrowser: 'مرورگر شما از ضبط صدا پشتیبانی نمی‌کند. می‌توانید پیام متنی بفرستید.',
    noMicrophone: 'میکروفونی یافت نشد.',
    uploadFailed: 'ارسال صدا ناموفق بود. دوباره تلاش کنید.',
    uploadSuccess: 'صدا با موفقیت ارسال شد',
    audioPreview: 'پیش‌نمایش صدا',
    recordingDuration: 'مدت ضبط',
    labelPlay: 'پخش',
    labelPause: 'مکث',
    labelReset: 'بازنشانی',
    historyEmpty: 'هنوز پیامی ارسال نشده. اولین پیام را بفرستید!',
    transcriptionPending: 'در انتظار رونویسی',
    transcriptionNotConfigured: 'صدا ذخیره شد',
  },
  common: {
    appName: 'کالریا',
    loading: 'در حال بارگذاری...',
    error: 'خطایی رخ داد',
    retry: 'تلاش مجدد',
    back: 'بازگشت',
    next: 'بعدی',
    save: 'ذخیره',
    cancel: 'لغو',
    confirm: 'تأیید',
    close: 'بستن',
    yes: 'بله',
    no: 'خیر',
    or: 'یا',
  },
  splash: {
    tagline: 'مربی هوشمند تغذیه شما',
    subtitle: 'راهنمای روزانه سلامت و تغذیه',
    description:
      'با مربی تغذیه هوشمند، برنامه غذایی شخصی‌سازی‌شده بر اساس فرهنگ غذایی ایرانی دریافت کنید.',
    getStarted: 'شروع کنید',
    comingSoon: 'به زودی',
  },
  nav: {
    home: 'خانه',
    chat: 'گفتگو',
    progress: 'پیشرفت',
    settings: 'تنظیمات',
  },
  language: {
    select: 'انتخاب زبان',
    fa: 'فارسی',
    en: 'English',
    ar: 'العربية',
    current: 'زبان فعلی',
    change: 'تغییر زبان',
    backToSettings: 'بازگشت به تنظیمات',
  },
  errors: {
    notFound: 'صفحه مورد نظر یافت نشد',
    offline: 'اتصال اینترنت برقرار نیست',
    generic: 'مشکلی پیش آمد. لطفاً دوباره تلاش کنید.',
  },
  settings: {
    title: 'تنظیمات',
    languageSection: 'زبان',
    profileSection: 'پروفایل',
    accountSection: 'حساب کاربری',
    currentLanguage: 'زبان فعلی',
    changeLanguage: 'تغییر زبان',
    displayName: 'نام شما',
    phoneNumber: 'شماره موبایل',
    logoutBtn: 'خروج از حساب',
    logoutConfirm: 'آیا مطمئن هستید که می‌خواهید خارج شوید؟',
    logoutCancel: 'ماندن',
    appVersion: 'نسخه برنامه',
  },
  auth: {
    loginTitle: 'ورود به مربی تغذیه',
    loginSubtitle: 'شماره موبایل خود را وارد کنید',
    phonePlaceholder: '۰۹۱۲۳۴۵۶۷۸۹',
    phoneLabel: 'شماره موبایل',
    phoneError: 'شماره موبایل معتبر نیست',
    sendOtp: 'ارسال کد تأیید',
    otpTitle: 'کد تأیید',
    otpSubtitle: 'کد ۶ رقمی ارسال شده را وارد کنید',
    otpLabel: 'کد تأیید',
    otpPlaceholder: '۱۲۳۴۵۶',
    otpError: 'کد باید ۶ رقم باشد',
    otpExpired: 'کد منقضی شده. مجدداً درخواست دهید.',
    verify: 'تأیید',
    resend: 'ارسال مجدد کد',
    resendIn: 'ارسال مجدد تا {seconds} ثانیه',
    invalidOtp: 'کد وارد شده اشتباه است',
    loginSuccess: 'با موفقیت وارد شدید',
    logoutSuccess: 'از حساب خارج شدید',
    networkError: 'خطای شبکه. لطفاً دوباره تلاش کنید.',
    countryLabel: 'کشور',
    countrySearch: 'جستجوی کشور...',
    phoneInvalidForCountry: 'شماره موبایل برای این کشور معتبر نیست',
  },
  onboarding: {
    step1: 'اطلاعات پایه',
    step2: 'هدف اصلی',
    step3: 'وضعیت سلامت',
    step4: 'سبک زندگی',
    step5: 'ترجیحات غذایی',
    step6: 'عادات غذایی',
    step7: 'تکمیل',
    back: 'بازگشت',
    next: 'بعدی',
    complete: 'تکمیل ثبت‌نام',
    saving: 'در حال ذخیره...',
    optional: '(اختیاری)',
    // Profile
    profileTitle: 'اطلاعات پایه',
    profileSubtitle: 'برای شروع، اطلاعات اولیه خود را وارد کنید.',
    fullName: 'نام کامل',
    fullNamePlaceholder: 'مثال: علی احمدی',
    gender: 'جنسیت',
    genderMale: 'مرد',
    genderFemale: 'زن',
    genderOther: 'سایر',
    genderPreferNotToSay: 'ترجیح می‌دهم نگویم',
    age: 'سن',
    agePlaceholder: '۲۵',
    heightCm: 'قد (سانتی‌متر)',
    heightPlaceholder: '۱۷۵',
    currentWeight: 'وزن فعلی (کیلوگرم)',
    weightPlaceholder: '۷۰',
    targetWeight: 'وزن هدف (کیلوگرم)',
    targetWeightPlaceholder: '۶۵',
    waist: 'دور کمر (سانتی‌متر)',
    waistPlaceholder: '۸۰',
    profileMoreDetails: 'جزئیات بیشتر (اختیاری)',
    wrist: 'دور مچ (سانتی‌متر)',
    wristPlaceholder: '۱۷',
    wristRange: 'دور مچ باید بین ۱۰ و ۳۰ سانتی‌متر باشد',
    thigh: 'دور ران (سانتی‌متر)',
    thighPlaceholder: '۵۵',
    thighRange: 'دور ران باید بین ۳۰ و ۱۰۰ سانتی‌متر باشد',
    nameRequired: 'نام الزامی است',
    nameMin: 'نام باید حداقل ۲ کاراکتر باشد',
    genderRequired: 'انتخاب جنسیت الزامی است',
    ageRange: 'سن باید بین ۱۰ و ۱۲۰ سال باشد',
    heightRequired: 'قد الزامی است',
    heightRange: 'قد باید بین ۱۰۰ و ۲۵۰ سانتی‌متر باشد',
    weightRequired: 'وزن فعلی الزامی است',
    weightRange: 'وزن باید بین ۲۰ و ۳۰۰ کیلوگرم باشد',
    targetWeightRange: 'وزن هدف باید بین ۲۰ و ۳۰۰ کیلوگرم باشد',
    waistRange: 'دور کمر باید بین ۴۰ و ۲۰۰ سانتی‌متر باشد',
    // Goal
    goalTitle: 'اهداف شما چیست؟',
    goalSubtitle: 'یک یا چند هدف انتخاب کنید تا برنامه شما بر اساس آن‌ها تنظیم شود.',
    goalSelectPrompt: 'لطفاً حداقل یک گزینه انتخاب کنید',
    goalWeightLoss: 'کاهش وزن',
    goalWeightGain: 'افزایش وزن',
    goalMuscleGain: 'عضله‌سازی',
    goalHealthyEating: 'تغذیه سالم',
    goalDiabetes: 'کنترل دیابت',
    goalFattyLiver: 'کبد چرب',
    goalPcos: 'سندرم تخمدان پلی‌کیستیک',
    goalDigestive: 'بهبود گوارش',
    goalSports: 'تغذیه ورزشی',
    goalPregnancy: 'بارداری و شیردهی',
    goalGeneral: 'سبک زندگی سالم',
    // Medical
    medicalTitle: 'وضعیت سلامت',
    medicalSubtitle: 'این اطلاعات برای ارائه توصیه‌های ایمن استفاده می‌شود.',
    medicalSafetyNotice: 'این اپلیکیشن جایگزین پزشک یا متخصص تغذیه نیست. اطلاعات شما محرمانه است.',
    medConditions: 'بیماری‌های زمینه‌ای',
    medDiabetes: 'دیابت',
    medKidney: 'بیماری کلیوی',
    medLiver: 'بیماری کبدی',
    medThyroid: 'مشکلات تیروئید',
    medBloodPressure: 'فشار خون بالا',
    medCholesterol: 'کلسترول بالا',
    medPcos: 'سندرم تخمدان پلی‌کیستیک (PCOS)',
    medPregnancy: 'بارداری یا شیردهی',
    medEatingDisorder: 'سابقه اختلال خوردن',
    medBariatric: 'سابقه جراحی چاقی',
    medMedications: 'داروهای مصرفی',
    medMedicationsPlaceholder: 'داروی مصرفی را وارد کنید',
    medAllergies: 'آلرژی‌ها و عدم تحمل غذایی',
    medAllergiesPlaceholder: 'مثال: گوجه‌فرنگی، آناناس...',
    medHasAllergy: 'آیا به چیزی حساسیت دارید؟',
    medAllergyNo: 'خیر',
    medAllergyYes: 'بله',
    medAllergyPresetGluten: 'گلوتن',
    medAllergyPresetLactose: 'لاکتوز',
    medAllergyPresetPeanut: 'بادام زمینی',
    medAllergyPresetEggplant: 'بادمجان',
    medWarningSymptoms: 'علائم هشداردهنده (اگر دارید انتخاب کنید)',
    medSymChestPain: 'درد قفسه سینه',
    medSymDizziness: 'سرگیجه شدید',
    medSymFatigue: 'خستگی مفرط',
    medSymWeightLoss: 'کاهش وزن ناگهانی بدون دلیل',
    medSymFainting: 'غش یا از حال رفتن',
    medAddItem: 'افزودن',
    medRemoveItem: 'حذف',
    // Lifestyle
    lifestyleTitle: 'سبک زندگی',
    lifestyleSubtitle: 'برنامه شما بر اساس روتین روزانه‌تان تنظیم می‌شود.',
    lifeSleep: 'میانگین ساعات خواب شبانه',
    lifeSleepUnit: 'ساعت',
    lifeStress: 'سطح استرس روزانه',
    lifeStressLow: 'بدون استرس',
    lifeStressHigh: 'استرس شدید',
    lifeWork: 'نوع برنامه کاری',
    lifeWorkRegular: 'ادارات (۹ تا ۵)',
    lifeWorkShift: 'شیفتی',
    lifeWorkFreelance: 'آزاد / دورکاری',
    lifeWorkStudent: 'دانشجو',
    lifeWorkHomemaker: 'خانه‌دار',
    lifeWorkRetired: 'بازنشسته',
    lifeWorkOther: 'سایر',
    lifeActivity: 'سطح فعالیت بدنی',
    lifeActSedentary: 'کم‌تحرک (بدون ورزش)',
    lifeActLight: 'سبک (۱-۳ روز در هفته)',
    lifeActModerate: 'متوسط (۳-۵ روز در هفته)',
    lifeActActive: 'فعال (۶-۷ روز در هفته)',
    lifeActVeryActive: 'بسیار فعال (ورزش حرفه‌ای)',
    lifeExercise: 'تعداد روزهای ورزش در هفته',
    lifeExerciseUnit: 'روز در هفته',
    lifeCooking: 'مهارت آشپزی',
    lifeCookingLow: 'مبتدی',
    lifeCookingHigh: 'حرفه‌ای',
    lifeBudget: 'بودجه غذایی ماهانه',
    lifeBudgetLow: 'کم (اقتصادی)',
    lifeBudgetMedium: 'متوسط',
    lifeBudgetHigh: 'بالا (پریمیوم)',
    lifeEatingOut: 'تعداد دفعات رستوران رفتن در هفته',
    lifeTravel: 'تعداد دفعات مسافرت در ماه',
    freqNever: 'هرگز',
    freqRarely: 'به ندرت',
    freqFewWeekly: 'چند بار در هفته',
    freqDaily: 'روزانه',
    freqSeveralDaily: 'چندین بار در روز',
    lifeRequired: 'این فیلد الزامی است',
    sleepRange: 'ساعات خواب باید بین ۰ و ۲۴ باشد',
    stressRange: 'سطح استرس باید بین ۱ و ۱۰ باشد',
    exerciseRange: 'تعداد روزهای ورزش باید بین ۰ و ۷ باشد',
    outOf10: 'از ۱۰',
    daysUnit: 'روز',
    // Preferences
    prefTitle: 'ترجیحات غذایی',
    prefSubtitle: 'بگویید چه غذاهایی دوست دارید تا برنامه شما دلپذیرتر باشد.',
    prefIranianFood: 'غذای ایرانی را دوست دارم',
    prefVegetarian: 'گیاه‌خوار هستم',
    prefVegan: 'وگان هستم',
    prefHalal: 'غذای حلال مصرف می‌کنم',
    prefDisliked: 'غذاهایی که دوست ندارم',
    prefDislikedPlaceholder: 'مثال: بادمجان، جگر',
    prefFavorite: 'غذاهای مورد علاقه',
    prefFavoritePlaceholder: 'مثال: کباب، قرمه‌سبزی',
    prefBreakfast: 'عادت صبحانه',
    prefBreakfastSkip: 'صبحانه نمی‌خورم',
    prefBreakfastLight: 'صبحانه سبک',
    prefBreakfastFull: 'صبحانه کامل',
    prefBreakfastVaries: 'متغیر',
    prefRice: 'مصرف برنج',
    prefBread: 'مصرف نان',
    prefSweets: 'مصرف شیرینی و شکر',
    prefTea: 'مصرف چای و نوشیدنی شیرین',
    prefRestaurant: 'تناوب رستوران رفتن',
    consumNever: 'هرگز',
    consumRarely: 'به ندرت',
    consumFewWeekly: 'چند بار در هفته',
    consumDaily: 'روزانه',
    consumSeveralDaily: 'چندین بار در روز',
    prefAddFood: 'افزودن',
    // Behavior
    behavTitle: 'عادات غذایی',
    behavSubtitle: 'صادقانه پاسخ دهید تا بهترین راهنمایی را دریافت کنید.',
    behavEmotional: 'هنگام استرس یا ناراحتی پرخوری می‌کنم',
    behavNight: 'شب‌خوری دارم',
    behavSkipping: 'اغلب وعده‌های غذایی را حذف می‌کنم',
    behavBinge: 'سابقه پرخوری ناگهانی (binge) دارم',
    behavCravings: 'ولع‌های غذایی رایج',
    behavCravSweet: 'شیرینی',
    behavCravSalty: 'شور',
    behavCravFried: 'سرخ‌کردنی',
    behavCravBread: 'نان و کربوهیدرات',
    behavCravChocolate: 'شکلات',
    behavCravOther: 'سایر',
    behavCravOtherPlaceholder: 'ولع دیگری وارد کنید',
    behavDietHistory: 'سابقه رژیم غذایی',
    behavDietHistoryPlaceholder: 'رژیم‌هایی که قبلاً امتحان کرده‌اید...',
    behavPreviousFails: 'دلایل ناموفق بودن رژیم‌های قبلی',
    behavPreviousFailsPlaceholder: 'چه چیزی باعث شد رژیم‌های قبلی موفق نشوید؟',
    behavHunger: 'الگوی گرسنگی',
    behavHungerHint: 'می‌توانید چند گزینه انتخاب کنید',
    behavHungerMorning: 'صبح‌ها بیشتر گرسنه می‌شوم',
    behavHungerAfternoon: 'بعد از ظهرها بیشتر گرسنه می‌شوم',
    behavHungerEvening: 'عصرها بیشتر گرسنه می‌شوم',
    behavHungerNight: 'شب‌ها بیشتر گرسنه می‌شوم',
    behavHungerRandom: 'الگوی خاصی ندارم',
    behavMotivation: 'سطح انگیزه',
    behavMotivationLow: 'کم',
    behavMotivationHigh: 'زیاد',
    behavAddCraving: 'افزودن ولع دیگر',
    // Final
    finalTitle: 'تقریباً آماده‌اید!',
    finalSubtitle: 'یک ویدئوی کوتاه راهنما را تماشا کنید و ثبت‌نام خود را تکمیل کنید.',
    finalVideoLabel: 'ویدئوی راهنمای اپلیکیشن',
    finalVideoComingSoon: 'ویدئوی راهنما به زودی اضافه می‌شود',
    finalVideoLoadError: 'بارگذاری ویدئو ناموفق بود. می‌توانید ادامه دهید.',
    finalWatchFirst: 'تماشای ویدئو توصیه می‌شود، اما می‌توانید ادامه دهید.',
    finalMarkWatched: 'تماشا شد (محیط توسعه)',
    finalWatchedBadge: 'ویدئو تماشا شد',
    finalComplete: 'شروع با مربی تغذیه',
    finalCompleting: 'در حال تکمیل...',
    // Clinical review
    clinicalTitle: 'نیاز به بررسی متخصص',
    clinicalMessage:
      'بر اساس اطلاعات وارد شده، پیشنهاد می‌شود پیش از شروع برنامه غذایی با یک متخصص تغذیه یا پزشک مشورت کنید. مربی تغذیه در کنار راهنمایی کلی، این موضوع را برای شما یادآوری خواهد کرد.',
    clinicalDisclaimer:
      'این اپلیکیشن جایگزین پزشک یا متخصص تغذیه نیست و مسئولیت تصمیمات پزشکی را بر عهده نمی‌گیرد.',
    // Completion
    doneTitle: 'خوش آمدید!',
    doneMessage: 'پروفایل شما با موفقیت تکمیل شد. مربی تغذیه آماده راهنمایی شماست.',
    doneClinicalTitle: 'پروفایل تکمیل شد',
    doneClinicalMessage:
      'با توجه به وضعیت سلامت شما، توصیه می‌کنیم قبل از شروع برنامه غذایی جدی با پزشک مشورت کنید.',
    doneContinue: 'ورود به اپلیکیشن',
    // Errors
    errApiError: 'خطا در ارتباط با سرور',
    errProfileRequired: 'ابتدا پروفایل خود را تکمیل کنید',
    errUnauthorized: 'لطفاً دوباره وارد شوید',
    errSubmitFailed: 'ارسال اطلاعات ناموفق بود. دوباره تلاش کنید.',
    errLoadFailed: 'بارگذاری اطلاعات ناموفق بود. صفحه را رفرش کنید.',
  },
  dashboard: {
    title: 'خانه',
    greetingGeneric: 'سلام!',
    greetingName: 'سلام {name}!',
    subtitle: 'مربی تغذیه آماده راهنمایی شماست.',
    quickActionsTitle: 'اقدامات سریع',
    generatePlan: 'ساخت برنامه غذایی',
    analyzeMeal: 'تحلیل وعده غذایی',
    whatToEatNow: 'الان چی بخورم؟',
    openChat: 'گفتگو با مربی',
    noPlanTitle: 'هنوز برنامه‌ای ندارید',
    noPlanDesc: 'برنامه غذایی شخصی‌سازی‌شده خود را بسازید.',
    noPlanCta: 'ساخت برنامه',
    currentPlanLabel: 'برنامه فعلی',
    noOnboarding: 'پروفایل ناقص است',
    noOnboardingCta: 'تکمیل پروفایل',
    riskLow: 'سطح ریسک: پایین',
    riskMedium: 'سطح ریسک: متوسط',
    riskHigh: 'سطح ریسک: بالا',
    riskClinical: 'نیاز به بررسی پزشکی',
    providerMock: 'حالت آزمایشی',
    providerLive: 'هوش مصنوعی فعال',
    clinicalAlertTitle: 'توجه: بررسی متخصص توصیه می‌شود',
    clinicalAlertDesc: 'بر اساس وضعیت سلامت شما، پیش از شروع هر رژیم غذایی با پزشک یا متخصص تغذیه مشورت کنید.',
    behaviorGuide: 'راهنمایی رفتاری سریع',
    calendarPlanDesc: 'برنامه غذایی هفتگی شما آماده است.',
  },
  plan: {
    title: 'برنامه غذایی',
    subtitle: 'برنامه غذایی شخصی‌سازی‌شده شما',
    generateBtn: 'ساخت برنامه',
    regenerateBtn: 'بازسازی برنامه',
    generating: 'در حال ساخت برنامه...',
    noPlanTitle: 'هنوز برنامه‌ای ندارید',
    noPlanDesc: 'مربی تغذیه بر اساس پروفایل شما یک برنامه شخصی می‌سازد.',
    noPlanCta: 'ساخت برنامه غذایی',
    generatedAt: 'ساخته‌شده در',
    summary: 'خلاصه',
    dailyGuidelinesTitle: 'راهنمای روزانه',
    calories: 'کالری',
    protein: 'پروتئین',
    carbs: 'کربوهیدرات',
    fat: 'چربی',
    fiber: 'فیبر',
    water: 'آب',
    notes: 'یادداشت',
    mealsTitle: 'وعده‌های غذایی',
    breakfast: 'صبحانه',
    lunch: 'ناهار',
    dinner: 'شام',
    snack: 'میان‌وعده',
    unknown: 'وعده',
    warnings: 'هشدارها',
    mockBadge: 'حالت آزمایشی',
    liveBadge: 'هوش مصنوعی',
    unitGrams: 'گرم',
    unitLiters: 'لیتر',
    unitKcal: 'کیلوکالری',
    unitMin: 'دقیقه',
  },
  mealAnalysis: {
    title: 'تحلیل وعده غذایی',
    subtitle: 'وعده غذایی خود را توضیح دهید تا تحلیل کنیم.',
    mealDescLabel: 'توضیح وعده غذایی',
    mealDescPlaceholder: 'مثال: برنج با مرغ و سالاد شیرازی، دوغ. یا: نان، پنیر، چای با شکر.',
    mealTimeLabel: 'نوع وعده',
    contextLabel: 'اطلاعات بیشتر (اختیاری)',
    contextPlaceholder: 'مثلاً: بعد از ورزش، سر کار، رستوران...',
    analyzeBtn: 'تحلیل کن',
    analyzing: 'در حال تحلیل...',
    newAnalysisBtn: 'تحلیل وعده جدید',
    resultTitle: 'نتیجه تحلیل',
    qualityScore: 'امتیاز کیفیت',
    outOf10: 'از ۱۰',
    protein: 'پروتئین',
    fiber: 'فیبر',
    sugar: 'قند',
    balance: 'تعادل',
    portion: 'حجم وعده',
    suggestionsTitle: 'پیشنهادها',
    warningsTitle: 'هشدارها',
    noWarnings: 'بدون هشدار خاص',
    breakfast: 'صبحانه',
    lunch: 'ناهار',
    dinner: 'شام',
    snack: 'میان‌وعده',
    unknown: 'نامشخص',
    mockBadge: 'حالت آزمایشی',
    likelyMeal: 'وعده احتمالی',
    uncertainties: 'موارد نامطمئن',
    nutritionQualityTitle: 'کیفیت تغذیه‌ای',
    proteinQuality: 'کیفیت پروتئین',
    fiberVegetableQuality: 'کیفیت فیبر و سبزیجات',
    carbohydrateQuality: 'کیفیت کربوهیدرات',
    fatQuality: 'کیفیت چربی',
    simpleSugarQuality: 'کیفیت قند ساده',
    portionVolumeAssessment: 'ارزیابی حجم وعده',
    satietyAssessment: 'ارزیابی سیری',
    goalEffect: 'اثر احتمالی روی هدف',
    smallCorrection: 'یک اصلاح کوچک',
    nextMealSuggestion: 'پیشنهاد وعده بعد',
    noExtremeCompensation: 'بدون جبران افراطی',
  },
  whatToEat: {
    title: 'الان چی بخورم؟',
    subtitle: 'مواد موجود را بنویسید تا پیشنهاد بدیم.',
    availableFoodsLabel: 'مواد موجود در خانه',
    availableFoodsPlaceholder: 'مثلاً: برنج، تخم‌مرغ، ماست، نان...',
    availableFoodsHint: 'Enter بزنید یا کاما بگذارید تا ماده اضافه شود',
    removeFoodAriaLabel: 'حذف {food}',
    addFood: 'افزودن',
    hungerLevelLabel: 'سطح گرسنگی',
    hungerLow: 'کم',
    hungerMedium: 'متوسط',
    hungerHigh: 'زیاد',
    mealContextLabel: 'موقعیت (اختیاری)',
    mealContextPlaceholder: 'مثلاً: بعد از ورزش، سر کار، میهمانی...',
    timeAvailableLabel: 'زمان آماده‌سازی (دقیقه)',
    timeAvailablePlaceholder: 'مثلاً: ۱۵',
    askBtn: 'پیشنهاد بده',
    asking: 'در حال آماده‌سازی پیشنهاد...',
    optionsTitle: 'پیشنهادها',
    calories: 'کالری تقریبی',
    prepTime: 'زمان آماده‌سازی',
    reasoningTitle: 'چرا این پیشنهادها؟',
    warningsTitle: 'نکات مهم',
    tryAgainBtn: 'پیشنهاد جدید',
    mockBadge: 'حالت آزمایشی',
    optionalDetails: 'جزئیات اختیاری',
    currentPlaceLabel: 'محل فعلی',
    currentPlacePlaceholder: 'خانه، محل کار، رستوران...',
    lastMealLabel: 'آخرین وعده',
    lastMealPlaceholder: 'مثلاً ۳ ساعت پیش ناهار سبک خوردم',
    hungerScaleLabel: 'گرسنگی از ۱ تا ۱۰',
    cookingAccessLabel: 'دسترسی به پخت‌وپز',
    cookingAccessPlaceholder: 'مثلاً فقط مایکروویو یا آشپزخانه کامل',
    budgetContextLabel: 'بودجه یا دسترسی',
    budgetContextPlaceholder: 'مثلاً اقتصادی، غذای بیرون، مواد محدود',
    preferenceNoteLabel: 'ترجیح امروز',
    preferenceNotePlaceholder: 'مثلاً غذای ایرانی، سبک، بدون گوشت...',
    bestAligned: 'هماهنگ‌تر با هدف',
    fastest: 'سریع‌ترین',
    flexible: 'انعطاف‌پذیر',
    householdPortions: 'اندازه خانگی',
    whyFitsGoal: 'چرا با هدف می‌خواند',
    substitutions: 'جایگزین‌ها',
    safetyNote: 'نکته ایمنی',
  },
  behaviorCoaching: {
    title: 'راهنمایی رفتاری سریع',
    subtitle: 'برای هوس، لغزش یا موقعیت‌های بیرون از خانه یک راهنمای کوتاه و بدون قضاوت بگیرید.',
    cravingTab: 'هوس',
    slipTab: 'لغزش',
    contextTab: 'رستوران/سفر',
    cravingFoodLabel: 'خوراکی مورد هوس',
    cravingFoodPlaceholder: 'مثلاً شیرینی، چیپس، نان...',
    cravingIntensityLabel: 'شدت هوس از ۱ تا ۱۰',
    hungerScaleLabel: 'گرسنگی از ۱ تا ۱۰',
    stressLabel: 'استرس از ۱ تا ۵',
    sleepQualityLabel: 'کیفیت خواب از ۱ تا ۵',
    currentPlaceLabel: 'محل فعلی',
    timeOfDayLabel: 'زمان روز',
    noteLabel: 'یادداشت کوتاه',
    notePlaceholder: 'چه اتفاقی افتاده یا چه چیزی کمک می‌خواهید؟',
    submitCraving: 'دریافت کمک برای هوس',
    submittingCraving: 'در حال آماده‌سازی راهنمایی...',
    slipWhatHappenedLabel: 'چه اتفاقی افتاد؟',
    slipWhatHappenedPlaceholder: 'مثلاً شام بیشتر از برنامه خوردم',
    slipFoodsLabel: 'خوراکی‌های خورده‌شده',
    slipFoodsPlaceholder: 'مثلاً پیتزا، شیرینی',
    slipAmountLabel: 'مقدار تقریبی',
    slipAmountPlaceholder: 'مثلاً دو تکه، یک بشقاب',
    submitSlip: 'دریافت راهنمای بازگشت',
    submittingSlip: 'در حال آماده‌سازی راهنمای بازگشت...',
    contextTypeLabel: 'نوع موقعیت',
    contextRestaurant: 'رستوران',
    contextParty: 'مهمانی',
    contextTravel: 'سفر',
    contextWork: 'محل کار',
    contextMixed: 'ترکیبی',
    availableOptionsLabel: 'گزینه‌های موجود',
    availableOptionsPlaceholder: 'مثلاً کباب، سالاد، برنج',
    preferredOptionLabel: 'گزینه دلخواه',
    preferredOptionPlaceholder: 'اگر چیزی را ترجیح می‌دهید بنویسید',
    submitContext: 'دریافت راهنمای موقعیت',
    submittingContext: 'در حال آماده‌سازی راهنمای موقعیت...',
    calmingMessage: 'پیام آرام‌کننده',
    likelyTriggers: 'محرک‌های احتمالی',
    hungerVsCraving: 'گرسنگی یا هوس',
    immediateOptions: 'گزینه‌های فوری',
    betterChoice: 'انتخاب هماهنگ‌تر',
    flexibleChoice: 'انتخاب انعطاف‌پذیر',
    preventionTip: 'نکته پیشگیری',
    followUpQuestion: 'سؤال پیگیری',
    dataNotFailure: 'داده است، نه شکست',
    triggerQuestions: 'سؤال‌های شناخت محرک',
    patternHypothesis: 'فرضیه الگو',
    oneSmallAdjustment: 'یک تنظیم کوچک',
    nextMealPlan: 'برنامه وعده بعد',
    tomorrowReset: 'بازگشت فردا',
    noExtremeCompensation: 'بدون جبران افراطی',
    bestAvailableChoice: 'بهترین انتخاب موجود',
    portionStrategy: 'راهبرد اندازه',
    plateBalanceTip: 'تعادل بشقاب',
    drinkTip: 'نوشیدنی',
    dessertStrategy: 'دسر یا میان‌وعده',
    highCalorieChoice: 'اگر گزینه پرکالری انتخاب شد',
    nextMealAdjustment: 'تنظیم وعده بعد',
    safetyNotes: 'نکات ایمنی',
    humanReview: 'نیاز به مرور انسانی',
    error: 'دریافت راهنمایی ناموفق بود. دوباره تلاش کنید.',
    scaleError10: 'عدد باید بین ۱ تا ۱۰ باشد.',
    scaleError5: 'عدد باید بین ۱ تا ۵ باشد.',
  },
  adaptPlan: {
    revisionApplied: 'بازبینی روی برنامه اعمال شد',
    revisionNotApplied: 'بازبینی فقط به صورت راهنمایی ارائه شد',
    revisionScope: 'دامنه بازبینی',
    revisedDate: 'تاریخ بازبینی',
    changedItems: 'موارد تغییر کرده',
    reasonForChanges: 'دلیل تغییرات',
    safetyNotes: 'نکات ایمنی',
    humanReview: 'نیاز به مرور انسانی',
    fallbackReason: 'دلیل استفاده از پاسخ جایگزین',
  },
  companionChat: {
    title: 'گفتگو با مربی',
    subtitle: 'سوال تغذیه‌ای دارید؟ بپرسید.',
    startChat: 'شروع گفتگو با مربی تغذیه',
    inputPlaceholder: 'پیام خود را بنویسید...',
    sendBtn: 'ارسال',
    sending: 'در حال ارسال...',
    emptyTitle: 'گفتگو را شروع کنید',
    emptyDesc: 'سوال تغذیه‌ای دارید؟ مربی آماده پاسخ است.',
    loadError: 'بارگذاری تاریخچه ناموفق بود.',
    sendError: 'ارسال پیام ناموفق بود. دوباره تلاش کنید.',
    mockBadge: 'حالت آزمایشی',
    you: 'شما',
    coach: 'مربی',
    typingIndicator: 'مربی در حال نوشتن...',
    clearMemory: 'پاک کردن حافظه گفتگو',
    clearMemoryConfirmTitle: 'حافظه گفتگو پاک شود؟',
    clearMemoryConfirm: 'بله، پاک کن',
    clearMemoryCancel: 'لغو',
    memoryCleared: 'حافظه گفتگو پاک شد',
  },
  safety: {
    clinicalTitle: 'توجه: مشاوره پزشکی توصیه می‌شود',
    clinicalMessage:
      'بر اساس اطلاعات سلامتی شما، پیش از شروع هر برنامه غذایی تخصصی با پزشک یا متخصص تغذیه مشورت کنید. مربی تغذیه می‌تواند راهنمایی کلی ارائه دهد اما جایگزین مشاوره پزشکی نیست.',
    clinicalDisclaimer:
      'این اپلیکیشن جایگزین پزشک، متخصص تغذیه یا هر ارائه‌دهنده بهداشتی نیست.',
    highRiskTitle: 'سطح ریسک: بالا',
    highRiskMessage:
      'با توجه به وضعیت سلامتی شما، برنامه ارائه‌شده محافظه‌کارانه و کلی است. مشاوره با متخصص تغذیه توصیه می‌شود.',
    notADoctorNote: 'این اطلاعات آموزشی است و جایگزین تشخیص و درمان پزشکی نمی‌شود.',
  },
  calendar: {
    title: 'تقویم غذایی',
    subtitle: 'برنامه غذایی هفتگی شما',
    noPlanTitle: 'هنوز برنامه‌ای ندارید',
    noPlanDesc: 'برنامه ۷ روزه اول خود را بسازید.',
    generateInitialWeek: 'ساخت برنامه ۷ روزه',
    generateNextWeek: 'ساخت هفته بعد',
    nextWeekPromptTitle: 'برنامه هفته بعد آماده‌سازی می‌خواهد',
    nextWeekPromptDescription: 'برای اینکه تقویم غذایی‌ات قطع نشود، برنامه ۷ روز آینده را بساز.',
    nextWeekPromptCta: 'ساخت برنامه هفته بعد',
    plannedDays: 'روزهای برنامه‌ریزی‌شده',
    missingDays: 'روزهای بدون برنامه',
    nextUnplannedDate: 'اولین روز بدون برنامه',
    breakfast: 'صبحانه',
    lunch: 'ناهار',
    dinner: 'شام',
    snack: 'میان‌وعده',
    today: 'امروز',
    day: 'روز',
    week: 'هفته',
    planDate: 'تاریخ',
    generationLoading: 'در حال ساخت برنامه...',
    generationSuccess: 'برنامه با موفقیت ساخته شد',
    generationError: 'ساخت برنامه ناموفق بود. دوباره تلاش کنید.',
    warnings: 'هشدارها',
    hydrationGoal: 'هدف آب‌رسانی',
    notes: 'یادداشت',
    alternatives: 'جایگزین‌ها',
    prepNotes: 'نکات آماده‌سازی',
    portionGuidance: 'راهنمای حجم',
    dietType: 'نوع رژیم',
    difficulty: 'سطح دشواری',
    dailyCalories: 'کالری روزانه',
    protein: 'پروتئین',
    carbs: 'کربوهیدرات',
    fat: 'چربی',
    fiber: 'فیبر',
    dayTypeTraining: 'روز تمرین',
    dayTypeRest: 'روز استراحت',
    dayTypeLight: 'فعالیت سبک',
    trainingGuidance: 'راهنمای تمرین',
    sleepWakeGuidance: 'راهنمای خواب و بیداری',
    hydrationPlan: 'برنامه آب‌رسانی',
    cheatMealGuidance: 'راهنمای وعده آزاد',
    medicalWarnings: 'هشدارهای پزشکی',
    mealTimeWindow: 'پنجره زمانی',
    mealCalories: 'کالری وعده',
    morningSnack: 'میان‌وعده صبح',
    afternoonSnack: 'میان‌وعده بعدازظهر',
    eveningSnack: 'میان‌وعده شبانه',
    preWorkout: 'قبل از تمرین',
    postWorkout: 'بعد از تمرین',
    drinkGuidance: 'راهنمای نوشیدنی',
    foodItems: 'مواد غذایی',
  },
  progress: {
    title: 'پیشرفت',
    subtitle: 'مسیر سلامتی شما',
    tabSummary: 'خلاصه',
    tabWeekly: 'گزارش هفتگی',
    checkInTitle: 'ثبت وضعیت امروز',
    checkInSubtitle: 'چند دقیقه وقت بگذارید — اطلاعات بیشتر، راهنمایی بهتر',
    checkInWeight: 'وزن امروز',
    checkInWeightUnit: 'کیلوگرم',
    checkInHunger: 'سطح گرسنگی (۱–۵)',
    checkInSleep: 'ساعت خواب',
    checkInSleepUnit: 'ساعت',
    checkInStress: 'سطح استرس (۱–۵)',
    checkInActivity: 'دقیقه تحرک',
    checkInActivityUnit: 'دقیقه',
    checkInNotes: 'یادداشت پیروی',
    checkInNotesPlaceholder: 'مثلاً: امروز رژیم را رعایت کردم، یک شام سنگین داشتم...',
    checkInSubmit: 'ثبت وضعیت',
    checkInSubmitting: 'در حال ثبت...',
    checkInSuccess: 'وضعیت امروز ثبت شد',
    checkInAlreadyToday: 'امروز ثبت شده — می‌توانید ویرایش کنید',
    checkInTodayMissing: 'امروز ثبت نشده — ثبت وضعیت',
    summaryTitle: 'خلاصه پیشرفت',
    latestWeight: 'آخرین وزن',
    weightTrend: 'روند وزن',
    behaviourWinsTitle: 'دستاوردهای این هفته',
    loggingStreak: 'روزهای متوالی ثبت',
    loggingStreakDays: 'روز',
    winSleep: 'خواب منظم',
    winActivity: 'تحرک کافی',
    winLogging: 'ثبت منظم',
    winLowStress: 'استرس پایین',
    winLowHunger: 'گرسنگی کنترل‌شده',
    winHydration: 'آب کافی',
    winProtein: 'پروتئین کافی',
    winFiber: 'فیبر کافی',
    winNotTracked: 'هنوز ثبت نمی‌شود',
    weeklyTitle: 'گزارش هفتگی',
    weeklyPeriod: 'دوره گزارش',
    weeklyAdherence: 'درصد پیروی',
    weeklyAvgSleep: 'میانگین خواب',
    weeklyAvgStress: 'میانگین استرس',
    weeklyAvgHunger: 'میانگین گرسنگی',
    weeklyTotalActivity: 'کل تحرک',
    weeklyWeightDelta: 'تغییر وزن',
    weeklySleepStressNote: 'نکته خواب و استرس',
    weeklyFocusTitle: 'پیشنهاد هفته بعد',
    weeklyLoggingDays: 'روزهای ثبت‌شده',
    emptyTitle: 'هنوز هیچ ثبتی ندارید',
    emptyDesc: 'اولین ثبت وضعیت را همین‌جا انجام دهید — فقط چند دقیقه کافی است',
    emptyCheckinCta: 'ثبت وضعیت اول',
    emptyWeeklyTitle: 'هنوز داده کافی ندارید',
    emptyWeeklyDesc: 'پس از ۳ روز ثبت، گزارش هفتگی آماده می‌شود',
    errSubmitFailed: 'ثبت ناموفق بود — دوباره تلاش کنید',
    errLoadFailed: 'بارگذاری داده‌ها با مشکل مواجه شد — دوباره تلاش کنید',
    unitKg: 'کیلوگرم',
    unitHours: 'ساعت',
    unitMinutes: 'دقیقه',
    unitPercent: 'درصد',
    checkInWaist: 'دور کمر',
    checkInWaistUnit: 'سانتی‌متر',
    checkInHunger10: 'گرسنگی (۱ تا ۱۰)',
    checkInSleepQuality: 'کیفیت خواب (۱ تا ۵)',
    checkInEnergy: 'انرژی (۱ تا ۵)',
    checkInCravings: 'هوس‌های غذایی',
    checkInCravingsPlaceholder: 'مثلاً شیرینی بعد از شام',
    checkInCravingType: 'نوع هوس',
    checkInCravingTypePlaceholder: 'شیرین، شور، نان، سرخ‌کردنی...',
    checkInEatingLocation: 'محل غذا خوردن',
    checkInEatingLocationPlaceholder: 'خانه، کار، رستوران...',
    checkInPlannedEatingOut: 'امروز غذای بیرون یا رستوران داشتم',
    checkInAdherence: 'پایبندی به برنامه (۱ تا ۵)',
    checkInSymptoms: 'علائم یا نشانه‌ها',
    checkInSymptomsPlaceholder: 'اگر علامت مهمی داشتید اینجا بنویسید',
    weeklySummaryTitle: 'خلاصه انسانی',
    weeklyWaistDelta: 'تغییر دور کمر',
    weeklyAdherenceSummary: 'خلاصه پایبندی',
    weeklyRiskyMeals: 'وعده‌های پرریسک',
    weeklyRiskyWindows: 'زمان‌های پرریسک',
    weeklyCravingPatterns: 'الگوی هوس‌ها',
    weeklyQualityTitle: 'کیفیت تغذیه',
    weeklyProteinQuality: 'پروتئین',
    weeklyFiberQuality: 'فیبر و سبزیجات',
    weeklyHydrationQuality: 'آب و مایعات',
    weeklySimpleSugarQuality: 'قند ساده',
    weeklySleepFood: 'رابطه خواب و خوردن',
    weeklyStressFood: 'رابطه استرس و خوردن',
    weeklyEatingOut: 'الگوی غذای بیرون',
    weeklyBehaviorPattern: 'جمع‌بندی الگوها',
    weeklyStrengths: 'سه نقطه قوت',
    weeklyAdjustments: 'دو تنظیم کوچک',
    weeklyNextGoal: 'هدف کوچک هفته بعد',
    weeklyMonitoringNotes: 'نکات پایش',
    weeklySafetyNotes: 'نکات ایمنی',
    weeklyHumanReview: 'مرور با متخصص توصیه می‌شود',
    weeklyConfidence: 'سطح اطمینان گزارش',
  },
}

export default fa
