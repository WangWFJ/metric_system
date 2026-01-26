<template>
  <el-container class="layout-container">
    <el-aside width="220px" class="aside">
      <div class="logo">
        <h2>指标数据管理系统</h2>
      </div>
      <el-menu
        router
        :default-active="$route.path"
        class="el-menu-vertical"
        background-color="transparent"
        text-color="#334155"
        active-text-color="#2F76F6"
      >
        <el-sub-menu index="/indicator-data-sub" v-if="hasPerm('indicator_data:view')">
          <template #title>
            <el-icon><DataLine /></el-icon>
            <span>指标数据</span>
          </template>
          <el-menu-item index="/dashboard">区县明细</el-menu-item>
          <el-menu-item index="/center-dashboard">支撑中心明细</el-menu-item>
          <el-menu-item index="/indicator-compare">图表显示</el-menu-item>
          <el-menu-item index="/big-screen">数据大屏</el-menu-item>
        </el-sub-menu>
        <el-sub-menu index="/indicator-sub" v-if="hasPerm('indicator:view') || hasPerm('indicator:add') || hasPerm('indicator:edit')">
          <template #title>
            <el-icon><DataLine /></el-icon>
            <span>指标管理</span>
          </template>
          <el-menu-item index="/indicators">指标管理</el-menu-item>
          <el-menu-item index="/majors">专业管理</el-menu-item>
          <el-menu-item index="/evaluation-types">考核类型管理</el-menu-item>
        </el-sub-menu>
        <el-sub-menu index="/users-sub" v-if="showAdminMenus">
          <template #title>
            <el-icon><User /></el-icon>
            <span>用户管理</span>
          </template>
          <el-menu-item index="/users">用户管理</el-menu-item>
          <el-menu-item index="/permissions">权限管理</el-menu-item>
          <el-menu-item index="/roles">角色管理</el-menu-item>
          <el-menu-item index="/role-permissions">角色授权</el-menu-item>
        </el-sub-menu>
      </el-menu>
      <div class="aside-bottom">
        <el-menu router :default-active="$route.path" class="bottom-menu" background-color="transparent" text-color="#334155" active-text-color="#2F76F6">
          <el-menu-item index="/settings">
            <el-icon><User /></el-icon>
            <span>个人设置</span>
          </el-menu-item>
        </el-menu>
      </div>
    </el-aside>
    <el-container>
      <el-header class="header">
        <div class="header-content">
          <div class="breadcrumb">
            <!-- Breadcrumb can be added here -->
          </div>
          <div class="user-info">
            <span v-if="userStore.user" class="username">{{ userStore.user.username }}</span>
            <el-button type="danger" size="small" @click="logout">退出登录</el-button>
          </div>
        </div>
      </el-header>
      <el-main class="main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { onMounted, watch, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/store/user'
import { DataLine, User } from '@element-plus/icons-vue'

const router = useRouter()
const userStore = useUserStore()

const logout = () => {
  userStore.logout()
  router.push('/login')
}

onMounted(() => {
  if (userStore.token && !userStore.user) {
    userStore.fetchUser()
  }
})

watch(() => userStore.token, (tok) => {
  if (tok) userStore.fetchUser()
})

const hasPerm = (code: string) => {
  return (userStore.permissions || []).includes(code)
}

const showAdminMenus = computed(() => hasPerm('user:manage'))
</script>

<style scoped>
.layout-container {
  height: 100vh;
}
.aside {
  background: linear-gradient(180deg, #F7FAFF 0%, #EDF5FF 100%);
  color: #334155;
  display: flex;
  flex-direction: column;
}
.aside-bottom {
  margin-top: auto;
}
.bottom-menu {
  border-top: 1px solid #e5ebf3;
}
.logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #EAF3FF;
}
.logo h2 {
  margin: 0;
  color: #1E2A78;
  font-size: 18px;
}
.el-menu-vertical {
  border-right: none;
  flex: 1;
}
.header {
  background: linear-gradient(90deg, #EAF3FF 0%, #D7E7FF 100%);
  border-bottom: 1px solid #e5eaf3;
  display: flex;
  align-items: center;
  padding: 0 20px;
  height: 60px;
}
.header-content {
  display: flex;
  justify-content: space-between;
  width: 100%;
  align-items: center;
}
.username {
  margin-right: 15px;
  font-weight: bold;
}
.main {
  background-color: #FAFBFF;
  padding: 20px;
}

:deep(.el-menu-item), :deep(.el-sub-menu__title) {
  border-radius: 12px;
  margin: 4px 8px;
}
:deep(.el-menu-item.is-active), :deep(.el-sub-menu__title.is-active) {
  background-color: #E6F0FF !important;
  color: #2F76F6 !important;
}
:deep(.el-menu-item:hover), :deep(.el-sub-menu__title:hover) {
  background-color: #F0F6FF;
}
</style>
