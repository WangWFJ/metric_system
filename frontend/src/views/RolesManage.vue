<template>
  <div class="manage-container">
    <el-card shadow="never">
      <div style="display:flex; gap:8px; align-items:center; margin-bottom:10px;">
        <el-input v-model="q" placeholder="搜索角色名称或编码" clearable style="width:280px" @keyup.enter="fetch" />
        <el-select v-model="status" placeholder="状态" clearable style="width:160px" @change="fetch">
          <el-option :value="1" label="启用" />
          <el-option :value="0" label="禁用" />
        </el-select>
        <el-button type="primary" @click="fetch">查询</el-button>
        <el-button type="success" @click="openCreate">新增角色</el-button>
      </div>
      <el-table :data="rows" v-loading="loading" style="width:100%">
        <el-table-column prop="role_id" label="ID" width="90" />
        <el-table-column prop="role_code" label="编码" min-width="180" />
        <el-table-column prop="role_name" label="名称" min-width="180" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="scope">
            <el-tag :type="scope.row.status === 1 ? 'success' : 'info'">{{ scope.row.status === 1 ? '启用' : '禁用' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180">
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

    <el-dialog v-model="dialog" :title="editId ? '编辑角色' : '新增角色'" width="600px" destroy-on-close>
      <el-form :model="form" label-width="110px">
        <el-form-item label="编码" required><el-input v-model="form.role_code" :disabled="!!editId" /></el-form-item>
        <el-form-item label="名称" required><el-input v-model="form.role_name" /></el-form-item>
        <el-form-item label="状态" required>
          <el-select v-model="form.status" style="width:100%">
            <el-option :value="1" label="启用" />
            <el-option :value="0" label="禁用" />
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
import { ref } from 'vue'
import { listRolesForPerm as listRoles, createRole, updateRole, deleteRole, type RoleItem } from '@/api/permission'
import { ElMessage } from 'element-plus'

const q = ref('')
const status = ref<number | undefined>(undefined)
const rows = ref<RoleItem[]>([])
const total = ref(0)
const page = ref(1)
const size = ref(20)
const loading = ref(false)
const dialog = ref(false)
const editId = ref<number | null>(null)
const form = ref<RoleItem>({ role_id: 0, role_code: '', role_name: '', status: 1 } as any)

const fetch = async () => {
  loading.value = true
  try {
    const res = await listRoles()
    rows.value = (status.value === undefined ? res : res.filter(r => r.status === status.value)).filter(r => !q.value || (r.role_name + r.role_code).includes(q.value))
    total.value = rows.value.length
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '加载失败')
  } finally {
    loading.value = false
  }
}

const openCreate = () => {
  editId.value = null
  form.value = { role_id: 0, role_code: '', role_name: '', status: 1 } as any
  dialog.value = true
}

const openEdit = (row: RoleItem) => {
  editId.value = row.role_id
  form.value = { ...row } as any
  dialog.value = true
}

const submit = async () => {
  try {
    if (editId.value) {
      await updateRole(editId.value, { role_name: (form.value as any).role_name, status: (form.value as any).status })
      ElMessage.success('已更新')
    } else {
      await createRole({ role_code: (form.value as any).role_code, role_name: (form.value as any).role_name, status: (form.value as any).status })
      ElMessage.success('已新增')
    }
    dialog.value = false
    fetch()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '保存失败')
  }
}

const handleDelete = async (row: RoleItem) => {
  try {
    await deleteRole(row.role_id)
    ElMessage.success('已删除')
    fetch()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '删除失败')
  }
}

fetch()
</script>

<style scoped>
.manage-container { padding: 10px; }
</style>
