import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { VitePWA } from 'vite-plugin-pwa'
import os from 'os'

/**
 * Detect the first non-internal IPv4 address on this machine.
 * Used so VITE_API_BASE can point to the LAN IP automatically.
 */
function getLocalIp(): string {
  const interfaces = os.networkInterfaces()
  for (const name of Object.keys(interfaces)) {
    for (const iface of interfaces[name] ?? []) {
      if (iface.family === 'IPv4' && !iface.internal) {
        return iface.address
      }
    }
  }
  return 'localhost'
}

const localIp = getLocalIp()

export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: 'autoUpdate',
      includeAssets: ['favicon.png', 'pwa-192x192.png', 'pwa-512x512.png'],
      manifest: {
        name: 'WATT-IF',
        short_name: 'WATT-IF',
        description: 'Household electricity forecast PWA',
        theme_color: '#1a1a2e',
        background_color: '#ffffff',
        display: 'standalone',
        icons: [
          { src: 'pwa-192x192.png', sizes: '192x192', type: 'image/png' },
          { src: 'pwa-512x512.png', sizes: '512x512', type: 'image/png' },
          { src: 'pwa-512x512.png', sizes: '512x512', type: 'image/png', purpose: 'any maskable' }
        ]
      },
      workbox: {
        runtimeCaching: [
          {
            // CacheFirst for static assets
            urlPattern: /\.(?:js|css|woff2?|png|jpg|svg)$/,
            handler: 'CacheFirst',
            options: {
              cacheName: 'static-assets',
              expiration: { maxAgeSeconds: 60 * 60 * 24 * 30 }
            }
          },
          {
            // NetworkFirst with 24h TTL for /forecast
            urlPattern: /\/forecast$/,
            handler: 'NetworkFirst',
            options: {
              cacheName: 'forecast-cache',
              expiration: { maxAgeSeconds: 60 * 60 * 24 }
            }
          },
          {
            // NetworkOnly for /ask (LLM responses must always be fresh)
            urlPattern: /\/ask$/,
            handler: 'NetworkOnly'
          }
        ]
      }
    })
  ],
  // Expose the auto-detected LAN IP as an env variable so the frontend
  // can reach the backend without hardcoding the IP in .env.local.
  define: {
    __LOCAL_IP__: JSON.stringify(localIp),
  },
  server: {
    host: '0.0.0.0', // listen on all interfaces for LAN access
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        rewrite: (path) => path.replace(/^\/api/, '')
      }
    }
  }
})
