import { createApp } from 'vue'
import App from './App.vue'
import { vReveal } from './directives/reveal'
import { i18n, initialLocale } from './i18n'
import router from './router'
import './style.css'

document.documentElement.lang = initialLocale

const app = createApp(App)

app.use(router)
app.use(i18n)
app.directive('reveal', vReveal) // плавное появление секций при скролле

app.mount('#app')
