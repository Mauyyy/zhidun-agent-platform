import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'

// 引入 Ant Design Vue 组件库及其核心样式
import Antd from 'ant-design-vue'
import 'ant-design-vue/dist/reset.css'
import '@/styles/global-theme.css'

const app = createApp(App)
const pinia = createPinia()

// 挂载路由和 UI 库
app.use(pinia)
app.use(router)
app.use(Antd)

app.mount('#app')