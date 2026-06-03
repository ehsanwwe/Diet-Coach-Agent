'use client'

import { AlertTriangle } from 'lucide-react'
import type { Dictionary } from '@/dictionaries/fa'

interface Props {
  dict: Dictionary['onboarding']
}

export default function ClinicalReviewNotice({ dict }: Props) {
  return (
    <div className="mx-6 my-4 rounded-2xl bg-warm-muted border border-warm border-opacity-30 p-4">
      <div className="flex gap-3">
        <AlertTriangle size={18} className="text-warm shrink-0 mt-0.5" />
        <div className="space-y-1.5">
          <p className="text-sm font-semibold text-ink">{dict.clinicalTitle}</p>
          <p className="text-xs text-ink-2 leading-relaxed">{dict.clinicalMessage}</p>
          <p className="text-xs text-ink-3 leading-relaxed border-t border-line pt-2 mt-2">
            {dict.clinicalDisclaimer}
          </p>
        </div>
      </div>
    </div>
  )
}
