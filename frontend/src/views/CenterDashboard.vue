<template>
  <div class="dashboard-container">
    <el-card class="filter-card" shadow="never" style="margin-bottom: 20px;">
      <el-form :inline="true" :model="filterForm" class="demo-form-inline">
        <el-form-item label="区县">
          <el-select v-model="filterForm.district_id" placeholder="选择区县" clearable @change="handleDistrictChange" style="width: 200px;">
            <el-option v-for="d in districts" :key="d.district_id" :label="d.district_name" :value="d.district_id" />
          </el-select>
        </el-form-item>
        <el-form-item label="支撑中心">
          <el-select v-model="filterForm.center_id" placeholder="选择支撑中心" clearable filterable @change="refresh(true)" style="width: 260px;">
            <el-option v-for="c in centers" :key="c.center_id" :label="c.center_name" :value="c.center_id" />
          </el-select>
        </el-form-item>
        <el-form-item label="专业">
          <el-select v-model="filterForm.major_id" placeholder="选择专业" clearable @change="refresh(true)" style="width: 200px;">
            <el-option v-for="m in majors" :key="m.major_id" :label="m.major_name" :value="m.major_id" />
          </el-select>
        </el-form-item>
        <el-form-item label="指标名称">
          <el-select
            v-model="filterForm.indicator_id"
            placeholder="搜索指标名称"
            clearable
            filterable
            remote
            :remote-method="handleIndicatorSearch"
            :loading="indicatorSearchLoading"
            @change="refresh(true)"
            style="width: 240px;"
          >
            <el-option v-for="i in indicatorSearchOptions" :key="i.indicator_id" :label="i.indicator_name" :value="i.indicator_id" />
          </el-select>
        </el-form-item>
        <el-form-item label="考核类型">
          <el-select v-model="filterForm.type_id" placeholder="网络支撑中心承包评估" style="width: 200px;" :disabled="true">
            <el-option v-for="t in types" :key="t.type_id" :label="t.type_name" :value="t.type_id" />
          </el-select>
        </el-form-item>
        <el-form-item label="日期范围">
          <el-date-picker
            v-model="filterForm.dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            value-format="YYYY-MM-DD"
            @change="refresh(true)"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="refresh(true)">查询</el-button>
          <el-button v-if="hasPerm('indicator_data:add')" type="success" @click="uploadDialogVisible = true">上传</el-button>
          <el-popover v-if="hasPerm('indicator_data:add')" placement="bottom" v-model:visible="batchVisible" :width="520" trigger="click">
            <div style="text-align:center;font-weight:600;color:#303133;margin-bottom:6px;">批量上传</div>
            <div style="display:flex; align-items:center; gap:8px; margin-bottom:8px;">
              <el-button type="primary" @click="handleDownloadTemplate">下载模板</el-button>
              <input type="file" accept=".xls,.xlsx" @change="handleBulkFileChange" />
              <span class="file-name-ellipsis">{{ bulkFileName || '未选择任何文件' }}</span>
              <el-button type="success" :loading="bulkUploading" :disabled="!bulkFile" @click="handleBulkUpload">批量上传</el-button>
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
          <el-button type="warning" @click="handleExport">导出明细</el-button>
          <el-button type="warning" plain @click="handleExportSummary">汇总导出</el-button>
          <el-button v-if="hasPerm('indicator_data:delete')" type="danger" :disabled="selectedIds.length === 0" @click="handleDeleteSelected">删除所选</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card class="box-card">
      <template #header>
        <div class="card-header">
          <span>支撑中心明细</span>
          <el-button type="primary" link @click="refresh">刷新</el-button>
        </div>
      </template>

      <el-table
        :data="items"
        v-loading="loading"
        stripe
        style="width: 100%"
        @selection-change="handleSelectionChange"
        highlight-current-row
      >
        <el-table-column v-if="hasPerm('indicator_data:delete')" type="selection" width="48" />
        <el-table-column prop="indicator_name" label="指标名称" min-width="180" />
        <el-table-column prop="district_name" label="区县" width="120" />
        <el-table-column prop="center_name" label="支撑中心" min-width="180" show-overflow-tooltip />
        <el-table-column prop="value" label="完成值" min-width="120">
          <template #default="scope">
            <span class="value-blue">{{ formatMetric(scope.row, 'value') }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="benchmark" label="基准值" width="120">
          <template #default="scope">
            <span>{{ formatMetric(scope.row, 'benchmark') }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="challenge" label="挑战值" width="120">
          <template #default="scope">
            <span>{{ formatMetric(scope.row, 'challenge') }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="score" label="得分" width="120">
          <template #default="scope">
            <span :style="scope.row.score < 0 ? 'color:#F56C6C;font-weight:bold' : ''">{{ formatNum(scope.row.score) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="stat_date" label="日期" width="150" />
        <el-table-column label="操作" width="200" align="center">
          <template #default="scope">
            <el-button-group class="op-group">
              <el-tooltip content="趋势" placement="top">
                <el-button circle size="small" type="primary" @click.stop="openTrend(scope.row)">
                  <el-icon><DataLine /></el-icon>
                </el-button>
              </el-tooltip>
              <el-tooltip content="支撑中心对比" placement="top">
                <el-button circle size="small" type="primary" @click.stop="openCompare(scope.row)">
                  <el-icon><Histogram /></el-icon>
                </el-button>
              </el-tooltip>
              <el-tooltip v-if="hasPerm('indicator_data:edit')" content="编辑" placement="top">
                <el-button circle size="small" @click.stop="openEditSingle(scope.row)">
                  <el-icon><Edit /></el-icon>
                </el-button>
              </el-tooltip>
              <el-tooltip v-if="hasPerm('indicator_data:delete')" content="删除" placement="top">
                <el-button circle size="small" type="danger" @click.stop="handleDeleteSingle(scope.row)">
                  <el-icon><Delete /></el-icon>
                </el-button>
              </el-tooltip>
            </el-button-group>
          </template>
        </el-table-column>
      </el-table>

      <div style="margin-top: 20px; display: flex; justify-content: flex-end;">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          :total="total"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>

    <el-dialog v-model="uploadDialogVisible" title="上传支撑中心指标" width="720px">
      <el-form :model="uploadForm" label-width="100px">
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="考核类型">
              <el-select v-model="uploadForm.type_id" placeholder="网络支撑中心承包评估" style="width: 100%;" :disabled="true">
                <el-option v-for="t in types" :key="t.type_id" :label="t.type_name" :value="t.type_id" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="指标">
              <el-select v-model="uploadForm.indicator_id" placeholder="选择指标" clearable filterable style="width: 100%;">
                <el-option v-for="i in uploadIndicatorsList" :key="i.indicator_id" :label="i.indicator_name" :value="i.indicator_id" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="区县">
              <el-select v-model="uploadForm.district_id" placeholder="选择区县" clearable style="width: 100%;" @change="handleUploadDistrictChange">
                <el-option v-for="d in districts" :key="d.district_id" :label="d.district_name" :value="d.district_id" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="支撑中心">
              <el-select v-model="uploadForm.center_id" placeholder="选择支撑中心" clearable filterable style="width: 100%;">
                <el-option v-for="c in uploadCenters" :key="c.center_id" :label="c.center_name" :value="c.center_id" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="统计日期">
              <el-date-picker v-model="uploadForm.stat_date" type="date" value-format="YYYY-MM-DD" style="width: 100%;" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="完成值">
              <el-input-number v-model="uploadForm.value" :precision="4" style="width: 100%;" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="基准值">
              <el-input-number v-model="uploadForm.benchmark" :precision="4" style="width: 100%;" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="挑战值">
              <el-input-number v-model="uploadForm.challenge" :precision="4" style="width: 100%;" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="得分">
              <el-input-number v-model="uploadForm.score" :precision="4" style="width: 100%;" />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
      <template #footer>
        <el-button @click="uploadDialogVisible = false">取消</el-button>
        <el-button v-if="hasPerm('indicator_data:add')" type="primary" @click="handleManualUpload">提交</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="editDialogVisible" title="编辑支撑中心指标" width="560px">
      <el-form :model="editForm" label-width="100px">
        <el-form-item label="指标">{{ editForm.indicator_name }}</el-form-item>
        <el-form-item label="支撑中心">{{ editForm.center_name }}</el-form-item>
        <el-form-item label="日期">{{ editForm.stat_date }}</el-form-item>
        <el-form-item label="完成值">
          <el-input-number v-model="editForm.value" :precision="4" style="width: 100%;" />
        </el-form-item>
        <el-form-item label="基准值">
          <el-input-number v-model="editForm.benchmark" :precision="4" style="width: 100%;" />
        </el-form-item>
        <el-form-item label="挑战值">
          <el-input-number v-model="editForm.challenge" :precision="4" style="width: 100%;" />
        </el-form-item>
        <el-form-item label="得分">
          <el-input-number v-model="editForm.score" :precision="4" style="width: 100%;" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="editSaving" @click="submitEditSingle">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="trendDialogVisible" title="趋势" width="900px">
      <CenterIndicatorChart
        v-if="trendDialogVisible"
        :indicator-id="trendIndicatorId"
        :center-id="trendCenterId"
        :title="trendTitle"
        :start-date="filterForm.dateRange?.[0]"
        :end-date="filterForm.dateRange?.[1]"
      />
    </el-dialog>

    <el-dialog v-model="compareDialogVisible" title="支撑中心对比" width="900px">
      <div ref="compareChartRef" style="width: 100%; height: 420px;"></div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import * as echarts from 'echarts'
import { ElMessage, ElMessageBox } from 'element-plus'
import { UploadFilled, DataLine, Histogram, Edit, Delete } from '@element-plus/icons-vue'
import { useUserStore } from '@/store/user'
import CenterIndicatorChart from '@/components/CenterIndicatorChart.vue'
import {
  getDistricts,
  getCenters,
  getMajors,
  getEvaluationTypes,
  getIndicatorsList,
  getIndicatorsByType,
  getIndicatorSuggestions,
  getCenterData,
  createCenterData,
  updateCenterData,
  deleteCenterData,
  uploadCenterData,
  getCenterUploadTemplate,
  exportCenterMetrics,
  exportCenterMetricsSummary,
  getCenterLatestById,
  type District,
  type Center,
  type Major,
  type EvaluationType,
  type IndicatorSimple,
  type CenterDataItem
} from '@/api/indicator'

const districts = ref<District[]>([])
const centers = ref<Center[]>([])
const uploadCenters = ref<Center[]>([])
const majors = ref<Major[]>([])
const types = ref<EvaluationType[]>([])
const uploadIndicatorsList = ref<IndicatorSimple[]>([])

const indicatorSearchLoading = ref(false)
const indicatorSearchOptions = ref<IndicatorSimple[]>([])

const items = ref<CenterDataItem[]>([])
const total = ref(0)
const loading = ref(false)

const currentPage = ref(1)
const pageSize = ref(20)

const userStore = useUserStore()
const hasPerm = (code: string) => (userStore.permissions || []).includes(code)

const uploadDialogVisible = ref(false)
const editDialogVisible = ref(false)
const editSaving = ref(false)
const selectedIds = ref<number[]>([])

const bulkFile = ref<File | null>(null)
const bulkFileName = ref('')
const bulkUploading = ref(false)
const bulkChips = ref<Array<{ name: string; left: number; top: number }>>([])
const fileCanvas = ref<HTMLElement | null>(null)
const batchVisible = ref(false)
const draggingIdx = ref<number | null>(null)
const dragOffset = ref({ x: 0, y: 0 })

const compareDialogVisible = ref(false)
const compareChartRef = ref<HTMLElement | null>(null)
let compareChart: echarts.ECharts | null = null

const trendDialogVisible = ref(false)
const trendIndicatorId = ref(0)
const trendCenterId = ref<number | undefined>(undefined)
const trendTitle = computed(() => (trendIndicatorId.value ? '趋势' : ''))

const filterForm = ref<{
  district_id?: number
  center_id?: number
  major_id?: number
  indicator_id?: number
  type_id?: number
  dateRange?: [string, string]
}>({
  district_id: undefined,
  center_id: undefined,
  major_id: undefined,
  indicator_id: undefined,
  type_id: undefined,
  dateRange: undefined,
})

const uploadForm = ref<{
  indicator_id?: number
  type_id?: number
  district_id?: number
  center_id?: number
  stat_date?: string
  value?: number
  benchmark?: number
  challenge?: number
  score?: number
}>({
  indicator_id: undefined,
  type_id: undefined,
  district_id: undefined,
  center_id: undefined,
  stat_date: undefined,
  value: undefined,
  benchmark: undefined,
  challenge: undefined,
  score: undefined,
})

const editForm = ref<any>({
  indicator_id: undefined,
  indicator_name: '',
  center_id: undefined,
  center_name: '',
  stat_date: '',
  value: undefined,
  benchmark: undefined,
  challenge: undefined,
  score: undefined,
})

const formatNum = (v: any) => {
  if (v === null || v === undefined || Number.isNaN(Number(v))) return ''
  const n = Number(v)
  if (Number.isInteger(n)) return String(n)
  return n.toFixed(4).replace(/0+$/, '').replace(/\.$/, '')
}

const isPercentIndicator = (name: string | undefined) => !!name && /率|占比/.test(name)
const formatMetric = (row: any, key: 'value' | 'benchmark' | 'challenge') => {
  const v = row?.[key]
  if (v === null || v === undefined || Number.isNaN(Number(v))) return ''
  const n = Number(v)
  if (isPercentIndicator(row?.indicator_name)) {
    const pct = Math.abs(n) <= 1 ? n * 100 : n
    return `${pct.toFixed(2).replace(/0+$/, '').replace(/\.$/, '')}%`
  }
  if (Number.isInteger(n)) return String(n)
  return n.toFixed(4).replace(/0+$/, '').replace(/\.$/, '')
}

const loadOptions = async () => {
  try {
    const [d, m, t] = await Promise.all([getDistricts(), getMajors(), getEvaluationTypes()])
    districts.value = d
    majors.value = m
    const fixed = (t || []).find(x => String(x.type_name).toLowerCase() === '网络支撑中心承包评估'.toLowerCase())
    types.value = fixed ? [fixed] : []
    if (fixed) {
      filterForm.value.type_id = fixed.type_id
      uploadForm.value.type_id = fixed.type_id
      try {
        uploadIndicatorsList.value = await getIndicatorsByType(fixed.type_id)
      } catch {
        uploadIndicatorsList.value = []
      }
    } else {
      uploadIndicatorsList.value = []
    }
  } catch {
    ElMessage.error('加载筛选项失败')
  }
}

const loadCenters = async () => {
  try {
    centers.value = await getCenters({ district_id: filterForm.value.district_id })
  } catch {
    centers.value = []
  }
}

const handleDistrictChange = async () => {
  filterForm.value.center_id = undefined
  await loadCenters()
  refresh(true)
}

const handleUploadDistrictChange = async () => {
  uploadForm.value.center_id = undefined
  try {
    uploadCenters.value = await getCenters({ district_id: uploadForm.value.district_id })
  } catch {
    uploadCenters.value = []
  }
}

const handleUploadTypeChange = async (val: number | undefined) => {
  uploadForm.value.indicator_id = undefined
  if (!val) {
    uploadIndicatorsList.value = []
    return
  }
  try {
    uploadIndicatorsList.value = await getIndicatorsByType(val)
  } catch {
    uploadIndicatorsList.value = []
  }
}

const handleIndicatorSearch = async (q: string) => {
  if (!q || q.length < 2) {
    indicatorSearchOptions.value = []
    return
  }
  indicatorSearchLoading.value = true
  try {
    indicatorSearchOptions.value = await getIndicatorSuggestions({ q, type_id: filterForm.value.type_id, size: 20 })
  } catch {
    indicatorSearchOptions.value = []
  } finally {
    indicatorSearchLoading.value = false
  }
}

const fetch = async () => {
  loading.value = true
  try {
    const start_date = filterForm.value.dateRange?.[0]
    const end_date = filterForm.value.dateRange?.[1]
    const res = await getCenterData({
      indicator_id: filterForm.value.indicator_id,
      center_id: filterForm.value.center_id,
      district_id: filterForm.value.district_id,
      major_id: filterForm.value.major_id,
      type_id: filterForm.value.type_id,
      start_date,
      end_date,
      page: currentPage.value,
      size: pageSize.value,
      order_by: 'stat_date',
      desc: true,
    })
    items.value = res.items
    total.value = res.total
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail?.message || e?.response?.data?.detail || '加载失败')
  } finally {
    loading.value = false
  }
}

const refresh = (reset = false) => {
  if (reset) currentPage.value = 1
  fetch()
}

const handleSelectionChange = (rows: any[]) => {
  selectedIds.value = rows.map(r => r.id)
}

const handleSizeChange = (v: number) => {
  pageSize.value = v
  currentPage.value = 1
  fetch()
}

const handleCurrentChange = (p: number) => {
  currentPage.value = p
  fetch()
}

const handleManualUpload = async () => {
  if (!uploadForm.value.indicator_id || !uploadForm.value.center_id || !uploadForm.value.stat_date || uploadForm.value.value === undefined) {
    ElMessage.warning('请填写必填项（指标、支撑中心、日期、完成值）')
    return
  }
  try {
    await createCenterData({
      indicator_id: uploadForm.value.indicator_id,
      center_id: uploadForm.value.center_id,
      stat_date: uploadForm.value.stat_date,
      value: uploadForm.value.value,
      type_id: uploadForm.value.type_id,
      benchmark: uploadForm.value.benchmark,
      challenge: uploadForm.value.challenge,
      score: uploadForm.value.score,
    })
    ElMessage.success('提交成功')
    uploadDialogVisible.value = false
    refresh(true)
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail?.message || e?.response?.data?.detail || '提交失败')
  }
}

const handleBulkFileChange = (e: Event) => {
  const target = e.target as HTMLInputElement
  const f = target.files?.[0] || null
  bulkFile.value = f
  bulkFileName.value = f?.name || ''
  bulkChips.value = f ? [{ name: f.name, left: 18, top: 18 }] : []
}

const removeChip = (idx: number) => {
  bulkChips.value.splice(idx, 1)
  bulkFile.value = null
  bulkFileName.value = ''
}

const onChipMouseDown = (idx: number, ev: MouseEvent) => {
  draggingIdx.value = idx
  const rect = (ev.currentTarget as HTMLElement).getBoundingClientRect()
  dragOffset.value = { x: ev.clientX - rect.left, y: ev.clientY - rect.top }
  window.addEventListener('mousemove', onChipMouseMove)
  window.addEventListener('mouseup', onChipMouseUp)
}

const onChipMouseMove = (ev: MouseEvent) => {
  if (draggingIdx.value === null) return
  const canvas = fileCanvas.value
  if (!canvas) return
  const crect = canvas.getBoundingClientRect()
  const left = ev.clientX - crect.left - dragOffset.value.x
  const top = ev.clientY - crect.top - dragOffset.value.y
  const chip = bulkChips.value[draggingIdx.value]
  chip.left = Math.max(0, Math.min(left, crect.width - 120))
  chip.top = Math.max(0, Math.min(top, crect.height - 28))
}

const onChipMouseUp = () => {
  draggingIdx.value = null
  window.removeEventListener('mousemove', onChipMouseMove)
  window.removeEventListener('mouseup', onChipMouseUp)
}

const downloadBlob = (blob: Blob, filename: string) => {
  const url = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  link.remove()
  window.URL.revokeObjectURL(url)
}

const handleDownloadTemplate = async () => {
  try {
    const resp: any = await getCenterUploadTemplate()
    const blob = resp instanceof Blob ? resp : resp?.data
    downloadBlob(blob, 'center_indicator_import_template.xlsx')
  } catch {
    ElMessage.error('下载模板失败')
  }
}

const handleBulkUpload = async () => {
  if (!bulkFile.value) return
  bulkUploading.value = true
  try {
    await uploadCenterData(bulkFile.value)
    ElMessage.success('批量上传成功')
    batchVisible.value = false
    bulkFile.value = null
    bulkFileName.value = ''
    bulkChips.value = []
    refresh(true)
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail?.message || e?.response?.data?.detail || '批量上传失败')
  } finally {
    bulkUploading.value = false
  }
}

const handleExport = async () => {
  try {
    const start_date = filterForm.value.dateRange?.[0]
    const end_date = filterForm.value.dateRange?.[1]
    const blobResp: any = await exportCenterMetrics({
      indicator_id: filterForm.value.indicator_id,
      center_id: filterForm.value.center_id,
      district_id: filterForm.value.district_id,
      major_id: filterForm.value.major_id,
      type_id: filterForm.value.type_id,
      start_date,
      end_date,
      page: 1,
      size: 2000,
      order_by: 'stat_date',
      desc: true,
    })
    const blob = blobResp instanceof Blob ? blobResp : blobResp?.data
    downloadBlob(blob, 'center_metrics_export.xlsx')
  } catch {
    ElMessage.error('导出失败')
  }
}

const handleExportSummary = async () => {
  try {
    const start_date = filterForm.value.dateRange?.[0]
    const end_date = filterForm.value.dateRange?.[1]
    const blobResp: any = await exportCenterMetricsSummary({
      indicator_id: filterForm.value.indicator_id,
      center_id: filterForm.value.center_id,
      district_id: filterForm.value.district_id,
      major_id: filterForm.value.major_id,
      type_id: filterForm.value.type_id,
      start_date,
      end_date,
      page: 1,
      size: 2000,
      order_by: 'stat_date',
      desc: true,
    })
    const blob = blobResp instanceof Blob ? blobResp : blobResp?.data
    downloadBlob(blob, 'center_metrics_export_summary.xlsx')
  } catch {
    ElMessage.error('汇总导出失败')
  }
}

const handleDeleteSelected = async () => {
  if (!selectedIds.value.length) return
  try {
    await ElMessageBox.confirm(`确认删除所选 ${selectedIds.value.length} 条数据？`, '提示', { type: 'warning' })
    await deleteCenterData({ ids: selectedIds.value })
    ElMessage.success('删除成功')
    selectedIds.value = []
    refresh(true)
  } catch {}
}

const handleDeleteSingle = async (row: any) => {
  try {
    await ElMessageBox.confirm('确认删除该条数据？', '提示', { type: 'warning' })
    await deleteCenterData({ ids: [row.id] })
    ElMessage.success('删除成功')
    refresh()
  } catch {}
}

const openEditSingle = (row: any) => {
  editForm.value = {
    id: row.id,
    indicator_id: row.indicator_id,
    indicator_name: row.indicator_name,
    center_id: row.center_id,
    center_name: row.center_name,
    stat_date: row.stat_date,
    value: row.value,
    benchmark: row.benchmark,
    challenge: row.challenge,
    score: row.score,
  }
  editDialogVisible.value = true
}

const submitEditSingle = async () => {
  editSaving.value = true
  try {
    await updateCenterData({
      indicator_id: editForm.value.indicator_id,
      center_id: editForm.value.center_id,
      stat_date: editForm.value.stat_date,
      value: editForm.value.value,
      benchmark: editForm.value.benchmark,
      challenge: editForm.value.challenge,
      score: editForm.value.score,
    })
    ElMessage.success('保存成功')
    editDialogVisible.value = false
    refresh()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail?.message || e?.response?.data?.detail || '保存失败')
  } finally {
    editSaving.value = false
  }
}

const openTrend = (row: any) => {
  trendIndicatorId.value = row.indicator_id
  trendCenterId.value = row.center_id
  trendDialogVisible.value = true
}

const openCompare = async (row: any) => {
  compareDialogVisible.value = true
  await new Promise(r => setTimeout(r, 50))
  if (!compareChartRef.value) return
  if (!compareChart) compareChart = echarts.init(compareChartRef.value)
  try {
    const list = await getCenterLatestById({
      indicator_id: row.indicator_id,
      stat_date: row.stat_date,
      district_id: filterForm.value.district_id,
    })
    const sorted = (list || []).slice().sort((a: any, b: any) => (b.value ?? -Infinity) - (a.value ?? -Infinity))
    const names = sorted.map((i: any) => i.center_name)
    const values = sorted.map((i: any) => i.value ?? null)
    compareChart.setOption(
      {
        title: { text: `${row.indicator_name} 支撑中心对比`, left: 10, top: 10 },
        tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
        grid: { left: 12, right: 12, top: 48, bottom: 24, containLabel: true },
        xAxis: { type: 'value' },
        yAxis: { type: 'category', data: names, inverse: true, axisLabel: { width: 140, overflow: 'truncate' } },
        series: [{ type: 'bar', data: values }],
      },
      true
    )
  } catch {
    ElMessage.error('加载对比数据失败')
  }
}

onMounted(async () => {
  await loadOptions()
  await loadCenters()
  fetch()
})
</script>

<style scoped>
.dashboard-container {
  padding: 10px;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.el-button-group .el-button { margin-right: 4px; }
.value-text {
  font-weight: bold;
  color: #409EFF;
}
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
  max-width: 60%;
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
