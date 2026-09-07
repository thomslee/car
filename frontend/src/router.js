import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/login', component: () => import('./views/LoginView.vue') },
  {
    path: '/',
    component: () => import('./views/LayoutView.vue'),
    children: [
      { path: '', component: () => import('./views/HomeView.vue'), meta: { title: '我的车辆' } },
      { path: 'users', component: () => import('./views/UserManageView.vue'), meta: { title: '用户管理', requiresAdmin: true } },
      { path: 'vehicle/new', component: () => import('./views/VehicleFormView.vue'), meta: { title: '添加车辆' } },
      { path: 'vehicle/:id/edit', component: () => import('./views/VehicleFormView.vue'), meta: { title: '编辑车辆' } },
      { path: 'vehicle/:id', component: () => import('./views/VehicleDetailView.vue'), meta: { title: '车辆主页' } },
      { path: 'vehicle/:id/archive', component: () => import('./views/VehicleArchiveDetailView.vue'), meta: { title: '车辆档案' } },
      { path: 'vehicle/:id/maintenance', component: () => import('./views/MaintenanceListView.vue'), meta: { title: '保养维修' } },
      { path: 'vehicle/:id/maintenance/:mid', component: () => import('./views/MaintenanceDetailView.vue'), meta: { title: '保养详情' } },
      { path: 'vehicle/:id/maintenance/new', component: () => import('./views/MaintenanceFormView.vue'), meta: { title: '录入保养' } },
      { path: 'vehicle/:id/maintenance/:mid/edit', component: () => import('./views/MaintenanceFormView.vue'), meta: { title: '编辑记录' } },
      { path: 'vehicle/:id/ocr', component: () => import('./views/OcrView.vue'), meta: { title: '扫描录入' } },
      { path: 'vehicle/:id/refuels', component: () => import('./views/RefuelListView.vue'), meta: { title: '加油记录' } },
      { path: 'vehicle/:id/refuels/:rid', component: () => import('./views/RefuelDetailView.vue'), meta: { title: '加油详情' } },
      { path: 'vehicle/:id/refuels/new', component: () => import('./views/RefuelFormView.vue'), meta: { title: '添加加油' } },
      { path: 'vehicle/:id/insurance', component: () => import('./views/InsuranceListView.vue'), meta: { title: '保险' } },
      { path: 'vehicle/:id/insurance/:iid', component: () => import('./views/InsuranceDetailView.vue'), meta: { title: '保单详情' } },
      { path: 'vehicle/:id/inspections', component: () => import('./views/InspectionListView.vue'), meta: { title: '年检' } },
      { path: 'vehicle/:id/violations', component: () => import('./views/ViolationListView.vue'), meta: { title: '违章' } },
      { path: 'vehicle/:id/ai', component: () => import('./views/AiView.vue'), meta: { title: 'AI 分析' } },
      { path: 'vehicle/:id/stats', component: () => import('./views/StatsView.vue'), meta: { title: '统计报表' } },
      { path: 'reminders', component: () => import('./views/ReminderView.vue'), meta: { title: '提醒中心' } },
      { path: 'settings', component: () => import('./views/SettingsView.vue'), meta: { title: '设置与模型' } }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to) => {
  const token = localStorage.getItem('car_token')
  const user = JSON.parse(localStorage.getItem('car_user') || 'null')
  if (!token && to.path !== '/login') return '/login'
  if (token && to.path === '/login') return '/'
  if (to.meta.requiresAdmin && user?.role !== 'admin') return '/'
  return true
})

export default router
