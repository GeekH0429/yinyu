import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'
import AutoImport from 'unplugin-auto-import/vite'
import Components from 'unplugin-vue-components/vite'
import { ElementPlusResolver } from 'unplugin-vue-components/resolvers'
import viteCompression from 'vite-plugin-compression'

export default defineConfig({
  plugins: [
    vue(),
    // ElMessage / ElMessageBox / ElNotification / ElLoading 等命令式 API 自动导入
    // (.js 模块里已显式 import 的也仍正常工作)。dts 关闭,本仓库非 TS。
    AutoImport({
      resolvers: [ElementPlusResolver()],
      dts: false
    }),
    // <el-xxx> 组件按模板使用情况自动按需引入,无需 app.use(ElementPlus)
    Components({
      resolvers: [ElementPlusResolver()],
      dts: false
    }),
    // 生成 .gz 预压缩文件,配合 Nginx gzip_static 直接吐出,免去运行时压缩
    viteCompression({
      algorithm: 'gzip',
      ext: '.gz',
      threshold: 10240,
      deleteOriginFile: false
    })
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  server: {
    host: '0.0.0.0',
    port: 5173,
    proxy: {
      '/api': { target: 'http://localhost:8000', changeOrigin: true },
      '/uploads': { target: 'http://localhost:8000', changeOrigin: true }
    }
  },
  build: {
    rollupOptions: {
      output: {
        // 把大依赖拆成独立 chunk,避免单 chunk 过大、改善缓存命中
        manualChunks: {
          echarts: ['echarts', 'vue-echarts'],
          tiptap: [
            '@tiptap/vue-3',
            '@tiptap/starter-kit',
            '@tiptap/extension-image',
            '@tiptap/extension-link',
            '@tiptap/extension-placeholder',
            '@tiptap/extension-underline'
          ]
        }
      }
    }
  }
})
