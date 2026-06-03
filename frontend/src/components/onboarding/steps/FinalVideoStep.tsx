'use client'

import { useState } from 'react'
import { PlayCircle, CheckCircle } from 'lucide-react'
import { cn } from '@/lib/cn'
import type { Dictionary } from '@/dictionaries/fa'
import ClinicalReviewNotice from '../ClinicalReviewNotice'
import OnboardingHabitChat from '../OnboardingHabitChat'

interface Props {
  dict: Dictionary['onboarding']
  audioDict: Dictionary['audio']
  isSubmitting: boolean
  apiError: string | null
  clinicalReviewRequired: boolean
  onComplete: () => void
  onBack: () => void
}

const DEV_BYPASS = process.env.NEXT_PUBLIC_ENABLE_DEV_VIDEO_BYPASS === 'true'

export default function FinalVideoStep({
  dict,
  audioDict,
  isSubmitting,
  apiError,
  clinicalReviewRequired,
  onComplete,
}: Props) {
  const [watched, setWatched] = useState(false)

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-y-auto px-6 py-2 space-y-6">
        <div>
          <h1 className="text-xl font-bold text-ink">{dict.finalTitle}</h1>
          <p className="text-sm text-ink-2 mt-1">{dict.finalSubtitle}</p>
        </div>

        {clinicalReviewRequired && <ClinicalReviewNotice dict={dict} />}

        {/* Video placeholder */}
        <div
          className="rounded-2xl bg-elevated border border-line overflow-hidden"
          aria-label={dict.finalVideoLabel}
        >
          <div className="aspect-video flex flex-col items-center justify-center gap-4 bg-brand-muted">
            <PlayCircle size={52} className="text-brand opacity-50" />
            <p className="text-sm text-ink-2 text-center px-6">{dict.finalVideoComingSoon}</p>
          </div>

          {DEV_BYPASS && !watched && (
            <div className="border-t border-line p-4">
              <button
                type="button"
                onClick={() => setWatched(true)}
                className="w-full py-2.5 rounded-xl border border-dashed border-brand-light text-sm text-brand hover:bg-brand-muted transition-colors"
              >
                {dict.finalMarkWatched}
              </button>
            </div>
          )}

          {watched && (
            <div className="border-t border-line px-4 py-3 flex items-center gap-2">
              <CheckCircle size={16} className="text-success" />
              <span className="text-sm text-success font-medium">{dict.finalWatchedBadge}</span>
            </div>
          )}
        </div>

        {!watched && (
          <p className="text-xs text-ink-3 text-center">{dict.finalWatchFirst}</p>
        )}

        {/* Habit chat — enabled only after video watched */}
        <div className="space-y-2">
          <h2 className="text-sm font-semibold text-ink">{audioDict.chatSectionTitle}</h2>
          <p className="text-xs text-ink-3">{audioDict.chatSectionSubtitle}</p>
          <OnboardingHabitChat
            dict={{
              startRecording: audioDict.startRecording,
              stopRecording: audioDict.stopRecording,
              cancelRecording: audioDict.cancelRecording,
              sendAudio: audioDict.sendAudio,
              recording: audioDict.recording,
              uploading: audioDict.uploading,
              permissionDenied: audioDict.permissionDenied,
              unsupportedBrowser: audioDict.unsupportedBrowser,
              noMicrophone: audioDict.noMicrophone,
              audioPreview: audioDict.audioPreview,
              recordingDuration: audioDict.recordingDuration,
              uploadFailed: audioDict.uploadFailed,
              uploadSuccess: audioDict.uploadSuccess,
              labelPlay: audioDict.labelPlay,
              labelPause: audioDict.labelPause,
              labelReset: audioDict.labelReset,
              textPlaceholder: audioDict.textPlaceholder,
              sendText: audioDict.sendText,
              historyEmpty: audioDict.historyEmpty,
              transcriptionPending: audioDict.transcriptionPending,
              transcriptionNotConfigured: audioDict.transcriptionNotConfigured,
              processing: audioDict.processing,
            }}
            enabled={watched}
          />
        </div>

        {apiError && (
          <p className="text-sm text-error bg-error/10 rounded-xl px-4 py-3">{apiError}</p>
        )}
      </div>

      <div className="px-6 pb-safe pb-8 pt-4 border-t border-line">
        <button
          type="button"
          onClick={onComplete}
          disabled={!watched || isSubmitting}
          className={cn(
            'w-full py-3.5 rounded-2xl font-semibold text-base transition-all',
            watched && !isSubmitting
              ? 'bg-brand text-white'
              : 'bg-line text-ink-3 cursor-not-allowed',
          )}
        >
          {isSubmitting ? dict.finalCompleting : dict.finalComplete}
        </button>
      </div>
    </div>
  )
}
