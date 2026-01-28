<template>
  <div class="dashboard-container">
    <el-card class="filter-card" shadow="never" style="margin-bottom: 20px;">
      <el-form :inline="true" :model="filterForm" class="demo-form-inline">
        <el-form-item label="区县">
          <el-select v-model="filterForm.district_id" placeholder="选择区县" clearable @change="refresh" style="width: 200px;">
            <el-option
              v-for="item in districts"
              :key="item.district_id"
              :label="item.district_name"
              :value="item.district_id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="圈层">
          <el-select v-model="filterForm.circle_id" placeholder="选择圈层" clearable @change="refresh" style="width: 160px;">
            <el-option v-for="c in circles" :key="c" :label="String(c)" :value="c" />
          </el-select>
        </el-form-item>
        <el-form-item label="专业">
          <el-select v-model="filterForm.major_id" placeholder="选择专业" clearable @change="refresh" style="width: 200px;">
            <el-option
              v-for="item in majors"
              :key="item.major_id"
              :label="item.major_name"
              :value="item.major_id"
            />
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
            <el-option
              v-for="item in indicatorSearchOptions"
              :key="item.indicator_id"
              :label="item.indicator_name"
              :value="item.indicator_id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="考核类型">
          <el-select v-model="filterForm.type_id" placeholder="选择类型" clearable @change="refresh" style="width: 200px;">
            <el-option
              v-for="item in types"
              :key="item.type_id"
              :label="item.type_name"
              :value="item.type_id"
            />
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
            @change="refresh"
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

    <el-row :gutter="20">
      <el-col :span="24">
        <el-card class="box-card">
          <template #header>
            <div class="card-header">
              <span>最新指标</span>
              <el-button type="primary" link @click="refresh">刷新</el-button>
            </div>
          </template>
          <el-table 
            :data="indicatorStore.indicators" 
            v-loading="indicatorStore.loading" 
            stripe 
            style="width: 100%"
            @selection-change="handleSelectionChange"
            highlight-current-row
          >
            <el-table-column v-if="hasPerm('indicator_data:delete')" type="selection" width="48" />
            <el-table-column prop="indicator_name" label="指标名称" min-width="180" />
            <el-table-column prop="district_name" label="区县" width="120" />
            <el-table-column prop="value" label="完成值" min-width="120">
              <template #default="scope">
                <span :class="getValueClass(scope.row)">{{ formatMetric(scope.row, 'value') }}</span>
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
            <el-table-column prop="exemption" label="豁免值" width="120">
              <template #default="scope">
                <span>{{ formatMetric(scope.row, 'exemption') }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="zero_tolerance" label="零容忍值" width="120">
              <template #default="scope">
                <span>{{ formatMetric(scope.row, 'zero_tolerance') }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="score" label="得分" width="120">
              <template #default="scope">
                <span :style="scope.row.score < 0 ? 'color:#F56C6C;font-weight:bold' : ''">{{ scope.row.score }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="stat_date" label="日期" width="150">
              <template #default="scope">
                <span>
                  {{
                    new Date(scope.row.stat_date).getFullYear() + '年' +
                    String(new Date(scope.row.stat_date).getMonth() + 1).padStart(2, '0') + '月' +
                    String(new Date(scope.row.stat_date).getDate()).padStart(2, '0') + '日'
                  }}
                </span>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="200" align="center">
              <template #default="scope">
                <el-button-group>
                  <el-tooltip content="趋势" placement="top">
                    <el-button circle size="small" type="primary" @click.stop="handleRowClick(scope.row)">
                      <el-icon><DataLine /></el-icon>
                    </el-button>
                  </el-tooltip>
                  <el-tooltip content="区县对比" placement="top">
                    <el-button circle size="small" type="primary" @click.stop="handleCompare(scope.row)">
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
              :total="indicatorStore.total"
              @size-change="handleSizeChange"
              @current-change="handleCurrentChange"
            />
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-dialog v-model="dialogVisible" title="指标趋势" width="100%" destroy-on-close>
      <IndicatorChart 
        v-if="selectedIndicator" 
        :indicator-id="selectedIndicator.indicator_id" 
        :indicator-name="selectedIndicator.indicator_name"
        :district-id="selectedIndicator.district_id"
      />
    </el-dialog>

    <el-dialog v-model="compareDialogVisible" title="区县对比" width="70%" destroy-on-close>
      <div ref="compareChartRef" style="width:100%;height:460px"></div>
    </el-dialog>

    <el-dialog v-model="uploadDialogVisible" title="上传指标" width="500px">
      <el-form :model="uploadForm" label-width="100px">
        <el-form-item label="考核类型" required>
          <el-select v-model="uploadForm.type_id" placeholder="选择类型" filterable style="width: 100%" @change="handleTypeChange">
            <el-option
              v-for="item in types"
              :key="item.type_id"
              :label="item.type_name"
              :value="item.type_id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="指标名称" required>
          <el-select v-model="uploadForm.indicator_id" placeholder="选择指标" filterable style="width: 100%" :disabled="!uploadForm.type_id" @change="">
            <el-option
              v-for="item in indicatorsList"
              :key="item.indicator_id"
              :label="item.indicator_name"
              :value="item.indicator_id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="区县" required>
          <el-select v-model="uploadForm.district_id" placeholder="选择区县" filterable style="width: 100%">
            <el-option
              v-for="item in districts"
              :key="item.district_id"
              :label="item.district_name"
              :value="item.district_id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="日期" required>
          <el-date-picker
            v-model="uploadForm.stat_date"
            type="date"
            placeholder="选择日期"
            value-format="YYYY-MM-DD"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="数值" required>
          <el-input-number v-model="uploadForm.value" :precision="4" :step="0.1" style="width: 100%" />
        </el-form-item>
        <el-form-item label="基准值">
          <el-input-number v-model="uploadForm.benchmark" :precision="4" :step="0.1" style="width: 100%" />
        </el-form-item>
        <el-form-item label="挑战值">
          <el-input-number v-model="uploadForm.challenge" :precision="4" :step="0.1" style="width: 100%" />
        </el-form-item>
        <el-form-item label="豁免值">
          <el-input-number v-model="uploadForm.exemption" :precision="4" :step="0.1" style="width: 100%" />
        </el-form-item>
        <el-form-item label="零容忍值">
          <el-input-number v-model="uploadForm.zero_tolerance" :precision="4" :step="0.1" style="width: 100%" />
        </el-form-item>
        <el-form-item label="得分">
          <el-input-number v-model="uploadForm.score" :precision="4" :step="0.1" style="width: 100%" />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="uploadDialogVisible = false">取消</el-button>
          <el-button v-if="hasPerm('indicator_data:add')" type="primary" @click="handleManualUpload">提交</el-button>
        </span>
      </template>
    </el-dialog>

    <el-dialog v-model="editDialogVisible" title="编辑指标数据" width="500px" destroy-on-close>
      <el-form :model="editForm" label-width="100px">
        <el-form-item label="数值" required>
          <el-input-number v-model="editForm.value" :precision="4" :step="0.1" style="width: 100%" />
        </el-form-item>
        <el-form-item label="基准值"><el-input-number v-model="editForm.benchmark" :precision="4" :step="0.1" style="width: 100%" /></el-form-item>
        <el-form-item label="挑战值"><el-input-number v-model="editForm.challenge" :precision="4" :step="0.1" style="width: 100%" /></el-form-item>
        <el-form-item label="豁免值"><el-input-number v-model="editForm.exemption" :precision="4" :step="0.1" style="width: 100%" /></el-form-item>
        <el-form-item label="零容忍值"><el-input-number v-model="editForm.zero_tolerance" :precision="4" :step="0.1" style="width: 100%" /></el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="editDialogVisible=false">取消</el-button>
          <el-button type="primary" @click="submitEditSingle">保存</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick } from 'vue'
import { useIndicatorStore } from '@/store/indicator'
import { 
  getDistricts, 
  getMajors, 
  getEvaluationTypes, 
  getIndicatorsList,
  getIndicatorsByType,
  getIndicatorSuggestions,
  createIndicatorData,
  updateIndicatorData,
  uploadIndicatorData, 
  getUploadTemplate,
  deleteIndicatorData,
  exportMetrics,
  type IndicatorData, 
  type District, 
  type Major, 
  type EvaluationType,
  type IndicatorSimple,
  getCircles
} from '@/api/indicator'
import IndicatorChart from '@/components/IndicatorChart.vue'
import * as echarts from 'echarts'
import { getIndicatorLatestById } from '@/api/indicator'
import { ElMessage, type UploadRequestOptions } from 'element-plus'
import { useUserStore } from '@/store/user'
import { UploadFilled, DataLine, Histogram, Edit, Delete } from '@element-plus/icons-vue'
import { exportMetricsSummary } from '@/api/indicator'

const indicatorStore = useIndicatorStore()
const userStore = useUserStore()
const dialogVisible = ref(false)
const uploadDialogVisible = ref(false)
const selectedIndicator = ref<IndicatorData | null>(null)
const selectedIds = ref<number[]>([])
const districts = ref<District[]>([])
const circles = ref<number[]>([])
const majors = ref<Major[]>([])
const types = ref<EvaluationType[]>([])
const indicatorsList = ref<IndicatorSimple[]>([])

const filterForm = ref({
  district_id: undefined as number | undefined,
  circle_id: undefined as number | undefined,
  major_id: undefined as number | undefined,
  type_id: undefined as number | undefined,
  indicator_id: undefined as number | undefined,
  dateRange: [] as string[]
})

const uploadForm = ref({
  indicator_id: undefined as number | undefined,
  type_id: undefined as number | undefined,
  district_id: undefined as number | undefined,
  stat_date: '',
  value: undefined as number | undefined,
  benchmark: undefined as number | undefined,
  challenge: undefined as number | undefined,
  exemption: undefined as number | undefined,
  zero_tolerance: undefined as number | undefined,
  score: undefined as number | undefined
})

const bulkFile = ref<File | null>(null)
const bulkFileName = ref('')
const bulkUploading = ref(false)
const bulkChips = ref<Array<{ name: string; left: number; top: number }>>([])
const fileCanvas = ref<HTMLElement | null>(null)
const batchVisible = ref(false)

const currentPage = ref(1)
const pageSize = ref(20)

const fetchOptions = async () => {
  try {
    const [distRes, majorRes, typeRes, indRes, circleRes] = await Promise.all([
      getDistricts(),
      getMajors(),
      getEvaluationTypes(),
      getIndicatorsList(),
      getCircles()
    ])
    districts.value = distRes
    majors.value = majorRes
    const allowNameList = ['区县kpi考核', '区县KPI考核', '省对区县评优']
    const allowedIds = new Set(
      (typeRes || [])
        .filter(t => allowNameList.includes(String(t.type_name)))
        .map(t => t.type_id)
    )
    types.value = (typeRes || []).filter(t => allowedIds.has(t.type_id))
    indicatorsList.value = indRes
    circles.value = circleRes
  } catch (error) {
    console.error('Failed to fetch options', error)
    ElMessage.error('获取选项失败')
  }
}

const handleTypeChange = async (val: number | undefined) => {
  uploadForm.value.indicator_id = undefined
  if (!val) {
    indicatorsList.value = []
    return
  }
  try {
    const res = await getIndicatorsByType(val)
    indicatorsList.value = res
  } catch (error) {
    console.error('Failed to fetch indicators by type', error)
    ElMessage.error('获取指标失败')
  }
}

const refresh = (isQuery = false) => {
  if (isQuery) {
    currentPage.value = 1
  }
  const params: any = { 
    size: pageSize.value, 
    page: currentPage.value,
    desc: true, 
    order_by: 'stat_date',
    district_id: filterForm.value.district_id,
    circle_id: filterForm.value.circle_id,
    major_id: filterForm.value.major_id,
    type_id: filterForm.value.type_id,
    indicator_id: filterForm.value.indicator_id
  }
  
  if (filterForm.value.dateRange && filterForm.value.dateRange.length === 2) {
    params.start_date = filterForm.value.dateRange[0]
    params.end_date = filterForm.value.dateRange[1]
  }

  indicatorStore.fetchIndicators(params)
}

const indicatorSearchOptions = ref<IndicatorSimple[]>([])
const indicatorSearchLoading = ref(false)
let indicatorSearchTimer: any
const handleIndicatorSearch = (query: string) => {
  if (!query || query.length < 2) {
    indicatorSearchOptions.value = []
    return
  }
  if (indicatorSearchTimer) clearTimeout(indicatorSearchTimer)
  indicatorSearchTimer = setTimeout(async () => {
    indicatorSearchLoading.value = true
    try {
      const res = await getIndicatorSuggestions({ q: query, type_id: filterForm.value.type_id, size: 20 })
      indicatorSearchOptions.value = res
    } catch (e) {
      indicatorSearchOptions.value = []
    } finally {
      indicatorSearchLoading.value = false
    }
  }, 300)
}
const handleSizeChange = (val: number) => {
  pageSize.value = val
  refresh()
}

const handleCurrentChange = (val: number) => {
  currentPage.value = val
  refresh()
}

const handleManualUpload = async () => {
  if (!uploadForm.value.indicator_id || !uploadForm.value.district_id || !uploadForm.value.stat_date || uploadForm.value.value === undefined) {
    ElMessage.warning('请填写所有必填字段')
    return
  }
  if (!uploadForm.value.type_id) {
    ElMessage.warning('请选择考核类型')
    return
  }

  try {
    await createIndicatorData({
      indicator_id: uploadForm.value.indicator_id,
      type_id: uploadForm.value.type_id,
      district_id: uploadForm.value.district_id,
      stat_date: uploadForm.value.stat_date,
      value: uploadForm.value.value,
      benchmark: uploadForm.value.benchmark,
      challenge: uploadForm.value.challenge,
      exemption: uploadForm.value.exemption,
      zero_tolerance: uploadForm.value.zero_tolerance,
      score: uploadForm.value.score
    })
    ElMessage.success('上传成功')
    uploadDialogVisible.value = false
    refresh()
    // Reset form
    uploadForm.value = {
      indicator_id: undefined,
      type_id: undefined,
      district_id: undefined,
      stat_date: '',
      value: undefined,
      benchmark: undefined,
      challenge: undefined,
      exemption: undefined,
      zero_tolerance: undefined,
      score: undefined
    }
  } catch (error: any) {
    console.error('Upload failed', error)
    ElMessage.error(error.response?.data?.detail?.message || '上传失败')
  }
}

const handleBulkFileChange = (e: Event) => {
  const target = e.target as HTMLInputElement
  const file = target.files && target.files[0]
  if (file) {
    bulkFile.value = file
    bulkFileName.value = file.name
    // 添加拖拽小卡片，默认位置 8,8
    bulkChips.value = [{ name: file.name, left: 8, top: 8 }]
  }
}

const handleBulkUpload = async () => {
  if (!bulkFile.value) return
  bulkUploading.value = true
  try {
    await uploadIndicatorData(bulkFile.value)
    ElMessage.success('批量上传成功')
    bulkFile.value = null
    bulkFileName.value = ''
    bulkChips.value = []
    refresh()
  } catch (error: any) {
    ElMessage.error(error?.response?.data?.detail?.message || '批量上传失败')
  } finally {
    bulkUploading.value = false
  }
}

const handleDownloadTemplate = async () => {
  try {
    const blobOrResp = await getUploadTemplate()
    const blob = (blobOrResp as any).data ?? blobOrResp
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'indicator_import_template.xlsx'
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  } catch (e) {
    ElMessage.error('下载模板失败')
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
    bulkFile.value = null
    bulkFileName.value = ''
  }
}

const getValueClass = (row: IndicatorData) => {
  return 'value-text'
}

const isPercentIndicator = (name: string | undefined) => {
  if (!name) return false
  return /率|占比|比例|比率/.test(name)
}

const formatMetric = (
  row: IndicatorData,
  key: 'value' | 'benchmark' | 'challenge' | 'exemption' | 'zero_tolerance'
) => {
  const val = (row as any)[key]
  if (val === null || val === undefined) return ''
  if (isPercentIndicator(row.indicator_name)) {
    const num = Number(val)
    if (Number.isFinite(num)) return (num * 100).toFixed(2) + '%'
  }
  return String(val)
}

const handleRowClick = (row: IndicatorData) => {
  selectedIndicator.value = row
  dialogVisible.value = true
}

const handleSelectionChange = (rows: IndicatorData[]) => {
  selectedIds.value = rows.map(r => (r as any).id).filter(Boolean)
}

const handleDeleteSelected = async () => {
  if (selectedIds.value.length === 0) return
  try {
    await deleteIndicatorData({ ids: selectedIds.value })
    ElMessage.success('删除成功')
    selectedIds.value = []
    refresh()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '删除失败')
  }
}

const handleExport = async () => {
  try {
    const params: any = {
      indicator_id: filterForm.value.indicator_id,
      district_id: filterForm.value.district_id,
      district_ids: filterForm.value.district_id ? [filterForm.value.district_id] : undefined,
      circle_id: filterForm.value.circle_id,
      start_date: filterForm.value.dateRange?.[0],
      end_date: filterForm.value.dateRange?.[1],
      major_id: filterForm.value.major_id,
      type_id: filterForm.value.type_id,
      order_by: 'stat_date',
      desc: true
    }
    const blobOrResp = await exportMetrics(params)
    const blob = (blobOrResp as any).data ?? blobOrResp
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'metrics_export.xlsx'
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '导出失败')
  }
}

