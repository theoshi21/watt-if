// frontend/src/vite-env.d.ts

/// <reference types="vite/client" />

/** Auto-detected LAN IP injected by vite.config.ts */
declare const __LOCAL_IP__: string

interface ImportMetaEnv {
  readonly VITE_API_BASE?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}