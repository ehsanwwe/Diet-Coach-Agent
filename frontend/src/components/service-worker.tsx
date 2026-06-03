'use client'
/**
 * Registers the PWA service worker on first client load.
 * Rendered as a transparent child of the root layout.
 */
import { useEffect } from 'react'

export function ServiceWorkerRegistration() {
  useEffect(() => {
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.register('/sw.js').catch(() => {
        // SW registration failure is non-fatal — app works without it
      })
    }
  }, [])

  return null
}
