/// <reference types="vite/client" />

declare module '*.vue' {
  import type { DefineComponent } from 'vue'
  const component: DefineComponent<{}, {}, any>
  export default component
}

interface ElectronAPI {
  selectDownloadDir: () => Promise<string | null>
  openFile: (path: string) => Promise<void>
  getBackendPort: () => number
}

interface Window {
  electronAPI?: ElectronAPI
}
