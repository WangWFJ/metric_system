import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import MainLayout from '@/layout/MainLayout.vue'
import Login from '@/views/Login.vue'
import Dashboard from '@/views/Dashboard.vue'
import IndicatorManage from '@/views/IndicatorManage.vue'
import MajorManage from '@/views/MajorManage.vue'
import UsersManage from '@/views/UsersManage.vue'
import UserSettings from '@/views/UserSettings.vue'
import PermissionsManage from '@/views/PermissionsManage.vue'
import RolePermissionAssign from '@/views/RolePermissionAssign.vue'
import RolesManage from '@/views/RolesManage.vue'
import EvaluationTypeManage from '@/views/EvaluationTypeManage.vue'
import CompareChart from '@/views/CompareChart.vue'
import BigScreen from '@/views/BigScreen.vue'
import CenterDashboard from '@/views/CenterDashboard.vue'

const routes: Array<RouteRecordRaw> = [
  {
    path: '/login',
    name: 'Login',
    component: Login,
    meta: { guest: true }
  },
  {
    path: '/',
    component: MainLayout,
    redirect: '/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: Dashboard,
        meta: { requiresAuth: true }
      }
      ,{
        path: 'indicators',
        name: 'IndicatorManage',
        component: IndicatorManage,
        meta: { requiresAuth: true }
      }
      ,{
        path: 'majors',
        name: 'MajorManage',
        component: MajorManage,
        meta: { requiresAuth: true }
      }
      ,{
        path: 'evaluation-types',
        name: 'EvaluationTypeManage',
        component: EvaluationTypeManage,
        meta: { requiresAuth: true }
      }
      ,{
        path: 'users',
        name: 'UsersManage',
        component: UsersManage,
        meta: { requiresAuth: true }
      }
      ,{
        path: 'permissions',
        name: 'PermissionsManage',
        component: PermissionsManage,
        meta: { requiresAuth: true }
      }
      ,{
        path: 'roles',
        name: 'RolesManage',
        component: RolesManage,
        meta: { requiresAuth: true }
      }
      ,{
        path: 'role-permissions',
        name: 'RolePermissionAssign',
        component: RolePermissionAssign,
        meta: { requiresAuth: true }
      }
      ,{
        path: 'settings',
        name: 'UserSettings',
        component: UserSettings,
        meta: { requiresAuth: true }
      }
      ,{
        path: 'indicator-compare',
        name: 'CompareChart',
        component: CompareChart,
        meta: { requiresAuth: true }
      }
      ,{
        path: 'big-screen',
        name: 'BigScreen',
        component: BigScreen,
        meta: { requiresAuth: true }
      }
      ,{
        path: 'center-dashboard',
        name: 'CenterDashboard',
        component: CenterDashboard,
        meta: { requiresAuth: true }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

function isTokenExpired(tok: string | null): boolean {
  if (!tok) return true
  const parts = tok.split('.')
  if (parts.length !== 3) return true
  try {
    const payload = JSON.parse(decodeURIComponent(escape(atob(parts[1].replace(/-/g, '+').replace(/_/g, '/')))))
    const exp = Number(payload.exp || 0)
    const now = Math.floor(Date.now() / 1000)
    return !exp || now >= exp
  } catch {
    return true
  }
}

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  const expired = isTokenExpired(token)
  if (expired) {
    localStorage.removeItem('token')
  }
  if (to.meta.requiresAuth && (!token || expired)) {
    next('/login')
  } else if (to.meta.guest && token && !expired) {
    next('/dashboard')
  } else {
    next()
  }
})

export default router
