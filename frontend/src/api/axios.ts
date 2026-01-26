import axios from 'axios'
import { ElMessage } from 'element-plus'
import router from '@/router'

const service = axios.create({
  baseURL: '/api/v1', // Base URL for API requests
  timeout: 10000, // Request timeout
})

// Request interceptor
service.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor
service.interceptors.response.use(
  (response) => {
    return response.data
  },
  (error) => {
    console.error('API Error:', error)
    const status = error.response ? error.response.status : null
    const message = error.response?.data?.detail || error.message || 'Error'

    const url = error.config?.url || ''
    if (status === 401) {
      if (url.includes('/users/login')) {
        // 登录失败由调用方处理提示文案
      } else {
        ElMessage.error('会话已过期，请重新登录。')
        localStorage.removeItem('token')
        router.push('/login')
      }
    } else {
      ElMessage.error(message)
    }
    return Promise.reject(error)
  }
)

export default service
