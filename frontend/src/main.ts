import { createApp } from 'vue'
// шрифты сайта университета – локально, без запросов к Google Fonts (кириллица и казахские буквы включены)
import '@fontsource/ibm-plex-sans/400.css'
import '@fontsource/ibm-plex-sans/500.css'
import '@fontsource/ibm-plex-sans/600.css'
import '@fontsource/montserrat/600.css'
import '@fontsource/montserrat/700.css'
import '@fontsource/montserrat/800.css'
import '@fontsource/ibm-plex-mono/400.css'
import '@fontsource/ibm-plex-mono/500.css'
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
