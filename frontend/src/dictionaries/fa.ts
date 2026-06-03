/**
 * Dictionary interface + Persian (Farsi) translations.
 * fa.ts is the source-of-truth for the Dictionary shape.
 * All other dictionary files must conform to this interface.
 */

export interface Dictionary {
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
}

const fa: Dictionary = {
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
}

export default fa
