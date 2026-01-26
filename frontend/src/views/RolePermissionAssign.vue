<template>
  <div class="assign-container">
    <el-card shadow="never">
      <div style="display:flex; gap:8px; align-items:center; margin-bottom:10px;">
        <el-select v-model="roleId" placeholder="选择角色" style="width:260px" @change="loadRolePerms">
          <el-option v-for="r in roles" :key="r.role_id" :label="r.role_name" :value="r.role_id" />
        </el-select>
        <el-button type="primary" @click="openAddPerm" :disabled="!roleId">新增权限</el-button>
      </div>
      <el-table :data="assignedPerms" v-loading="loading" style="width:100%">
        <el-table-column prop="permission_code" label="编码" min-width="220" />
        <el-table-column prop="permission_name" label="名称" min-width="220" />
        <el-table-column prop="resource" label="资源" width="160" />
        <el-table-column prop="action" label="动作" width="120" />
        <el-table-column label="操作" width="140">
          <template #default="scope">
            <el-button link type="danger" size="small" @click="removePerm(scope.row)">移除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-dialog v-model="addDialog" title="新增角色权限" width="520px">
        <el-form label-width="110px">
        <el-form-item label="选择权限" required>
          <el-select v-model="addPermIds" multiple placeholder="选择未拥有的权限" filterable style="width:100%">
            <el-option v-for="p in unassignedPerms" :key="p.permission_id" :label="p.permission_name + '（' + p.permission_code + '）'" :value="p.permission_id" />
          </el-select>
        </el-form-item>
        </el-form>
        <template #footer>
          <span class="dialog-footer">
            <el-button @click="addDialog=false">取消</el-button>
            <el-button type="primary" @click="confirmAdd" :disabled="!addPermIds.length">确定</el-button>
          </span>
        </template>
      </el-dialog>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { listRolesForPerm, listPermissions, getRolePermissions, assignRolePermissions, revokeRolePermissions, type RoleItem, type PermissionItem } from '@/api/permission'
import { ElMessage } from 'element-plus'

const roles = ref<RoleItem[]>([])
const roleId = ref<number | undefined>(undefined)
const assignedPerms = ref<PermissionItem[]>([])
const unassignedPerms = ref<PermissionItem[]>([])
const loading = ref(false)
const addDialog = ref(false)
const addPermIds = ref<number[]>([])

const loadRolePerms = async () => {
  if (!roleId.value) return
  loading.value = true
  try {
    const owned = await listPermissions({ page: 1, size: 2000, role_id: roleId.value })
    assignedPerms.value = owned.data
    const all = await listPermissions({ page: 1, size: 5000 })
    const ownedIds = new Set(assignedPerms.value.map(p => p.permission_id))
    unassignedPerms.value = all.data.filter(p => !ownedIds.has(p.permission_id))
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '加载失败')
  } finally {
    loading.value = false
  }
}

const openAddPerm = () => { addPermIds.value = []; addDialog.value = true }
const confirmAdd = async () => {
  if (!roleId.value || !addPermIds.value.length) { ElMessage.warning('请选择角色与权限'); return }
  try {
    await assignRolePermissions({ role_id: roleId.value, permission_ids: addPermIds.value })
    ElMessage.success('已新增权限')
    addDialog.value = false
    await loadRolePerms()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '新增权限失败')
  }
}

onMounted(async () => {
  try {
    roles.value = await listRolesForPerm()
  } catch {}
})

const removePerm = async (row: PermissionItem) => {
  if (!roleId.value) return
  try {
    await revokeRolePermissions({ role_id: roleId.value, permission_ids: [row.permission_id] })
    ElMessage.success('已移除权限')
    await loadRolePerms()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '移除失败')
  }
}
</script>

<style scoped>
.assign-container { padding: 10px; }
</style>
