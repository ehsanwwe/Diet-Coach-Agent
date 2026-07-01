'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { adminApi, AdminApiError } from '@/lib/admin-api'
import { setAdminToken } from '@/lib/admin-storage'

export default function AdminLoginPage() {
  const router = useRouter()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    try {
      const res = await adminApi.login(username, password)
      setAdminToken(res.admin_token)
      router.replace('/admin/users')
    } catch (err) {
      if (err instanceof AdminApiError && err.status === 401) {
        setError('نام کاربری یا رمز عبور نادرست است')
      } else if (err instanceof AdminApiError && err.status === 503) {
        setError('پنل ادمین روی این سرور فعال نیست')
      } else {
        setError('خطایی رخ داد. لطفاً دوباره تلاش کنید.')
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <div className="w-full max-w-sm">
        <div className="bg-white rounded-2xl shadow-sm border border-stone-100 p-8">
          <h1 className="text-xl font-semibold text-stone-800 mb-1 text-center">
            ورود به ادمین
          </h1>
          <p className="text-sm text-stone-400 text-center mb-6">
            مربی تغذیه — پنل مدیریت
          </p>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-stone-600 mb-1">
                نام کاربری
              </label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
                autoComplete="username"
                className="w-full px-3 py-2 rounded-xl border border-stone-200 bg-stone-50
                           focus:outline-none focus:ring-2 focus:ring-stone-300
                           text-stone-800 text-sm"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-stone-600 mb-1">
                رمز عبور
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                autoComplete="current-password"
                className="w-full px-3 py-2 rounded-xl border border-stone-200 bg-stone-50
                           focus:outline-none focus:ring-2 focus:ring-stone-300
                           text-stone-800 text-sm"
              />
            </div>

            {error && (
              <p className="text-sm text-red-500 bg-red-50 rounded-xl px-3 py-2">
                {error}
              </p>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full py-2.5 rounded-xl bg-stone-700 text-white text-sm font-medium
                         hover:bg-stone-800 disabled:opacity-50 disabled:cursor-not-allowed
                         transition-colors"
            >
              {loading ? 'در حال ورود...' : 'ورود به ادمین'}
            </button>
          </form>
        </div>
      </div>
    </div>
  )
}
