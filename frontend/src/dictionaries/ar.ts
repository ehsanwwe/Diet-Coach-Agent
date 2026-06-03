import type { Dictionary } from './fa'

const ar: Dictionary = {
  common: {
    appName: 'مدرب التغذية',
    loading: 'جارٍ التحميل...',
    error: 'حدث خطأ',
    retry: 'حاول مرة أخرى',
    back: 'رجوع',
    next: 'التالي',
    save: 'حفظ',
    cancel: 'إلغاء',
    confirm: 'تأكيد',
    close: 'إغلاق',
    yes: 'نعم',
    no: 'لا',
    or: 'أو',
  },
  splash: {
    tagline: 'مدرب التغذية الذكي',
    subtitle: 'إرشادات يومية للصحة والتغذية',
    description:
      'احصل على خطة وجبات مخصصة مع مدرب التغذية الذكي، متوافقة مع ثقافتك واحتياجاتك الصحية.',
    getStarted: 'ابدأ الآن',
    comingSoon: 'قريباً',
  },
  nav: {
    home: 'الرئيسية',
    chat: 'المحادثة',
    progress: 'التقدم',
    settings: 'الإعدادات',
  },
  language: {
    select: 'اختر اللغة',
    fa: 'فارسی',
    en: 'English',
    ar: 'العربية',
    current: 'اللغة الحالية',
    change: 'تغيير اللغة',
  },
  errors: {
    notFound: 'الصفحة غير موجودة',
    offline: 'لا يوجد اتصال بالإنترنت',
    generic: 'حدث خطأ ما. يرجى المحاولة مرة أخرى.',
  },
  auth: {
    loginTitle: 'تسجيل الدخول إلى مدرب التغذية',
    loginSubtitle: 'أدخل رقم هاتفك للمتابعة',
    phonePlaceholder: '09123456789',
    phoneLabel: 'رقم الهاتف',
    phoneError: 'أدخل رقم هاتف صحيح',
    sendOtp: 'إرسال رمز التحقق',
    otpTitle: 'رمز التحقق',
    otpSubtitle: 'أدخل الرمز المكون من 6 أرقام الذي أرسلناه إليك',
    otpLabel: 'رمز التحقق',
    otpPlaceholder: '123456',
    otpError: 'يجب أن يكون الرمز 6 أرقام',
    otpExpired: 'انتهت صلاحية الرمز. يرجى طلب رمز جديد.',
    verify: 'تحقق',
    resend: 'إعادة إرسال الرمز',
    resendIn: 'إعادة الإرسال خلال {seconds} ثانية',
    invalidOtp: 'الرمز غير صحيح. يرجى المحاولة مرة أخرى.',
    loginSuccess: 'تم تسجيل الدخول بنجاح',
    logoutSuccess: 'تم تسجيل الخروج بنجاح',
    networkError: 'خطأ في الشبكة. يرجى المحاولة مرة أخرى.',
  },
}

export default ar
