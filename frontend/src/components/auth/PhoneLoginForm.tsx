'use client'

import { useState, useMemo } from 'react'
import { useRouter } from 'next/navigation'
import { AsYouType, isValidPhoneNumber, parsePhoneNumber } from 'libphonenumber-js'
import { ChevronDown, Search, X } from 'lucide-react'
import { cn } from '@/lib/cn'
import type { Dictionary } from '@/dictionaries/fa'
import type { Locale } from '@/lib/i18n'
import { requestOtp } from '@/lib/auth'
import { ApiRequestError } from '@/lib/api'
import { COUNTRIES, getDefaultCountry, type CountryEntry } from '@/lib/countries'

interface Props {
  dict: Dictionary['auth'] & Pick<Dictionary['common'], 'loading'>
  locale: Locale
}

export default function PhoneLoginForm({ dict, locale }: Props) {
  const router = useRouter()
  const [country, setCountry] = useState<CountryEntry>(() => getDefaultCountry(locale))
  const [localPhone, setLocalPhone] = useState('')
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [showCountryModal, setShowCountryModal] = useState(false)

  function handlePhoneChange(raw: string) {
    const formatter = new AsYouType(country.code)
    const formatted = formatter.input(raw.replace(/[^\d\s\-()]/g, ''))
    setLocalPhone(formatted)
    setError('')
  }

  function handleCountrySelect(c: CountryEntry) {
    setCountry(c)
    setLocalPhone('')
    setError('')
    setShowCountryModal(false)
  }

  function getE164(): string | null {
    try {
      const parsed = parsePhoneNumber(localPhone, country.code)
      if (parsed.isValid()) return parsed.format('E.164')
      return null
    } catch {
      return null
    }
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError('')

    if (!localPhone.trim()) {
      setError(dict.phoneError)
      return
    }

    const e164 = getE164()
    if (!e164 || !isValidPhoneNumber(localPhone, country.code)) {
      setError(dict.phoneInvalidForCountry)
      return
    }

    setIsLoading(true)
    try {
      await requestOtp(e164)
      const encoded = encodeURIComponent(e164)
      router.push(`/${locale}/login/verify?phone=${encoded}`)
    } catch (err) {
      if (err instanceof ApiRequestError) {
        if (err.status === 422) {
          setError(dict.phoneError)
        } else {
          setError(dict.networkError)
        }
      } else {
        setError(dict.networkError)
      }
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <>
      <form onSubmit={handleSubmit} noValidate className="w-full flex flex-col gap-5" style={{direction: 'ltr'}}>
        <div className="flex flex-col gap-1.5">
          <label className="text-sm font-medium text-ink-2">{dict.phoneLabel}</label>

          {/* Phone input row */}
          <div
            className={cn(
              'flex items-stretch rounded-2xl border overflow-hidden bg-elevated transition-colors',
              'focus-within:border-brand focus-within:ring-2 focus-within:ring-brand/20',
              error ? 'border-red-400' : 'border-line',
              isLoading ? 'opacity-60' : '',
            )}
          >
            {/* Country selector button */}
            <button
              type="button"
              onClick={() => setShowCountryModal(true)}
              disabled={isLoading}
              className="flex items-center gap-1.5 px-3 py-3 border-e border-line shrink-0 bg-elevated hover:bg-brand-muted transition-colors"
              aria-label={dict.countryLabel}
            >
              <span className="text-lg leading-none">{country.flag}</span>
              <span className="text-sm font-medium text-ink-2 tabular-nums" dir="ltr">
                {country.dialCode}
              </span>
              <ChevronDown size={14} className="text-ink-3" />
            </button>

            {/* Phone number input */}
            <input
              id="phone"
              type="tel"
              inputMode="tel"
              dir="ltr"
              autoComplete="tel-national"
              autoFocus
              value={localPhone}
              onChange={(e) => handlePhoneChange(e.target.value)}
              placeholder={country.code === 'IR' ? '09123456789' : '123456789'}
              disabled={isLoading}
              className="flex-1 px-3 py-3 text-base text-ink bg-transparent outline-none placeholder:text-ink-3 min-w-0"
            />
          </div>

          {error && (
            <p role="alert" className="text-sm text-red-500 ps-1">
              {error}
            </p>
          )}
        </div>

        <button
          type="submit"
          disabled={isLoading}
          className={cn(
            'w-full py-3.5 rounded-2xl text-base font-semibold transition-all',
            'bg-brand text-white shadow-sm',
            isLoading
              ? 'opacity-60 cursor-not-allowed'
              : 'hover:bg-brand-light active:scale-[0.98]',
          )}
        >
          {isLoading ? dict.loading : dict.sendOtp}
        </button>
      </form>

      {showCountryModal && (
        <CountrySelectorModal
          dict={dict}
          selected={country}
          onSelect={handleCountrySelect}
          onClose={() => setShowCountryModal(false)}
        />
      )}
    </>
  )
}

function CountrySelectorModal({
  dict,
  selected,
  onSelect,
  onClose,
}: {
  dict: Props['dict']
  selected: CountryEntry
  onSelect: (c: CountryEntry) => void
  onClose: () => void
}) {
  const [query, setQuery] = useState('')

  const filtered = useMemo(() => {
    const q = query.toLowerCase().trim()
    if (!q) return COUNTRIES
    return COUNTRIES.filter(
      (c) =>
        c.name.toLowerCase().includes(q) ||
        c.dialCode.includes(q) ||
        c.code.toLowerCase().includes(q),
    )
  }, [query])

  return (
    <div
      className="fixed inset-0 z-50 flex flex-col justify-end items-center"
      onClick={(e) => { if (e.target === e.currentTarget) onClose() }}
    >
      {/* Backdrop */}
      <div className="absolute inset-0 bg-ink/40" onClick={onClose} />

      {/* Sheet — constrained to app shell width, centered on desktop */}
      <div
        className="relative bg-elevated rounded-t-3xl flex flex-col max-h-[70vh] w-full"
        style={{ maxWidth: 'var(--app-max-width)' }}
      >
        {/* Handle */}
        <div className="flex justify-center pt-3 pb-1 shrink-0">
          <div className="w-10 h-1 rounded-full bg-line" />
        </div>

        {/* Header */}
        <div className="flex items-center justify-between px-5 pb-3 shrink-0">
          <span className="text-base font-semibold text-ink">{dict.countryLabel}</span>
          <button
            type="button"
            onClick={onClose}
            className="w-8 h-8 flex items-center justify-center rounded-full hover:bg-brand-muted transition-colors"
          >
            <X size={18} className="text-ink-2" />
          </button>
        </div>

        {/* Search */}
        <div className="px-4 pb-3 shrink-0">
          <div className="flex items-center gap-2 px-3 py-2 rounded-xl border border-line bg-surface">
            <Search size={16} className="text-ink-3 shrink-0" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder={dict.countrySearch}
              autoFocus
              className="flex-1 text-sm text-ink bg-transparent outline-none placeholder:text-ink-3"
            />
          </div>
        </div>

        {/* Country list */}
        <div className="overflow-y-auto flex-1 min-h-0">
          {filtered.length === 0 ? (
            <p className="text-sm text-ink-3 text-center py-8">{query}</p>
          ) : (
            filtered.map((c) => (
              <button
                key={c.code}
                type="button"
                onClick={() => onSelect(c)}
                className={cn(
                  'w-full flex items-center gap-3 px-5 py-3 transition-colors text-start',
                  selected.code === c.code
                    ? 'bg-brand-muted'
                    : 'hover:bg-surface active:bg-brand-muted',
                )}
              >
                <span className="text-2xl leading-none">{c.flag}</span>
                <span className="flex-1 text-sm text-ink">{c.name}</span>
                <span className="text-sm font-medium text-ink-3 tabular-nums" dir="ltr">
                  {c.dialCode}
                </span>
              </button>
            ))
          )}
          {/* Bottom safe area */}
          <div className="pb-safe pb-6" />
        </div>
      </div>
    </div>
  )
}