const handleExportSummary = async () => {
  try {
    const params: any = {
      indicator_id: filterForm.value.indicator_id,
      district_id: filterForm.value.district_id,
      district_ids: filterForm.value.district_id ? [filterForm.value.district_id] : undefined,
      circle_id: filterForm.value.circle_id,
      start_date: filterForm.value.dateRange?.[0],
      end_date: filterForm.value.dateRange?.[1],
      major_id: filterForm.value.major_id,
      type_id: filterForm.value.type_id,
      order_by: 'stat_date',
      desc: true
    }
    const blobOrResp = await exportMetricsSummary(params)
    const blob = (blobOrResp as any).data ?? blobOrResp
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'metrics_summary.xlsx'
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '汇总导出失败')
  }
}

const handleDeleteSingle = async (row: IndicatorData) => {
  const id = (row as any).id
  if (!id) return
  try {
    await deleteIndicatorData({ ids: [id] })
    ElMessage.success('删除成功')
    refresh()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '删除失败')
  }
}

const compareDialogVisible = ref(false)
const compareChartRef = ref<HTMLElement | null>(null)
let compareChart: echarts.ECharts | null = null
const editDialogVisible = ref(false)
const editForm = ref<{ indicator_id?: number; district_id?: number; stat_date?: string; value?: number; benchmark?: number; challenge?: number; exemption?: number; zero_tolerance?: number }>({})
const handleCompare = async (row: IndicatorData) => {
  try {
    compareDialogVisible.value = true
    await nextTick()
    if (!compareChartRef.value) return
    
    if (compareChart) {
      compareChart.dispose()
      compareChart = null
    }
    compareChart = echarts.init(compareChartRef.value)
    
    compareChart.showLoading()
    const res = await getIndicatorLatestById({ indicator_id: (row as any).indicator_id, stat_date: (row as any).stat_date })
    const arr: any[] = Array.isArray(res) ? res : []
    const x = arr.map(it => it.district_name)
    const y = arr.map(it => (it.value ?? null))
    const option: echarts.EChartsOption = {
      title: { text: `${row.indicator_name} 区县对比` },
      tooltip: { trigger: 'axis' },
      xAxis: { type: 'category', data: x, axisLabel: { interval: 0, rotate: 30 } },
      yAxis: { type: 'value' },
      series: [{ type: 'bar', data: y }],
      grid: { left: '6%', right: '6%', bottom: '16%', containLabel: true }
    }
    compareChart.setOption(option)
    compareChart.hideLoading()
  } catch (e) {
    console.error(e)
    compareChart?.hideLoading()
  }
}

const hasPerm = (code: string) => {
  return (userStore.permissions || []).includes(code)
}

const openEditSingle = (row: IndicatorData) => {
  editForm.value = {
    indicator_id: (row as any).indicator_id,
    district_id: (row as any).district_id,
    stat_date: (row as any).stat_date,
    value: (row as any).value,
    benchmark: (row as any).benchmark,
    challenge: (row as any).challenge,
    exemption: (row as any).exemption,
    zero_tolerance: (row as any).zero_tolerance
  }
  editDialogVisible.value = true
}

const submitEditSingle = async () => {
  const p = editForm.value
  if (!p.indicator_id || !p.district_id || !p.stat_date || p.value === undefined) { ElMessage.warning('请填写必填项'); return }
  try {
    await updateIndicatorData({
      indicator_id: p.indicator_id,
      district_id: p.district_id,
      stat_date: p.stat_date,
      value: p.value,
      benchmark: p.benchmark,
      challenge: p.challenge,
      exemption: p.exemption,
      zero_tolerance: p.zero_tolerance
    })
    ElMessage.success('已保存')
    editDialogVisible.value = false
    refresh()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '保存失败')
  }
}


onMounted(() => {
  fetchOptions()
  refresh()
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
