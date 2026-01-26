<template>
  <div class="manage-container">
    <el-card shadow="never">
      <div style="display:flex; gap:8px; align-items:center; margin-bottom:10px;">
        <el-input v-model="q" placeholder="搜索考核类型名称" clearable style="width:280px" @keyup.enter="fetch" />
        <el-button type="primary" @click="fetch">查询</el-button>
        <el-button type="success" @click="openCreate">新增类型</el-button>
      </div>
      <el-table :data="rows" v-loading="loading" style="width:100%">
        <el-table-column prop="type_id" label="ID" width="90" />
        <el-table-column prop="type_name" label="类型名称" min-width="220" />
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

    <el-dialog v-model="dialog" :title="editId ? '编辑类型' : '新增类型'" width="500px" destroy-on-close>
      <el-form :model="form" label-width="110px">
        <el-form-item label="类型名称" required><el-input v-model="form.type_name" /></el-form-item>
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
import { listEvaluationTypes, createEvaluationType, updateEvaluationType, deleteEvaluationType, type EvaluationTypeItem } from '@/api/evaluation_type'
import { ElMessage } from 'element-plus'
import { Edit, Delete } from '@element-plus/icons-vue'

const q = ref('')
const rows = ref<EvaluationTypeItem[]>([])
const total = ref(0)
const page = ref(1)
const size = ref(20)
const loading = ref(false)
const dialog = ref(false)
const editId = ref<number | null>(null)
const form = ref<EvaluationTypeItem>({ type_id: 0, type_name: '' })

const fetch = async () => {
  loading.value = true
  try {
    const res = await listEvaluationTypes({ q: q.value, page: page.value, size: size.value })
    rows.value = res.data
    total.value = res.total
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '加载失败')
  } finally {
    loading.value = false
  }
}

const openCreate = () => { editId.value = null; form.value = { type_id: 0, type_name: '' }; dialog.value = true }
const openEdit = (row: EvaluationTypeItem) => { editId.value = row.type_id; form.value = { ...row }; dialog.value = true }

const submit = async () => {
  try {
    if (editId.value) {
      await updateEvaluationType(editId.value, { type_name: form.value.type_name })
      ElMessage.success('已更新')
    } else {
      await createEvaluationType({ type_name: form.value.type_name })
      ElMessage.success('已新增')
    }
    dialog.value = false
    fetch()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '保存失败')
  }
}

const handleDelete = async (row: EvaluationTypeItem) => {
  try {
    await deleteEvaluationType(row.type_id)
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
