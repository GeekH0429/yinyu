import { defineConfig } from 'vite'
import uni from '@dcloudio/vite-plugin-uni'

// uni-app(vue3 + vite)配置
export default defineConfig({
  plugins: [uni()]
})
