import type { ComponentProps } from 'react'
import {
  Activity,
  Apple,
  Baby,
  Bot,
  Brain,
  CalendarDays,
  Check,
  ChevronDown,
  ChevronUp,
  CircleHelp,
  ClipboardList,
  Droplets,
  Dumbbell,
  Flower2,
  HeartPulse,
  Home,
  Leaf,
  MessageCircle,
  Mic,
  RefreshCw,
  Ruler,
  Salad,
  Scale,
  Search,
  Settings,
  Soup,
  Sparkles,
  Stethoscope,
  Sun,
  Sunrise,
  TrendingUp,
  Utensils,
  UtensilsCrossed,
} from 'lucide-react'

const icons = {
  activity: Activity,
  apple: Apple,
  baby: Baby,
  bot: Bot,
  brain: Brain,
  calendar: CalendarDays,
  chat: MessageCircle,
  check: Check,
  chevronDown: ChevronDown,
  chevronUp: ChevronUp,
  clipboardList: ClipboardList,
  dinner: Soup,
  digestive: Leaf,
  generalHealth: Sparkles,
  healthyEating: Salad,
  home: Home,
  lunch: Sun,
  meal: Utensils,
  medical: Stethoscope,
  microphone: Mic,
  muscle: Dumbbell,
  nutrition: UtensilsCrossed,
  pcos: Flower2,
  portion: Ruler,
  progress: TrendingUp,
  question: CircleHelp,
  refresh: RefreshCw,
  safety: HeartPulse,
  search: Search,
  settings: Settings,
  snack: Apple,
  sports: Activity,
  sunrise: Sunrise,
  water: Droplets,
  weight: Scale,
} as const

export type AppIconName = keyof typeof icons

type Props = Omit<ComponentProps<typeof Home>, 'name'> & {
  name: AppIconName
}

export default function AppIcon({ name, size = 20, strokeWidth = 2, ...props }: Props) {
  const Icon = icons[name]
  return <Icon aria-hidden="true" focusable="false" size={size} strokeWidth={strokeWidth} {...props} />
}
