import { defineConfig } from 'vite'
import uni from '@dcloudio/vite-plugin-uni'

// uni-app(vue3 + vite)配置
export default defineConfig({
  plugins: [uni()],
  server: {
    // 暴露到局域网,真机/其他设备可通过电脑 IP 访问(Vite 默认只监听 localhost)
    host: true
  }
})
