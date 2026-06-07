import type { Dictionary } from '@/dictionaries/fa'
import AppIcon from '@/components/ui/AppIcon'

interface Props {
  dict: Pick<Dictionary, 'safety'>
  variant?: 'clinical' | 'high_risk'
  compact?: boolean
}

export default function ClinicalReviewState({
  dict,
  variant = 'clinical',
  compact = false,
}: Props) {
  const isClinical = variant === 'clinical'

  if (compact) {
    return (
      <div className="flex items-start gap-3 p-4 rounded-2xl bg-warm-muted border border-warm/20">
        <AppIcon name="medical" className="text-warm mt-0.5 shrink-0" size={20} />
        <div className="min-w-0">
          <p className="text-sm font-semibold text-ink mb-1">
            {isClinical ? dict.safety.clinicalTitle : dict.safety.highRiskTitle}
          </p>
          <p className="text-xs text-ink-2 leading-relaxed">
            {isClinical ? dict.safety.clinicalMessage : dict.safety.highRiskMessage}
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="rounded-2xl bg-warm-muted border border-warm/20 overflow-hidden">
      <div className="flex items-center gap-3 px-5 py-4 border-b border-warm/20">
        <AppIcon name="medical" className="text-warm shrink-0" size={26} />
        <h2 className="text-base font-semibold text-ink">
          {isClinical ? dict.safety.clinicalTitle : dict.safety.highRiskTitle}
        </h2>
      </div>
      <div className="px-5 py-4 space-y-3">
        <p className="text-sm text-ink-2 leading-relaxed">
          {isClinical ? dict.safety.clinicalMessage : dict.safety.highRiskMessage}
        </p>
        <p className="text-xs text-ink-3 leading-relaxed italic">
          {dict.safety.clinicalDisclaimer}
        </p>
      </div>
    </div>
  )
}
