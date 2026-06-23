'use client'

import { useCallback, useEffect, useRef, useState } from 'react'
import { useRouter } from 'next/navigation'
import { cn } from '@/lib/cn'
import type { Dictionary } from '@/dictionaries/fa'
import type { Locale } from '@/lib/i18n'
import { requestOtp, verifyOtp } from '@/lib/auth'
import { ApiRequestError } from '@/lib/api'

const RESEND_COOLDOWN = 60
const OTP_LENGTH = 6
const AUTO_SUBMIT_DELAY = 900

function toAsciiDigit(ch: string): string {
  // Persian digits ۰-۹ (U+06F0–U+06F9) and Arabic-Indic ٠-٩ (U+0660–U+0669)
  const code = ch.charCodeAt(0)
  if (code >= 0x06f0 && code <= 0x06f9) return String(code - 0x06f0)
  if (code >= 0x0660 && code <= 0x0669) return String(code - 0x0660)
  return ch
}

function normalizeDigits(s: string): string {
  return s.split('').map(toAsciiDigit).join('').replace(/\D/g, '')
}

interface Props {
  dict: Dictionary['auth'] & Pick<Dictionary['common'], 'loading'>
  locale: Locale
  phone: string
}

export default function OtpVerifyForm({ dict, locale, phone }: Props) {
  const router = useRouter()
  const [digits, setDigits] = useState<string[]>(Array(OTP_LENGTH).fill(''))
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [isComplete, setIsComplete] = useState(false)
  const [shake, setShake] = useState(false)
  const [countdown, setCountdown] = useState(RESEND_COOLDOWN)
  const inputRefs = useRef<(HTMLInputElement | null)[]>(Array(OTP_LENGTH).fill(null))
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const autoSubmitRef = useRef<ReturnType<typeof setTimeout> | null>(null)

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
    inputRefs.current[0]?.focus()
    return () => {
      if (timerRef.current) clearInterval(timerRef.current)
      if (autoSubmitRef.current) clearTimeout(autoSubmitRef.current)
    }
  }, [startCountdown])

  async function submitOtp(code: string) {
    setError('')
    setIsLoading(true)
    try {
      const tokenData = await verifyOtp(phone, code)
      router.push(
        tokenData.user.is_onboarded
          ? `/${locale}/dashboard`
          : `/${locale}/onboarding`,
      )
    } catch (err) {
      if (err instanceof ApiRequestError) {
        if (err.status === 400 || err.status === 401) {
          setError(dict.invalidOtp)
        } else if (err.status === 410) {
          setError(dict.otpExpired)
        } else {
          setError(dict.networkError)
        }
      } else {
        setError(dict.networkError)
      }
      setIsComplete(false)
      setShake(true)
      setTimeout(() => setShake(false), 600)
    } finally {
      setIsLoading(false)
    }
  }

  function handleChange(index: number, raw: string) {
    const digit = normalizeDigits(raw).slice(-1)
    if (!digit && raw !== '') return

    const next = [...digits]
    next[index] = digit
    setDigits(next)
    setError('')

    if (digit && index < OTP_LENGTH - 1) {
      inputRefs.current[index + 1]?.focus()
    }

    const code = next.join('')
    if (code.length === OTP_LENGTH && !next.includes('')) {
      setIsComplete(true)
      if (autoSubmitRef.current) clearTimeout(autoSubmitRef.current)
      autoSubmitRef.current = setTimeout(() => {
        submitOtp(code)
      }, AUTO_SUBMIT_DELAY)
    } else {
      setIsComplete(false)
      if (autoSubmitRef.current) clearTimeout(autoSubmitRef.current)
    }
  }

  function handleKeyDown(index: number, e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === 'Backspace') {
      if (digits[index]) {
        const next = [...digits]
        next[index] = ''
        setDigits(next)
        setIsComplete(false)
        if (autoSubmitRef.current) clearTimeout(autoSubmitRef.current)
      } else if (index > 0) {
        const next = [...digits]
        next[index - 1] = ''
        setDigits(next)
        setIsComplete(false)
        if (autoSubmitRef.current) clearTimeout(autoSubmitRef.current)
        inputRefs.current[index - 1]?.focus()
      }
      e.preventDefault()
    } else if (e.key === 'ArrowLeft') {
      if (index > 0) inputRefs.current[index - 1]?.focus()
    } else if (e.key === 'ArrowRight') {
      if (index < OTP_LENGTH - 1) inputRefs.current[index + 1]?.focus()
    } else if (e.key === 'Enter') {
      const code = digits.join('')
      if (code.length === OTP_LENGTH && !digits.includes('')) {
        if (autoSubmitRef.current) clearTimeout(autoSubmitRef.current)
        submitOtp(code)
      }
    }
  }

  function handlePaste(e: React.ClipboardEvent) {
    e.preventDefault()
    const pasted = normalizeDigits(e.clipboardData.getData('text')).slice(0, OTP_LENGTH)
    if (!pasted) return

    const next = Array(OTP_LENGTH).fill('')
    for (let i = 0; i < pasted.length; i++) {
      next[i] = pasted[i]
    }
    setDigits(next)
    setError('')

    const focusIdx = Math.min(pasted.length, OTP_LENGTH - 1)
    inputRefs.current[focusIdx]?.focus()

    if (pasted.length === OTP_LENGTH) {
      setIsComplete(true)
      if (autoSubmitRef.current) clearTimeout(autoSubmitRef.current)
      autoSubmitRef.current = setTimeout(() => {
        submitOtp(pasted)
      }, AUTO_SUBMIT_DELAY)
    }
  }

  function handleManualSubmit(e: React.FormEvent) {
    e.preventDefault()
    const code = digits.join('')
    if (code.length !== OTP_LENGTH || digits.includes('')) {
      setError(dict.otpError)
      return
    }
    if (autoSubmitRef.current) clearTimeout(autoSubmitRef.current)
    submitOtp(code)
  }

  async function handleResend() {
    if (countdown > 0) return
    setError('')
    setDigits(Array(OTP_LENGTH).fill(''))
    setIsComplete(false)
    inputRefs.current[0]?.focus()
    try {
      await requestOtp(phone)
      startCountdown()
    } catch (err) {
      if (err instanceof ApiRequestError) {
        setError(dict.networkError)
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
    <form onSubmit={handleManualSubmit} noValidate className="w-full flex flex-col gap-5">
      <div className="flex flex-col gap-3">
        {/* 6-digit boxes */}
        <div
          dir="ltr"
          className={cn(
            'flex gap-2 justify-center',
            shake && 'animate-[shake_0.5s_ease-in-out]',
          )}
          onPaste={handlePaste}
        >
          {digits.map((d, i) => (
            <input
              key={i}
              ref={(el) => { inputRefs.current[i] = el }}
              type="text"
              inputMode="numeric"
              autoComplete={i === 0 ? 'one-time-code' : 'off'}
              maxLength={2}
              value={d}
              onChange={(e) => handleChange(i, e.target.value)}
              onKeyDown={(e) => handleKeyDown(i, e)}
              disabled={isLoading}
              aria-label={`Digit ${i + 1}`}
              className={cn(
                'w-11 h-14 text-center text-xl font-semibold rounded-2xl border outline-none',
                'bg-elevated text-ink transition-all select-none',
                'focus:border-brand focus:ring-2 focus:ring-brand/20',
                isLoading && 'opacity-60 cursor-not-allowed',
                error
                  ? 'border-red-400 bg-red-50/40'
                  : d
                    ? 'border-brand/60 bg-brand-muted'
                    : 'border-line',
                isComplete && !error && 'border-brand bg-brand-muted animate-pulse',
              )}
            />
          ))}
        </div>

        {error && (
          <p role="alert" className="text-sm text-red-500 text-center">
            {error}
          </p>
        )}
      </div>

      <button
        type="submit"
        disabled={isLoading || digits.includes('')}
        className={cn(
          'w-full py-3.5 rounded-2xl text-base font-semibold transition-all',
          'bg-brand text-white shadow-sm',
          isLoading || digits.includes('')
            ? 'opacity-60 cursor-not-allowed'
            : 'hover:bg-brand-light active:scale-[0.98]',
        )}
      >
        {isLoading ? (
          <span className="flex items-center justify-center gap-2">
            <span className="w-4 h-4 rounded-full border-2 border-white/40 border-t-white animate-spin" />
            {dict.loading}
          </span>
        ) : (
          dict.verify
        )}
      </button>

      <button
        type="button"
        onClick={handleResend}
        disabled={countdown > 0 || isLoading}
        className={cn(
          'w-full py-2.5 text-sm transition-colors rounded-2xl',
          countdown > 0 || isLoading
            ? 'text-ink-3 cursor-not-allowed'
            : 'text-brand hover:bg-brand-muted',
        )}
      >
        {resendLabel}
      </button>
    </form>
  )
}
