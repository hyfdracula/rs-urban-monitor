import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: () => import('../views/HomeView.vue'),
    meta: { title: '总览' },
  },
  {
    path: '/compare',
    name: 'Compare',
    component: () => import('../views/CompareView.vue'),
    meta: { title: '双期对比' },
  },
  {
    path: '/custom-area',
    name: 'CustomArea',
    component: () => import('../views/CustomAreaView.vue'),
    meta: { title: '自定义研究区' },
  },
  {
    path: '/upload',
    name: 'Upload',
    component: () => import('../views/UploadView.vue'),
    meta: { title: '数据上传' },
  },
  {
    path: '/report',
    name: 'Report',
    component: () => import('../views/ReportView.vue'),
    meta: { title: '分析报告' },
  },
  {
    path: '/analysis/:taskId',
    name: 'Analysis',
    component: () => import('../views/AnalysisView.vue'),
    meta: { title: '分析结果' },
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('../views/NotFoundView.vue'),
    meta: { title: '页面未找到' },
  },
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
})

router.beforeEach((to) => {
  document.title = `${to.meta.title || '遥感城市监测'} - RS Urban Monitor`
})

export default router
