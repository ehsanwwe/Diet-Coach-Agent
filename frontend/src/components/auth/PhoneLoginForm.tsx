'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import type { Dictionary } from '@/dictionaries/fa'
import type { Locale } from '@/lib/i18n'
import { requestOtp } from '@/lib/auth'
import { ApiRequestError } from '@/lib/api'

interface Props {
  dict: Dictionary['auth'] & Pick<Dictionary['common'], 'loading'>
  locale: Locale
}

export default function PhoneLoginForm({ dict, locale }: Props) {
  const router = useRouter()
  const [phone, setPhone] = useState('')
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(false)

  function validatePhone(value: string): boolean {
    return value.trim().length >= 7
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError('')

    if (!validatePhone(phone)) {
      setError(dict.phoneError)
      return
    }

    setIsLoading(true)
    try {
      await requestOtp(phone.trim())
      const encoded = encodeURIComponent(phone.trim())
      router.push(`/${locale}/login/verify?phone=${encoded}`)
    } catch (err) {
      if (err instanceof ApiRequestError) {
        setError(err.message)
      } else {
        setError(dict.networkError)
      }
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} noValidate className="w-full flex flex-col gap-5">
      <div className="flex flex-col gap-1.5">
        <label
          htmlFor="phone"
          className="text-sm font-medium text-ink-2"
        >
          {dict.phoneLabel}
        </label>
        <input
          id="phone"
          type="tel"
          inputMode="tel"
          dir="ltr"
          autoComplete="tel"
          autoFocus
          value={phone}
          onChange={(e) => setPhone(e.target.value)}
          placeholder={dict.phonePlaceholder}
          disabled={isLoading}
          className={[
            'w-full px-4 py-3 rounded-2xl border text-base text-ink bg-elevated',
            'placeholder:text-ink-3 outline-none transition-colors',
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
        {isLoading ? dict.loading : dict.sendOtp}
      </button>
    </form>
  )
}
