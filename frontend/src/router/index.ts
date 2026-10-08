import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'

declare module 'vue-router' {
  interface RouteMeta {
    fullHeight?: boolean // чат занимает весь экран – без подвала
  }
}

// главная грузится сразу, остальные страницы – отдельными чанками при первом переходе
const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { path: '/', name: 'home', component: HomeView },
    { path: '/chat', name: 'chat', component: () => import('../views/ChatView.vue'), meta: { fullHeight: true } },
    { path: '/calculator', name: 'calculator', component: () => import('../views/CalculatorView.vue') },
    { path: '/knowledge', name: 'knowledge', component: () => import('../views/KnowledgeView.vue') },
    { path: '/performance', name: 'performance', component: () => import('../views/PerformanceView.vue') },
    { path: '/about', name: 'about', component: () => import('../views/AboutView.vue') },
    { path: '/:pathMatch(.*)*', redirect: '/' },
  ],
  scrollBehavior: (_to, _from, saved) => saved ?? { top: 0 },
})

export default router
