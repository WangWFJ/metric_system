<template>
  <div class="screen">
    <div class="topbar">
      <div class="title">数据大屏</div>
      <div class="meta">
        <div class="meta-item" v-if="displayedDate">数据日期：{{ displayedDate }}</div>
        <div class="meta-item">{{ nowText }}</div>
      </div>
    </div>

    <div class="filters">
      <el-select v-model="form.type_id" placeholder="考核类型" clearable style="width: 220px" @change="handleTypeChange">
        <el-option v-for="t in types" :key="t.type_id" :label="t.type_name" :value="t.type_id" />
      </el-select>
      <el-date-picker
        v-model="form.stat_date"
        type="date"
        value-format="YYYY-MM-DD"
        placeholder="选择日期"
        clearable
        style="width: 180px"
        @change="handleDateChange"
      />
      <el-select
        v-model="form.indicator_id"
        filterable
        remote
        reserve-keyword
        :remote-method="handleIndicatorSearch"
        :loading="indicatorSearchLoading"
        placeholder="搜索并选择指标"
        style="width: 340px"
        @change="handleIndicatorChange"
      >
        <el-option v-for="o in indicatorOptions" :key="o.indicator_id" :label="o.indicator_name" :value="o.indicator_id" />
      </el-select>
      <el-button type="primary" :loading="loading" @click="fetchData">刷新</el-button>
    </div>

    <div class="content">
      <div ref="leftPanelRef" class="panel left">
        <div class="chart-scroll">
          <DistrictRankingChart :title="chartTitle" :items="chartItems" :height="chartHeight" :value-suffix="valueSuffix" />
        </div>
      </div>
      <div class="panel right">
        <div class="panel-title">{{ tableTitle }}</div>
        <div class="table-wrap">
          <el-table :data="sortedAll" height="100%" stripe class="table" v-loading="loading">
            <el-table-column label="排名" width="70">
              <template #default="scope">
                <span class="rank">{{ scope.$index + 1 }}</span>
              </template>
            </el-table-column>
            <el-table-column :prop="entityNameKey" :label="entityLabel" min-width="140" show-overflow-tooltip />
            <el-table-column prop="value" label="完成值" min-width="120">
              <template #default="scope">
                <span class="num">{{ formatNum(scope.row.value) }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="stat_date" label="日期" min-width="120" />
          </el-table>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import DistrictRankingChart from '@/components/DistrictRankingChart.vue'
import { getEvaluationTypes, getIndicatorSuggestions, getIndicatorsByType, getIndicatorLatestById, getCenterLatestById, type EvaluationType, type IndicatorSimple, type IndicatorLatestItem } from '@/api/indicator'

const types = ref<EvaluationType[]>([])
const indicatorOptions = ref<IndicatorSimple[]>([])
const indicatorSearchLoading = ref(false)
const loading = ref(false)

const form = ref<{ type_id?: number; indicator_id?: number; stat_date?: string }>({ type_id: undefined, indicator_id: undefined, stat_date: undefined })
const nowText = ref('')
let timer: number | null = null
const leftPanelRef = ref<HTMLElement | null>(null)
const leftPanelHeight = ref(520)
let leftPanelRo: ResizeObserver | null = null

const indicatorName = ref('')
const displayedDate = ref('')
const raw = ref<Array<IndicatorLatestItem & { value: number | null; score?: number | null }>>([])

const isPercentIndicator = computed(() => /率|占比/.test(indicatorName.value || ''))
const valueSuffix = computed(() => (isPercentIndicator.value ? '%' : ''))

const isCenterType = computed(() => form.value.type_id === 3)
const entityLabel = computed(() => (isCenterType.value ? '支撑中心' : '区县'))
const entityNameKey = computed(() => (isCenterType.value ? 'center_name' : 'district_name'))
const chartTitle = computed(() => `${indicatorName.value || '指标'} 全${isCenterType.value ? '支撑中心' : '区县'}（高→低）`)
const tableTitle = computed(() => `${indicatorName.value || '指标'} 全${isCenterType.value ? '支撑中心' : '区县'}排名（高→低）`)

const sortedAll = ref<Array<any>>([])
const chartItems = ref<Array<{ name: string; value: number | null }>>([])

const panelChartHeight = computed(() => Math.max(360, leftPanelHeight.value - 24))
const chartHeight = computed(() => {
  const header = 56
  const row = 28
  const h = header + chartItems.value.length * row
  return Math.max(panelChartHeight.value, h)
})

const formatNum = (v: any) => {
  if (v === null || v === undefined || Number.isNaN(Number(v))) return ''
  const n = Number(v)
  if (isPercentIndicator.value) {
    const pct = Math.abs(n) <= 1 ? n * 100 : n
    return `${pct.toFixed(2).replace(/0+$/, '').replace(/\.$/, '')}%`
  }
  if (Number.isInteger(n)) return String(n)
  return n.toFixed(4).replace(/0+$/, '').replace(/\.$/, '')
}

const applySort = () => {
  const arr = raw.value.slice()
  const toNum = (v: any) => (v === null || v === undefined ? null : Number(v))
  const ranked = arr
    .map(it => ({
      ...it,
      value: toNum((it as any).value),
    }))
    .sort((a, b) => {
      const av = (a as any).value
      const bv = (b as any).value
      if (av === null && bv === null) return a.district_name.localeCompare(b.district_name)
      if (av === null) return 1
      if (bv === null) return -1
      return Number(bv) - Number(av)
    })

  sortedAll.value = ranked.map(it => ({
    district_id: (it as any).district_id,
    district_name: (it as any).district_name,
    center_id: (it as any).center_id,
    center_name: (it as any).center_name,
    stat_date: it.stat_date,
    value: it.value,
  }))

  chartItems.value = ranked.map(it => {
    const v = (it as any).value as number | null
    const name = (it as any)[entityNameKey.value] as string
    if (v === null || v === undefined) return { name, value: null }
    if (isPercentIndicator.value && Math.abs(v) <= 1) return { name, value: Number((v * 100).toFixed(6)) }
    return { name, value: v }
  })
}

const handleIndicatorSearch = async (q: string) => {
  if (!q || q.length < 2) {
    indicatorOptions.value = []
    return
  }
  indicatorSearchLoading.value = true
  try {
    indicatorOptions.value = await getIndicatorSuggestions({ q, type_id: form.value.type_id, size: 20 })
  } catch {
    indicatorOptions.value = []
  } finally {
    indicatorSearchLoading.value = false
  }
}

const handleTypeChange = async () => {
  if (!form.value.type_id) return
  try {
    const list = await getIndicatorsByType(form.value.type_id)
    indicatorOptions.value = list
  } catch {
    indicatorOptions.value = []
  }
}

const handleDateChange = () => {
  if (!form.value.indicator_id) return
  fetchData()
}

const handleIndicatorChange = () => {
  const id = form.value.indicator_id
  if (!id) return
  const found = indicatorOptions.value.find(i => i.indicator_id === id)
  if (found) indicatorName.value = found.indicator_name
  fetchData()
}

const fetchData = async () => {
  if (!form.value.indicator_id) {
    ElMessage.warning('请选择指标')
    return
  }
  loading.value = true
  try {
    const res = isCenterType.value
      ? await getCenterLatestById({ indicator_id: form.value.indicator_id, stat_date: form.value.stat_date || undefined })
      : await getIndicatorLatestById({ indicator_id: form.value.indicator_id, stat_date: form.value.stat_date || undefined })
    const arr: any[] = Array.isArray(res) ? res : []
    if (arr.length && arr[0].indicator_name) indicatorName.value = String(arr[0].indicator_name)
    displayedDate.value = form.value.stat_date || (arr.length ? String(arr[0].stat_date || '') : '')
    raw.value = arr.map(it => ({
      ...it,
      value: it.value ?? null,
    }))
    applySort()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail?.message || e?.response?.data?.detail || '加载失败')
  } finally {
    loading.value = false
  }
}

