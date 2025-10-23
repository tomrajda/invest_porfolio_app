import { createApp } from 'vue'
import './style.css'
import App from './App.vue'
import apiClient from './axios'
import './style.css'

const app = createApp(App)

// set API client as global property of Vue
app.config.globalProperties.$api = apiClient

app.mount('#app')