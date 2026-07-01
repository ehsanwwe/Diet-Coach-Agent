'use client'

import { useEffect, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import Link from 'next/link'
import AdminShell from '../../AdminShell'
import { adminApi, AdminApiError, AdminUserDetail } from '@/lib/admin-api'

function Row({ label, value }: { label: string; value: string | number | null | undefined }) {
  return (
    <div className="flex justify-between py-2 border-b border-stone-50 last:border-0">
      <span className="text-stone-500 text-sm">{label}</span>
      <span className="text-stone-800 text-sm font-medium">{value ?? '—'}</span>
    </div>
  )
}

export default function AdminUserDetailPage() {
  const params = useParams()
  const router = useRouter()
  const userId = params?.userId as string

  const [user, setUser] = useState<AdminUserDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const [exportLoading, setExportLoading] = useState<string | null>(null)
  const [exportError, setExportError] = useState<string | null>(null)

  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false)
  const [deleteLoading, setDeleteLoading] = useState(false)
  const [deleteError, setDeleteError] = useState<string | null>(null)

  useEffect(() => {
    if (!userId) return
    adminApi.getUser(userId)
      .then(setUser)
      .catch((err: unknown) => {
        setError(err instanceof AdminApiError ? err.message : 'خطا در بارگذاری')
      })
      .finally(() => setLoading(false))
  }, [userId])

  const handleExport = async (type: 'onboarding' | 'chat' | 'nutrition' | 'all') => {
    setExportLoading(type)
    setExportError(null)
    try {
      await adminApi.downloadExport(userId, type)
    } catch {
      setExportError('خطا در دریافت فایل')
    } finally {
      setExportLoading(null)
    }
  }

  const handleDelete = async () => {
    setDeleteLoading(true)
    setDeleteError(null)
    try {
      await adminApi.deleteUser(userId)
      router.replace('/admin/users')
    } catch (err) {
      setDeleteError(err instanceof AdminApiError ? err.message : 'حذف با خطا مواجه شد')
      setDeleteLoading(false)
      setShowDeleteConfirm(false)
    }
  }

  return (
    <AdminShell>
      <div className="max-w-2xl">
        <div className="flex items-center gap-3 mb-6">
          <Link
            href="/admin/users"
            className="text-stone-400 hover:text-stone-600 text-sm"
          >
            → مدیریت کاربران
          </Link>
          <span className="text-stone-300">/</span>
          <span className="text-stone-600 text-sm">جزئیات کاربر</span>
        </div>

        {loading && <p className="text-stone-400 text-sm">در حال بارگذاری...</p>}
        {error && (
          <div className="bg-red-50 text-red-600 rounded-xl px-4 py-3 text-sm">{error}</div>
        )}

        {user && (
          <>
            {/* User info card */}
            <div className="bg-white rounded-2xl border border-stone-100 p-5 mb-4">
              <h1 className="font-semibold text-stone-800 mb-4">
                {user.full_name ?? 'کاربر بدون نام'}
              </h1>
              <Row label="شناسه" value={user.id} />
              <Row label="شماره تلفن" value={user.phone} />
              <Row label="زبان" value={user.language} />
              <Row label="جنسیت" value={user.gender} />
              <Row label="قد (cm)" value={user.height_cm} />
              <Row label="وزن (kg)" value={user.weight_kg} />
              <Row label="هدف وزنی (kg)" value={user.target_weight_kg} />
              <Row label="هدف تغذیه" value={user.goal_type} />
              <Row label="سطح ریسک" value={user.risk_level} />
              <Row label="جلسات چت" value={user.chat_session_count} />
              <Row label="پیام‌های چت" value={user.chat_message_count} />
              <Row label="برنامه تغذیه" value={user.nutrition_plan_count} />
              <Row
                label="ثبت‌نام"
                value={user.is_onboarded ? 'کامل' : 'ناقص'}
              />
              <Row
                label="تاریخ عضویت"
                value={new Date(user.created_at).toLocaleDateString('fa-IR')}
              />
            </div>

            {/* Export buttons */}
            <div className="bg-white rounded-2xl border border-stone-100 p-5 mb-4">
              <h2 className="text-sm font-medium text-stone-600 mb-3">دریافت داده‌ها</h2>
              {exportError && (
                <p className="text-xs text-red-500 mb-3">{exportError}</p>
              )}
              <div className="grid grid-cols-2 gap-2">
                {(
                  [
                    { type: 'chat', label: 'Export Json چت' },
                    { type: 'nutrition', label: 'Export Json رژیم' },
                    { type: 'onboarding', label: 'Export Json ثبت‌نام' },
                    { type: 'all', label: 'Export Json کامل' },
                  ] as const
                ).map(({ type, label }) => (
                  <button
                    key={type}
                    onClick={() => handleExport(type)}
                    disabled={exportLoading !== null}
                    className="px-3 py-2 rounded-xl border border-stone-200 text-sm text-stone-600
                               hover:bg-stone-50 disabled:opacity-50 disabled:cursor-not-allowed
                               transition-colors text-right"
                  >
                    {exportLoading === type ? 'در حال دریافت...' : label}
                  </button>
                ))}
              </div>
            </div>

            {/* Delete section */}
            <div className="bg-white rounded-2xl border border-red-100 p-5">
              <h2 className="text-sm font-medium text-red-600 mb-3">حذف کاربر</h2>

              {deleteError && (
                <p className="text-xs text-red-500 mb-3">{deleteError}</p>
              )}

              {!showDeleteConfirm ? (
                <button
                  onClick={() => setShowDeleteConfirm(true)}
                  className="px-4 py-2 rounded-xl border border-red-200 text-sm text-red-600
                             hover:bg-red-50 transition-colors"
                >
                  حذف کامل کاربر
                </button>
              ) : (
                <div className="space-y-3">
                  <div className="bg-red-50 rounded-xl px-4 py-3 text-sm text-red-700">
                    «این عملیات همه اطلاعات کاربر تستی را حذف می‌کند و قابل بازگشت نیست.»
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={handleDelete}
                      disabled={deleteLoading}
                      className="px-4 py-2 rounded-xl bg-red-600 text-white text-sm
                                 hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed
                                 transition-colors"
                    >
                      {deleteLoading ? 'در حال حذف...' : 'بله، حذف شود'}
                    </button>
                    <button
                      onClick={() => setShowDeleteConfirm(false)}
                      disabled={deleteLoading}
                      className="px-4 py-2 rounded-xl border border-stone-200 text-sm text-stone-600
                                 hover:bg-stone-50 disabled:opacity-50 transition-colors"
                    >
                      انصراف
                    </button>
                  </div>
                </div>
              )}
            </div>
          </>
        )}
      </div>
    </AdminShell>
  )
}