const tickNow = () => {
  const d = new Date()
  const yyyy = d.getFullYear()
  const mm = String(d.getMonth() + 1).padStart(2, '0')
  const dd = String(d.getDate()).padStart(2, '0')
  const hh = String(d.getHours()).padStart(2, '0')
  const mi = String(d.getMinutes()).padStart(2, '0')
  const ss = String(d.getSeconds()).padStart(2, '0')
  nowText.value = `${yyyy}-${mm}-${dd} ${hh}:${mi}:${ss}`
}

const fetchTypes = async () => {
  try {
    types.value = await getEvaluationTypes()
  } catch {}
}

onMounted(() => {
  fetchTypes()
  tickNow()
  timer = window.setInterval(tickNow, 1000)
  nextTick(() => {
    if (!leftPanelRef.value) return
    leftPanelHeight.value = leftPanelRef.value.clientHeight
    leftPanelRo = new ResizeObserver(() => {
      if (!leftPanelRef.value) return
      leftPanelHeight.value = leftPanelRef.value.clientHeight
    })
    leftPanelRo.observe(leftPanelRef.value)
  })
})

onUnmounted(() => {
  if (timer) window.clearInterval(timer)
  timer = null
  leftPanelRo?.disconnect()
  leftPanelRo = null
})
</script>

