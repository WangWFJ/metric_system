<template>
  <div class="manage-container">
    <el-card shadow="never">
      <div style="display:flex; gap:8px; align-items:center; margin-bottom:10px;">
        <el-input v-model="q" placeholder="搜索用户名或手机号" clearable style="width:280px" @keyup.enter="fetch" />
        <el-select v-model="filterRoleId" placeholder="筛选角色" clearable style="width:220px" @change="fetch">
          <el-option v-for="r in roles" :key="r.role_id" :label="r.role_name" :value="r.role_id" />
        </el-select>
        <el-select v-model="filterStatus" placeholder="状态" clearable style="width:160px" @change="fetch">
          <el-option :value="1" label="启用" />
          <el-option :value="0" label="锁定" />
        </el-select>
        <el-button type="primary" @click="fetch">查询</el-button>
        <el-button type="success" @click="openCreate">新增用户</el-button>
      </div>
      <el-table :data="rows" v-loading="loading" style="width:100%">
        <el-table-column prop="id" label="ID" width="100" />
        <el-table-column prop="username" label="用户名" min-width="160" />
        <el-table-column prop="phone" label="手机号" width="140" />
        <el-table-column prop="role_id" label="角色" width="160">
          <template #default="scope">
            <span>{{ (roles.find(r => r.role_id === scope.row.role_id) || {}).role_name || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="scope">
            <el-tag :type="scope.row.status === 1 ? 'success' : 'danger'">{{ scope.row.status === 1 ? '启用' : '锁定' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200">
          <template #default="scope">
            <el-button link type="primary" size="small" @click="openEdit(scope.row)">编辑</el-button>
            <el-button link type="danger" size="small" @click="handleDelete(scope.row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <div style="display:flex; justify-content:flex-end; margin-top:10px;">
        <el-pagination
          v-model:current-page="page"
          v-model:page-size="size"
          :page-sizes="[10,20,50,100]"
          layout="total, sizes, prev, pager, next, jumper"
          :total="total"
          @size-change="fetch"
          @current-change="fetch"
        />
      </div>
    </el-card>

    <el-dialog v-model="dialog" :title="editId ? '编辑用户' : '新增用户'" width="600px" destroy-on-close>
      <el-form :model="form" label-width="110px">
        <el-form-item label="用户名" required><el-input v-model="form.username" :disabled="!!editId" /></el-form-item>
        <el-form-item label="密码"><el-input v-model="form.password" type="password" placeholder="不填则默认 cmcc123456" /></el-form-item>
        <el-form-item label="手机号" :required="!editId"><el-input v-model="form.phone" /></el-form-item>
        <el-form-item label="角色" required>
          <el-select v-model="form.role_id" placeholder="选择角色" filterable style="width:100%">
            <el-option v-for="r in roles" :key="r.role_id" :label="r.role_name" :value="r.role_id" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态" required>
          <el-select v-model="form.status" style="width:100%">
            <el-option :value="1" label="启用" />
            <el-option :value="0" label="锁定" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialog=false">取消</el-button>
          <el-button type="primary" @click="submit">保存</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { listUsers, createUserAdmin, updateUserAdmin, deleteUserAdmin, listRolesAdmin, type RoleItem, type PageResp } from '@/api/user'
import { ElMessage } from 'element-plus'

const q = ref('')
const filterRoleId = ref<number | undefined>(undefined)
const filterStatus = ref<number | undefined>(undefined)

type Row = { id: number; username: string; phone?: string; role_id: number; status: number }
const rows = ref<Row[]>([])
const total = ref(0)
const page = ref(1)
const size = ref(20)
const loading = ref(false)

const roles = ref<RoleItem[]>([])

const dialog = ref(false)
const form = ref<Row & { password?: string }>({ id: 0, username: '', phone: '', role_id: 1, status: 1 })
const editId = ref<number | null>(null)

const fetch = async () => {
  loading.value = true
  try {
    const res = await listUsers({ q: q.value, role_id: filterRoleId.value, status: filterStatus.value, page: page.value, size: size.value })
    rows.value = res.data as any
    total.value = res.total
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '加载失败')
  } finally {
    loading.value = false
  }
}

const openCreate = () => {
  editId.value = null
  form.value = { id: 0, username: '', phone: '', role_id: (roles.value[0]?.role_id || 1), status: 1 }
  dialog.value = true
}

const openEdit = (row: Row) => {
  editId.value = row.id
  form.value = { ...row }
  form.value.password = ''
  dialog.value = true
}

const submit = async () => {
  try {
    if (editId.value) {
      const payload: any = { phone: form.value.phone, role_id: form.value.role_id, status: form.value.status }
      if (form.value.password) payload.password = form.value.password
      await updateUserAdmin(editId.value, payload)
      ElMessage.success('已更新')
    } else {
      if (!form.value.phone) { ElMessage.warning('请填写手机号'); return }
      const payload: any = { username: form.value.username, phone: form.value.phone, role_id: form.value.role_id, status: form.value.status }
      if (form.value.password) payload.password = form.value.password
      await createUserAdmin(payload)
      ElMessage.success('已新增')
    }
    dialog.value = false
    fetch()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '保存失败')
  }
}

const handleDelete = async (row: Row) => {
  try {
    await deleteUserAdmin(row.id)
    ElMessage.success('已删除')
    fetch()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '删除失败')
  }
}

onMounted(async () => {
  try {
    roles.value = await listRolesAdmin()
  } catch {}
  fetch()
})
</script>

<style scoped>
.manage-container { padding: 10px; }
</style>
