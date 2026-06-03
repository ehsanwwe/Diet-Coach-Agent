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
  }
  errors: {
    notFound: string
    offline: string
    generic: string
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
    appName: 'مربی تغذیه',
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
  },
  errors: {
    notFound: 'صفحه مورد نظر یافت نشد',
    offline: 'اتصال اینترنت برقرار نیست',
    generic: 'مشکلی پیش آمد. لطفاً دوباره تلاش کنید.',
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
    goalTitle: 'هدف اصلی شما چیست؟',
    goalSubtitle: 'یک هدف اصلی انتخاب کنید تا برنامه شما بر اساس آن تنظیم شود.',
    goalSelectPrompt: 'لطفاً یک گزینه انتخاب کنید',
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
    medAllergiesPlaceholder: 'مثال: گلوتن، لاکتوز، بادام زمینی',
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
    finalWatchFirst: 'لطفاً ابتدا ویدئو را تماشا کنید',
    finalMarkWatched: '✓ تماشا شد (محیط توسعه)',
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
}

export default fa
