'use client'

import { useCallback, useEffect, useRef, useState } from 'react'
import { useRouter } from 'next/navigation'
import type { Dictionary } from '@/dictionaries/fa'
import type { Locale } from '@/lib/i18n'
import { requestOtp, verifyOtp } from '@/lib/auth'
import { ApiRequestError } from '@/lib/api'

const RESEND_COOLDOWN = 60 // seconds

interface Props {
  dict: Dictionary['auth'] & Pick<Dictionary['common'], 'loading'>
  locale: Locale
  phone: string
}

export default function OtpVerifyForm({ dict, locale, phone }: Props) {
  const router = useRouter()
  const [otp, setOtp] = useState('')
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [countdown, setCountdown] = useState(RESEND_COOLDOWN)
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const startCountdown = useCallback(() => {
    setCountdown(RESEND_COOLDOWN)
    if (timerRef.current) clearInterval(timerRef.current)
    timerRef.current = setInterval(() => {
      setCountdown((prev) => {
        if (prev <= 1) {
          clearInterval(timerRef.current!)
          return 0
        }
        return prev - 1
      })
    }, 1000)
  }, [])

  useEffect(() => {
    startCountdown()
    return () => {
      if (timerRef.current) clearInterval(timerRef.current)
    }
  }, [startCountdown])

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError('')

    const code = otp.trim()
    if (!/^\d{6}$/.test(code)) {
      setError(dict.otpError)
      return
    }

    setIsLoading(true)
    try {
      await verifyOtp(phone, code)
      router.push(`/${locale}`)
    } catch (err) {
      if (err instanceof ApiRequestError) {
        setError(err.status === 400 ? dict.invalidOtp : err.message)
      } else {
        setError(dict.networkError)
      }
    } finally {
      setIsLoading(false)
    }
  }

  async function handleResend() {
    if (countdown > 0) return
    setError('')
    try {
      await requestOtp(phone)
      startCountdown()
    } catch (err) {
      if (err instanceof ApiRequestError) {
        setError(err.message)
      } else {
        setError(dict.networkError)
      }
    }
  }

  const resendLabel =
    countdown > 0
      ? dict.resendIn.replace('{seconds}', String(countdown))
      : dict.resend

  return (
    <form onSubmit={handleSubmit} noValidate className="w-full flex flex-col gap-5">
      <div className="flex flex-col gap-1.5">
        <label htmlFor="otp" className="text-sm font-medium text-ink-2">
          {dict.otpLabel}
        </label>
        <input
          id="otp"
          type="text"
          inputMode="numeric"
          autoComplete="one-time-code"
          dir="ltr"
          autoFocus
          maxLength={6}
          value={otp}
          onChange={(e) => setOtp(e.target.value.replace(/\D/g, ''))}
          placeholder={dict.otpPlaceholder}
          disabled={isLoading}
          className={[
            'w-full px-4 py-3 rounded-2xl border text-center text-xl tracking-[0.4em] font-mono',
            'text-ink bg-elevated placeholder:text-ink-3 outline-none transition-colors',
            'focus:border-brand focus:ring-2 focus:ring-brand/20',
            error ? 'border-red-400' : 'border-line',
            isLoading ? 'opacity-60 cursor-not-allowed' : '',
          ].join(' ')}
        />
        {error && (
          <p role="alert" className="text-sm text-red-500 ps-1">
            {error}
          </p>
        )}
      </div>

      <button
        type="submit"
        disabled={isLoading}
        className={[
          'w-full py-3.5 rounded-2xl text-base font-semibold transition-all',
          'bg-brand text-white shadow-sm',
          isLoading
            ? 'opacity-60 cursor-not-allowed'
            : 'hover:bg-brand-light active:scale-[0.98]',
        ].join(' ')}
      >
        {isLoading ? dict.loading : dict.verify}
      </button>

      <button
        type="button"
        onClick={handleResend}
        disabled={countdown > 0}
        className={[
          'w-full py-2.5 text-sm transition-colors rounded-2xl',
          countdown > 0
            ? 'text-ink-3 cursor-not-allowed'
            : 'text-brand hover:bg-brand-muted',
        ].join(' ')}
      >
        {resendLabel}
      </button>
    </form>
  )
}
