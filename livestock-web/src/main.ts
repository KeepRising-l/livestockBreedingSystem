import { createApp } from 'vue'
import { createPinia } from 'pinia'

import App from './App.vue'
import router from './router'
import { registerIcons } from './utils/icons'
import './styles/index.scss'

// Element Plus 按需引入后，ElMessage/ElMessageBox 等命令式组件的样式需手动引入
import 'element-plus/es/components/message/style/css'
import 'element-plus/es/components/message-box/style/css'
import 'element-plus/es/components/notification/style/css'
import 'element-plus/es/components/loading/style/css'

const app = createApp(App)

// 只注册实际用到的图标，避免全量注册拖慢渲染
registerIcons(app)

app.use(createPinia())
app.use(router)
app.mount('#app')
