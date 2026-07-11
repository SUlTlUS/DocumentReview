import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/documents' },
    { path: '/upload', component: () => import('../views/Upload.vue') },
    { path: '/documents', component: () => import('../views/DocumentList.vue') },
    { path: '/documents/:id/review', component: () => import('../views/ReviewResult.vue') },
    { path: '/documents/:id/chat', component: () => import('../views/Chat.vue') },
  ],
  scrollBehavior: () => ({ top: 0 }),
})
router.afterEach(() => requestAnimationFrame(() => document.querySelector<HTMLElement>('#main-content')?.focus()))
export default router
