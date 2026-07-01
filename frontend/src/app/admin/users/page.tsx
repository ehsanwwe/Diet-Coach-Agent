'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import AdminShell from '../AdminShell'
import { adminApi, AdminApiError, AdminUserListItem } from '@/lib/admin-api'

function formatDate(iso: string | null): string {
  if (!iso) return '—'
  return new Date(iso).toLocaleDateString('fa-IR', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
}

export default function AdminUsersPage() {
  const [users, setUsers] = useState<AdminUserListItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    adminApi.listUsers()
      .then(setUsers)
      .catch((err: unknown) => {
        if (err instanceof AdminApiError) {
          setError(err.message)
        } else {
          setError('خطا در بارگذاری کاربران')
        }
      })
      .finally(() => setLoading(false))
  }, [])

  return (
    <AdminShell>
      <div className="max-w-5xl">
        <h1 className="text-lg font-semibold text-stone-800 mb-5">مدیریت کاربران</h1>

        {loading && (
          <p className="text-stone-400 text-sm">در حال بارگذاری...</p>
        )}

        {error && (
          <div className="bg-red-50 text-red-600 rounded-xl px-4 py-3 text-sm">
            {error}
          </div>
        )}

        {!loading && !error && users.length === 0 && (
          <p className="text-stone-400 text-sm">هیچ کاربری ثبت نشده است.</p>
        )}

        {!loading && !error && users.length > 0 && (
          <div className="bg-white rounded-2xl border border-stone-100 overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-stone-50 border-b border-stone-100">
                <tr>
                  <th className="px-4 py-3 text-right font-medium text-stone-500">نام / شماره</th>
                  <th className="px-4 py-3 text-right font-medium text-stone-500">زبان</th>
                  <th className="px-4 py-3 text-right font-medium text-stone-500">ثبت‌نام</th>
                  <th className="px-4 py-3 text-right font-medium text-stone-500">آخرین فعالیت</th>
                  <th className="px-4 py-3 text-right font-medium text-stone-500">وضعیت</th>
                  <th className="px-4 py-3"></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-stone-50">
                {users.map((user) => (
                  <tr key={user.id} className="hover:bg-stone-50/50 transition-colors">
                    <td className="px-4 py-3">
                      <p className="font-medium text-stone-800">
                        {user.full_name ?? '—'}
                      </p>
                      <p className="text-xs text-stone-400 mt-0.5 font-mono">{user.phone}</p>
                    </td>
                    <td className="px-4 py-3 text-stone-600">
                      {user.language ?? '—'}
                    </td>
                    <td className="px-4 py-3 text-stone-500">
                      {formatDate(user.created_at)}
                    </td>
                    <td className="px-4 py-3 text-stone-500">
                      {formatDate(user.latest_activity)}
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={`inline-block px-2 py-0.5 rounded-full text-xs font-medium ${
                          user.is_onboarded
                            ? 'bg-green-50 text-green-600'
                            : 'bg-amber-50 text-amber-600'
                        }`}
                      >
                        {user.is_onboarded ? 'ثبت‌نام کامل' : 'ناقص'}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <Link
                        href={`/admin/users/${user.id}`}
                        className="text-stone-500 hover:text-stone-700 text-xs underline-offset-2 hover:underline"
                      >
                        مشاهده
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </AdminShell>
  )
}
