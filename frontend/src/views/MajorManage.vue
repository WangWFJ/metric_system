<template>
  <div class="manage-container">
    <el-card shadow="never">
      <div style="display:flex; gap:8px; align-items:center; margin-bottom:10px;">
        <el-input v-model="q" placeholder="搜索专业名称/编码" clearable style="width:280px" @keyup.enter="fetch" />
        <el-button type="primary" @click="fetch">查询</el-button>
        <el-button type="success" @click="openCreate">新增专业</el-button>
      </div>
      <el-table :data="rows" v-loading="loading" style="width:100%">
        <el-table-column prop="major_id" label="ID" width="100" />
        <el-table-column prop="major_name" label="名称" min-width="220" />
        <el-table-column prop="major_code" label="编码" width="160" />
        <el-table-column label="操作" width="160" align="center">
          <template #default="scope">
            <el-button-group>
              <el-tooltip content="编辑" placement="top">
                <el-button circle size="small" @click.stop="openEdit(scope.row)">
                  <el-icon><Edit /></el-icon>
                </el-button>
              </el-tooltip>
              <el-tooltip content="删除" placement="top">
                <el-button circle size="small" type="danger" @click.stop="handleDelete(scope.row)">
                  <el-icon><Delete /></el-icon>
                </el-button>
              </el-tooltip>
            </el-button-group>
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

    <el-dialog v-model="dialog" :title="editId ? '编辑专业' : '新增专业'" width="600px" destroy-on-close>
      <el-form :model="form" label-width="110px">
        <el-form-item label="名称" required><el-input v-model="form.major_name" /></el-form-item>
        <el-form-item label="编码" required><el-input v-model="form.major_code" /></el-form-item>
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
import { listMajors, createMajor, updateMajor, deleteMajorById, type Major, type PageResponse } from '@/api/indicator'
import { ElMessage } from 'element-plus'
import { Edit, Delete } from '@element-plus/icons-vue'

const q = ref('')
const rows = ref<Major[]>([])
const total = ref(0)
const page = ref(1)
const size = ref(20)
const loading = ref(false)

const dialog = ref(false)
const form = ref<Major>({ major_id: 0, major_name: '', major_code: '' })
const editId = ref<number | null>(null)

const fetch = async () => {
  loading.value = true
  try {
    const res = await listMajors({ q: q.value, page: page.value, size: size.value })
    rows.value = res.data
    total.value = res.total
  } catch (e) {
    ElMessage.error('加载失败')
  } finally {
    loading.value = false
  }
}

const openCreate = () => {
  editId.value = null
  form.value = { major_id: 0, major_name: '', major_code: '' }
  dialog.value = true
}

const openEdit = (row: Major) => {
  editId.value = row.major_id
  form.value = { ...row }
  dialog.value = true
}

const submit = async () => {
  try {
    if (editId.value) {
      await updateMajor(editId.value, form.value)
      ElMessage.success('已更新')
    } else {
      await createMajor(form.value)
      ElMessage.success('已新增')
    }
    dialog.value = false
    fetch()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '保存失败')
  }
}

const handleDelete = async (row: Major) => {
  try {
    await deleteMajorById(row.major_id)
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
.el-button-group .el-button { margin-right: 4px; }
</style>
