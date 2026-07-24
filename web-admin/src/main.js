import { createApp } from 'vue'
import { createPinia } from 'pinia'
// Element Plus 按需引入:组件由 unplugin-vue-components + ElementPlusResolver 自动导入,
// ElMessage / ElMessageBox 等命令式 API 由 unplugin-auto-import + ElementPlusResolver
// 自动导入(含相应 CSS)。各自文件中已显式 import 的也仍可正常工作。

import App from './App.vue'
import router from './router'
import './styles/main.css'

const app = createApp(App)

app.use(createPinia())
app.use(router)

app.mount('#app')
