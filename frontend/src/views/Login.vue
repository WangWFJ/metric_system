<template>
  <div class="login-page">
    <!-- 背景装饰 -->
    <div class="background-decoration">
      <div class="wave wave-1"></div>
      <div class="wave wave-2"></div>
      <div class="wave wave-3"></div>
    </div>
    
    <!-- 主卡片容器 -->
    <div class="login-card">
      <!-- 左侧插画区域 -->
      <div class="illustration-panel">
        <div class="illustration-content">
          <div class="welcome-scene">
            <div class="ribbon">
              <span class="welcome-text">欢迎登陆指标管理系统</span>
              </div>
            <div class="character character-left">👤</div>
            <div class="character character-right">👤</div>
          </div>
        </div>
      </div>
      
      <!-- 右侧表单区域 -->
      <div class="form-panel">
        <div class="form-content">
          <h1 class="form-title">登录</h1>
          <p class="form-subtitle">请登录以继续</p>
          
          <el-form :model="form" @submit.prevent="handleLogin" class="login-form">
            <el-form-item>
              <el-input 
                v-model="form.username" 
                placeholder="输入用户名或手机号"
                size="large"
                class="rounded-input"
              />
            </el-form-item>
            
            <el-form-item>
              <el-input 
                v-model="form.password" 
                type="password" 
                placeholder="密码"
                size="large"
                class="rounded-input"
                show-password
              />
            </el-form-item>
            
            <el-button 
              type="primary" 
              native-type="submit" 
              :loading="loading" 
              class="login-button"
              size="large"
            >
              登录
            </el-button>
          </el-form>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/store/user'
import { ElMessage } from 'element-plus'

const router = useRouter()
const userStore = useUserStore()
const loading = ref(false)

const form = reactive({
  username: '',
  password: ''
})

const handleLogin = async () => {
  if (!form.username || !form.password) {
    ElMessage.warning('请输入用户名或手机号与密码')
    return
  }
  loading.value = true
  const res = await userStore.login({
    username: form.username,
    password: form.password
  })
  loading.value = false
  if (res.success) {
    ElMessage.success('登录成功')
    router.push('/dashboard')
  } else {
    ElMessage.error(res.message || '用户名或密码错误')
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
  background: linear-gradient(135deg, #E6F0FF 0%, #9CC7FF 100%);
}

/* 背景装饰 */
.background-decoration {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 1;
}

.wave {
  position: absolute;
  border-radius: 50%;
  opacity: 0.06;
}

.wave-1 {
  width: 600px;
  height: 600px;
  top: -300px;
  left: -300px;
  background: radial-gradient(circle, rgba(255,255,255,0.2) 0%, transparent 70%);
  animation: float 6s ease-in-out infinite;
}

.wave-2 {
  width: 800px;
  height: 800px;
  bottom: -400px;
  right: -400px;
  background: radial-gradient(circle, rgba(255,255,255,0.15) 0%, transparent 70%);
  animation: float 8s ease-in-out infinite reverse;
}

.wave-3 {
  width: 400px;
  height: 400px;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  background: radial-gradient(circle, rgba(255,255,255,0.12) 0%, transparent 70%);
  animation: float 10s ease-in-out infinite;
}

@keyframes float {
  0%, 100% { transform: translateY(0px) scale(1); }
  50% { transform: translateY(-20px) scale(1.05); }
}

/* 主卡片 */
.login-card {
  display: flex;
  background: white;
  border-radius: 28px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.10);
  overflow: hidden;
  z-index: 2;
  max-width: 900px;
  width: 90%;
  min-height: 500px;
}

/* 左侧插画面板 */
.illustration-panel {
  flex: 1;
  background: linear-gradient(135deg, #F3F8FF 0%, #D7E7FF 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px;
  position: relative;
}

.illustration-content {
  text-align: center;
  position: relative;
}

.welcome-scene {
  position: relative;
  display: inline-block;
}

.ribbon {
  background: linear-gradient(45deg, #8BB4FF, #A78BFA);
  padding: 12px 24px;
  border-radius: 25px;
  box-shadow: 0 4px 15px rgba(139, 180, 255, 0.25);
  position: relative;
  z-index: 2;
}

.welcome-text {
  color: #FFFFFF;
  font-family: 'Brush Script MT', cursive;
  font-size: 24px;
  font-weight: bold;
  letter-spacing: 1px;
}

.character {
  position: absolute;
  font-size: 32px;
  top: 50%;
  transform: translateY(-50%);
  z-index: 1;
}

.character-left {
  left: -40px;
}

.character-right {
  right: -40px;
}

/* 右侧表单面板 */
.form-panel {
  flex: 1;
  padding: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.form-content {
  width: 100%;
  max-width: 320px;
}

.form-title {
  color: #1E2A78;
  font-size: 32px;
  font-weight: bold;
  margin: 0 0 8px 0;
  text-align: left;
}

.form-subtitle {
  color: #8A90A0;
  font-size: 14px;
  margin: 0 0 32px 0;
  text-align: left;
}

.login-form {
  margin-bottom: 24px;
}

.rounded-input {
  border-radius: 12px;
  background-color: #F8F9FA;
  border: 1px solid #E5E8F0;
}

.rounded-input :deep(.el-input__wrapper) {
  border-radius: 12px;
  background-color: #F8F9FA;
  box-shadow: none;
}

.rounded-input :deep(.el-input__inner) {
  color: #495057;
  font-size: 14px;
}

.form-options {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

/* 已移除保持登录复选框样式 */


.login-button {
  width: 100%;
  border-radius: 12px;
  background: linear-gradient(135deg, #8AB8FF 0%, #6F8CEB 100%);
  border: none;
  font-weight: bold;
  letter-spacing: 1px;
  transition: all 0.3s ease;
}

.login-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(47, 118, 246, 0.3);
}

/* 已移除忘记密码、分隔与社交登录相关样式 */

/* 响应式设计 */
@media (max-width: 768px) {
  .login-card {
    flex-direction: column;
    max-width: 400px;
    min-height: auto;
  }
  
  .illustration-panel {
    padding: 30px;
    min-height: 200px;
  }
  
  .form-panel {
    padding: 30px;
  }
  
  .form-title {
    font-size: 28px;
  }
  
  .welcome-text {
    font-size: 20px;
  }
}

@media (max-width: 480px) {
  .login-card {
    width: 95%;
    border-radius: 20px;
  }
  
  .form-panel {
    padding: 20px;
  }
  
  .form-title {
    font-size: 24px;
  }
  
  .social-login {
    gap: 12px;
  }
  
  .social-button {
    width: 42px;
    height: 42px;
    font-size: 16px;
  }
}
</style>