<style scoped>
.screen {
  width: 100%;
  min-height: calc(100vh - 60px);
  background: radial-gradient(1200px 500px at 50% 0%, rgba(99, 102, 241, 0.28), rgba(15, 23, 42, 0.95)),
    linear-gradient(180deg, rgba(2, 6, 23, 0.98), rgba(2, 6, 23, 0.98));
  border-radius: 16px;
  padding: 16px;
  color: #e5e7eb;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.topbar {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 12px;
}

.title {
  font-size: 22px;
  font-weight: 700;
  letter-spacing: 1px;
}

.meta {
  display: flex;
  gap: 12px;
  align-items: center;
  color: rgba(226, 232, 240, 0.88);
  font-size: 12px;
}

.filters {
  display: flex;
  gap: 10px;
  align-items: center;
  flex-wrap: wrap;
}

.content {
  flex: 1;
  display: grid;
  grid-template-columns: 1.1fr 1fr;
  gap: 12px;
  min-height: 520px;
}

.panel {
  background: rgba(15, 23, 42, 0.65);
  border: 1px solid rgba(148, 163, 184, 0.18);
  border-radius: 16px;
  padding: 12px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.chart-scroll {
  flex: 1;
  height: 0;
  overflow-y: auto;
  overflow-x: hidden;
  padding-right: 6px;
}

.panel-title {
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 10px;
  color: #e5e7eb;
}

.table {
  width: 100%;
  flex: 1;
}

.table-wrap {
  flex: 1;
  height: 0;
}

.rank {
  font-weight: 700;
}

.num {
  font-variant-numeric: tabular-nums;
}

:deep(.el-select),
:deep(.el-input__wrapper) {
  --el-input-bg-color: rgba(2, 6, 23, 0.62);
  --el-input-border-color: rgba(148, 163, 184, 0.42);
  --el-text-color-regular: #f8fafc;
  --el-border-color: rgba(148, 163, 184, 0.42);
}

:deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 1px rgba(96, 165, 250, 0.7) inset;
}

:deep(.el-input__inner::placeholder) {
  color: rgba(226, 232, 240, 0.75);
}

:deep(.el-select .el-input__inner) {
  color: #f8fafc;
}

:deep(.filters .el-select__wrapper),
:deep(.filters .el-date-editor .el-input__wrapper),
:deep(.filters .el-select .el-input__wrapper),
:deep(.filters .el-input__wrapper) {
  background-color: rgba(2, 6, 23, 0.62);
}

:deep(.filters .el-input__prefix-inner),
:deep(.filters .el-input__suffix-inner),
:deep(.filters .el-select__caret) {
  color: rgba(248, 250, 252, 0.92);
}

:deep(.el-table) {
  --el-table-bg-color: transparent;
  --el-table-tr-bg-color: transparent;
  --el-table-header-bg-color: rgba(15, 23, 42, 0.55);
  --el-table-text-color: #f8fafc;
  --el-table-border-color: rgba(148, 163, 184, 0.18);
  --el-fill-color-lighter: rgba(255, 255, 255, 0.05);
}

:deep(.el-table th.el-table__cell) {
  color: rgba(226, 232, 240, 0.92);
}

:deep(.el-table--striped .el-table__body tr.el-table__row--striped td.el-table__cell) {
  background: rgba(255, 255, 255, 0.06);
}

:deep(.el-table__body tr:hover > td.el-table__cell) {
  background: rgba(96, 165, 250, 0.10);
}
</style>
