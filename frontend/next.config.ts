import type { NextConfig } from 'next'

const nextConfig: NextConfig = {
  reactStrictMode: true,

  async headers() {
    return [
      {
        // Service worker must not be cached by the browser so updates deploy immediately
        source: '/sw.js',
        headers: [
          { key: 'Cache-Control', value: 'public, max-age=0, must-revalidate' },
          // Allows the SW to control the full origin scope
          { key: 'Service-Worker-Allowed', value: '/' },
        ],
      },
      {
        // PWA manifest — short cache, allow revalidation
        source: '/manifest.json',
        headers: [
          { key: 'Cache-Control', value: 'public, max-age=3600, must-revalidate' },
        ],
      },
    ]
  },
}

export default nextConfig
