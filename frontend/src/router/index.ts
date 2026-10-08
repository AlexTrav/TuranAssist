import { createRouter, createWebHistory } from 'vue-router'

// BASE_URL учитывает --base сборки ("/TuranAssist/" на GitHub Pages)
const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { path: '/', name: 'home', component: () => import('../views/HomeView.vue') },
    { path: '/chat', name: 'chat', component: () => import('../views/ChatView.vue') },
    { path: '/performance', name: 'performance', component: () => import('../views/PerformanceView.vue') },
    { path: '/about', name: 'about', component: () => import('../views/AboutView.vue') },
    { path: '/:pathMatch(.*)*', redirect: '/' },
  ],
  scrollBehavior() {
    return { top: 0 } // при переходе между страницами всегда наверх
  },
})

export default router
