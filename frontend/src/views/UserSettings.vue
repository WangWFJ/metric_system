<template>
  <div class="settings-container">
    <el-card shadow="never" style="margin-bottom: 12px;">
      <div style="font-weight: 600; margin-bottom: 8px;">修改密码</div>
      <el-form :model="pwdForm" label-width="110px" style="max-width: 520px;">
        <el-form-item label="当前密码" required>
          <el-input v-model="pwdForm.current_password" type="password" />
        </el-form-item>
        <el-form-item label="新密码" required>
          <el-input v-model="pwdForm.new_password" type="password" placeholder="至少8位，需包含字母与数字" />
          <div class="pwd-tip">新密码要求：至少 8 位，且同时包含字母与数字</div>
        </el-form-item>
        <el-form-item label="确认新密码" required>
          <el-input v-model="pwdForm.confirm_password" type="password" />
        </el-form-item>
        <el-button type="primary" @click="submitPwd" :loading="pwdLoading">保存</el-button>
      </el-form>
    </el-card>

    <el-card shadow="never">
      <div style="font-weight: 600; margin-bottom: 8px;">个人信息</div>
      <el-form :model="profileForm" label-width="110px" style="max-width: 520px;">
        <el-form-item label="用户名">
          <el-input :model-value="userStore.user?.username || ''" disabled />
        </el-form-item>
        <el-form-item label="手机号">
          <el-input v-model="profileForm.phone" />
        </el-form-item>
        <el-button type="primary" @click="submitProfile" :loading="profileLoading">保存</el-button>
      </el-form>
    </el-card>
  </div>
  </template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { updateMyPassword, updateMyProfile } from '@/api/user'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/store/user'

const pwdForm = ref({ current_password: '', new_password: '', confirm_password: '' })
const profileForm = ref<{ phone?: string }>({ phone: '' })
const pwdLoading = ref(false)
const profileLoading = ref(false)
const userStore = useUserStore()

onMounted(() => {
  if (!userStore.user) userStore.fetchUser()
  if (userStore.user?.phone) profileForm.value.phone = userStore.user.phone
})

const submitPwd = async () => {
  if (!pwdForm.value.current_password || !pwdForm.value.new_password || !pwdForm.value.confirm_password) {
    ElMessage.warning('请填写完整密码信息')
    return
  }
  const strong = pwdForm.value.new_password.length >= 8 && /[A-Za-z]/.test(pwdForm.value.new_password) && /\d/.test(pwdForm.value.new_password)
  if (!strong) {
    ElMessage.warning('新密码需至少8位并包含字母与数字')
    return
  }
  pwdLoading.value = true
  try {
    await updateMyPassword(pwdForm.value)
    ElMessage.success('密码已更新')
    pwdForm.value = { current_password: '', new_password: '', confirm_password: '' }
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '更新失败')
  } finally {
    pwdLoading.value = false
  }
}

const submitProfile = async () => {
  profileLoading.value = true
  try {
    await updateMyProfile({ phone: profileForm.value.phone })
    ElMessage.success('已保存')
    userStore.fetchUser()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '保存失败')
  } finally {
    profileLoading.value = false
  }
}
</script>

<style scoped>
.settings-container { padding: 10px; }
.pwd-tip { color: #909399; font-size: 12px; margin-top: 4px; }
</style>
