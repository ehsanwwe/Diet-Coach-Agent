'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'

/** Root /admin redirects to /admin/users (the main useful page). */
export default function AdminRootPage() {
  const router = useRouter()
  useEffect(() => {
    router.replace('/admin/users')
  }, [router])
  return null
}
