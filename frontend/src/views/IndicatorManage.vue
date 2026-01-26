<template>
  <div class="manage-container">
    <el-card shadow="never">
      <div style="display:flex; gap:8px; align-items:center; margin-bottom:10px;">
        <el-autocomplete
          v-model="q"
          :fetch-suggestions="handleSuggest"
          placeholder="搜索指标名称，支持提示补全"
          clearable
          style="width:320px"
          @select="handleSelectSuggest"
        />
        <el-select v-model="filterTypeId" placeholder="筛选考核类型" clearable filterable style="width:220px" @change="onFilterChange">
          <el-option v-for="t in types" :key="t.type_id" :label="t.type_name" :value="t.type_id" />
        </el-select>
        <el-button type="primary" @click="fetch">查询</el-button>
        <el-button type="success" @click="openCreate">新增指标</el-button>
        <el-popover placement="bottom" v-model:visible="batchVisible" :width="520" trigger="click">
          <div style="text-align:center;font-weight:600;color:#303133;margin-bottom:6px;">批量上传</div>
          <div style="display:flex; align-items:center; gap:8px; margin-bottom:8px;">
            <el-button type="primary" @click="downloadIndicatorsTemplate">下载模板</el-button>
            <input type="file" accept=".xls,.xlsx" @change="onIndicatorsFileChange" />
            <span class="file-name-ellipsis">{{ indicatorsFileName || '未选择任何文件' }}</span>
            <el-button type="success" :loading="indicatorsUploading" :disabled="!indicatorsFile" @click="uploadIndicatorsFile">批量上传</el-button>
          </div>
          <div class="file-canvas" ref="fileCanvas" aria-label="拖拽上传区域">
            <div
              v-for="(chip, idx) in bulkChips"
              :key="idx"
              class="file-chip"
              :style="{ left: chip.left + 'px', top: chip.top + 'px' }"
              tabindex="0"
              @mousedown="onChipMouseDown(idx, $event)"
            >
              {{ chip.name }}
              <button class="chip-close" aria-label="移除" @click="removeChip(idx)">×</button>
            </div>
          </div>
          <template #reference>
            <el-button type="success">批量上传</el-button>
          </template>
        </el-popover>
      </div>
      <el-table :data="rows" v-loading="loading" style="width:100%">
        <el-table-column prop="indicator_id" label="ID" width="100" />
        <!-- 名称列显示具体指标名 -->
        <el-table-column prop="indicator_name" label="名称" min-width="220" />
        <el-table-column prop="unit" label="单位" width="120" />
        <el-table-column prop="major_id" label="专业" width="140">
          <template #default="scope">
            <span>{{ (majors.find(m => m.major_id === scope.row.major_id) || {}).major_name || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="type_id" label="类型" width="140">
          <template #default="scope">
            <span>{{ (types.find(t => t.type_id === scope.row.type_id) || {}).type_name || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="is_positive" label="是否正向" width="100">
          <template #default="scope">
            <span>{{ scope.row.is_positive === 1 ? '正向' : scope.row.is_positive === 0 ? '负向' : '其他' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="80" />
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

    <el-dialog v-model="dialog" :title="editId ? '编辑指标' : '新增指标'" width="600px" destroy-on-close>
      <el-form :model="form" label-width="110px">
        <el-form-item label="名称" required><el-input v-model="form.indicator_name" /></el-form-item>
        <el-form-item label="单位"><el-input v-model="form.unit" /></el-form-item>
        <el-form-item label="专业" required>
          <el-select v-model="form.major_id" placeholder="选择专业" filterable style="width:100%">
            <el-option v-for="m in majors" :key="m.major_id" :label="m.major_name" :value="m.major_id" />
          </el-select>
        </el-form-item>
        <el-form-item label="类型" required>
          <el-select v-model="form.type_id" placeholder="选择类型" filterable style="width:100%">
            <el-option v-for="t in types" :key="t.type_id" :label="t.type_name" :value="t.type_id" />
          </el-select>
        </el-form-item>
        <el-form-item label="正向" required><el-select v-model="form.is_positive"><el-option :value="1" label="正向" /><el-option :value="0" label="负向" /><el-option :value="2" label="其他" /></el-select></el-form-item>
        <el-form-item label="状态" required>
          <el-select v-model="form.status" style="width:100%">
            <el-option :value="1" label="启用" />
            <el-option :value="0" label="停用" />
          </el-select>
        </el-form-item>
        <el-form-item label="版本"><el-input-number v-model="form.version" /></el-form-item>
        <el-form-item label="说明"><el-input v-model="form.description" type="textarea" /></el-form-item>
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
import { listIndicators, createIndicator, updateIndicator, deleteIndicatorById, getMajors, getEvaluationTypes, getIndicatorSuggestions, getIndicatorsUploadTemplate, uploadIndicators, type IndicatorFull, type PageResponse, type Major, type EvaluationType, type IndicatorSimple } from '@/api/indicator'
import { ElMessage } from 'element-plus'
import { Edit, Delete } from '@element-plus/icons-vue'
import { useUserStore } from '@/store/user'

const q = ref('')
const filterTypeId = ref<number | undefined>(undefined)
const indicatorsFile = ref<File | null>(null)
const indicatorsFileName = ref('')
const indicatorsUploading = ref(false)
const batchVisible = ref(false)
const bulkChips = ref<Array<{ name: string; left: number; top: number }>>([])
const fileCanvas = ref<HTMLElement | null>(null)
const rows = ref<IndicatorFull[]>([])
const userStore = useUserStore()
const total = ref(0)
const page = ref(1)
const size = ref(20)
const loading = ref(false)

const dialog = ref(false)
const form = ref<IndicatorFull>({ indicator_id: 0, indicator_name: '', is_positive: 1, status: 1, version: 1 })
const editId = ref<number | null>(null)
const majors = ref<Major[]>([])
const types = ref<EvaluationType[]>([])

const fetch = async () => {
  loading.value = true
  try {
    const res = await listIndicators({ q: q.value, type_id: filterTypeId.value, page: page.value, size: size.value })
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
  form.value = { indicator_id: 0, indicator_name: '', is_positive: 1, status: 1, version: 1 }
  dialog.value = true
}

const onFilterChange = () => {
  page.value = 1
  fetch()
}

let suggestTimer: any
const handleSuggest = (queryString: string, cb: (arg: any[]) => void) => {
  if (!queryString || queryString.length < 2) {
    cb([])
    return
  }
  if (suggestTimer) clearTimeout(suggestTimer)
  suggestTimer = setTimeout(async () => {
    try {
      const res = await getIndicatorSuggestions({ q: queryString, type_id: filterTypeId.value, size: 10 })
      cb(res.map((it: IndicatorSimple) => ({ value: it.indicator_name, id: it.indicator_id })))
    } catch {
      cb([])
    }
  }, 300)
}

const handleSelectSuggest = (item: any) => {
  q.value = item.value
  page.value = 1
  fetch()
}

const onIndicatorsFileChange = (e: Event) => {
  const target = e.target as HTMLInputElement
  const file = target.files && target.files[0]
  if (file) {
    indicatorsFile.value = file
    indicatorsFileName.value = file.name
    bulkChips.value = [{ name: file.name, left: 8, top: 8 }]
  }
}

const downloadIndicatorsTemplate = async () => {
  try {
    const resp = await getIndicatorsUploadTemplate()
    const blob = (resp as any).data ?? resp
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'indicator_manage_template.xlsx'
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  } catch {
    ElMessage.error('下载模板失败')
  }
}

const uploadIndicatorsFile = async () => {
  if (!indicatorsFile.value) return
  indicatorsUploading.value = true
  try {
    await uploadIndicators(indicatorsFile.value)
    ElMessage.success('上传成功')
    indicatorsFile.value = null
    indicatorsFileName.value = ''
    fetch()
    batchVisible.value = false
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail?.message || '上传失败')
  } finally {
    indicatorsUploading.value = false
  }
}

const onChipMouseDown = (idx: number, e: MouseEvent) => {
  const canvas = fileCanvas.value
  if (!canvas) return
  const chips = canvas.querySelectorAll('.file-chip')
  const el = chips[idx] as HTMLElement
  const canvasRect = canvas.getBoundingClientRect()
  const chipRect = el.getBoundingClientRect()
  const startX = e.clientX - chipRect.left
  const startY = e.clientY - chipRect.top
  const onMove = (ev: MouseEvent) => {
    let x = ev.clientX - canvasRect.left - startX
    let y = ev.clientY - canvasRect.top - startY
    x = Math.max(0, Math.min(x, canvasRect.width - el.offsetWidth))
    y = Math.max(0, Math.min(y, canvasRect.height - el.offsetHeight))
    bulkChips.value[idx].left = x
    bulkChips.value[idx].top = y
  }
  const onUp = () => {
    document.removeEventListener('mousemove', onMove)
    document.removeEventListener('mouseup', onUp)
  }
  document.addEventListener('mousemove', onMove)
  document.addEventListener('mouseup', onUp)
}

const removeChip = (idx: number) => {
  bulkChips.value.splice(idx, 1)
  if (bulkChips.value.length === 0) {
    indicatorsFile.value = null
    indicatorsFileName.value = ''
  }
}

const openEdit = (row: IndicatorFull) => {
  editId.value = row.indicator_id
  form.value = { ...row }
  dialog.value = true
}

const submit = async () => {
  try {
    if (editId.value) {
      await updateIndicator(editId.value, form.value)
      ElMessage.success('已更新')
    } else {
      await createIndicator(form.value)
      ElMessage.success('已新增')
    }
    dialog.value = false
    fetch()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '保存失败')
  }
}

const handleDelete = async (row: IndicatorFull) => {
  try {
    await deleteIndicatorById(row.indicator_id)
    ElMessage.success('已删除')
    fetch()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '删除失败')
  }
}

onMounted(() => fetch())
onMounted(async () => {
  try {
    const [m, t] = await Promise.all([getMajors(), getEvaluationTypes()])
    majors.value = m
    types.value = t
  } catch {}
})
</script>

<style scoped>
.manage-container { padding: 10px; }
.el-button-group .el-button { margin-right: 4px; }
.file-canvas {
  position: relative;
  width: 100%;
  height: 160px;
  border: 1px dashed #d9d9d9;
  border-radius: 6px;
  background: #fafafa;
  margin-top: 8px;
  overflow: hidden;
}
.file-chip {
  position: absolute;
  max-width: 70%;
  padding: 6px 28px 6px 10px;
  border-radius: 16px;
  background: #e6f4ff;
  color: #1677ff;
  box-shadow: 0 1px 3px rgba(0,0,0,.08);
  cursor: move;
  user-select: none;
}
.file-chip:focus { outline: 2px solid #91caff; }
.chip-close {
  position: absolute; right: 6px; top: 4px;
  border: none; background: transparent; color: #666; cursor: pointer;
}
.file-name-ellipsis { color:#606266; max-width: 240px; display:inline-block; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
</style>
