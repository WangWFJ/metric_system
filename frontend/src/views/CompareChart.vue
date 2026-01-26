<template>
  <div class="compare-container">
    <el-card class="filter-card" shadow="never" style="margin-bottom: 12px;">
      <el-form :inline="true">
        <el-form-item label="指标">
          <el-select
            v-model="form.indicator_id"
            placeholder="搜索指标名称"
            clearable
            filterable
            remote
            :remote-method="handleIndicatorSearch"
            :loading="indicatorSearchLoading"
            style="width: 240px;"
          >
            <el-option v-for="item in indicatorOptions" :key="item.indicator_id" :label="item.indicator_name" :value="item.indicator_id" />
          </el-select>
        </el-form-item>
        <el-form-item label="多指标">
          <el-select
            v-model="multiIndicatorIds"
            multiple
            collapse-tags
            placeholder="选择多个指标"
            filterable
            remote
            :remote-method="handleIndicatorSearch"
            :loading="indicatorSearchLoading"
            style="width: 320px;"
          >
            <el-option v-for="item in indicatorOptions" :key="item.indicator_id" :label="item.indicator_name" :value="item.indicator_id" />
          </el-select>
        </el-form-item>
        <el-form-item label="考核类型">
          <el-select v-model="form.type_id" placeholder="选择类型" clearable style="width: 200px;">
            <el-option v-for="t in types" :key="t.type_id" :label="t.type_name" :value="t.type_id" />
          </el-select>
        </el-form-item>
        <el-form-item label="日期">
          <el-date-picker v-model="form.stat_date" type="date" placeholder="选择日期" value-format="YYYY-MM-DD" />
        </el-form-item>
        <el-form-item label="区县">
          <el-select v-model="form.district_ids" multiple collapse-tags placeholder="选择区县" style="width: 280px;">
            <el-option v-for="d in districts" :key="d.district_id" :label="d.district_name" :value="d.district_id" />
          </el-select>
        </el-form-item>
        
        <el-form-item>
          <el-checkbox v-model="selectAll">全选区县</el-checkbox>
        </el-form-item>
        <el-form-item>
          <el-button @click="reset">重置</el-button>
        </el-form-item>
  </el-form>
  </el-card>

  <el-card shadow="never" style="margin-bottom: 12px;">
      <div style="font-weight:600;margin-bottom:6px;">图表显示</div>
      <div style="color:#606266;margin-bottom:8px;">
        <span>指标：{{ indicatorName || '-' }}</span>
        <span v-if="viewMode === 'compare'" style="margin-left:16px;">时间：{{ displayedDate || '-' }}</span>
        <span style="margin-left:16px;">单位：{{ unit || '-' }}</span>
      </div>
      <div style="margin-bottom:8px;">
        <el-radio-group v-model="viewMode" size="small">
          <el-radio-button value="compare">区县对比</el-radio-button>
          <el-radio-button value="trend">时间趋势</el-radio-button>
        </el-radio-group>
      </div>

      <div v-if="viewMode === 'compare'" v-loading="loading" style="min-height: 120px;">
        <div v-if="items.length === 0" style="padding: 24px; text-align: center; color: #909399;">暂无数据</div>
        <div v-else ref="chartRef" style="width:100%;height:420px;"></div>
        <div v-if="items.length > 0" style="margin-top:8px;">
          <el-radio-group v-model="chartType" size="small">
            <el-radio-button value="bar">柱状图</el-radio-button>
            <el-radio-button value="line">折线图</el-radio-button>
          </el-radio-group>
        </div>
      </div>

      <div v-else>
        <el-form :inline="true" style="margin-bottom:8px;">
          <el-form-item label="趋势区县">
            <el-select v-model="trendDistrictId" placeholder="选择区县" clearable style="width: 220px;">
              <el-option v-for="d in districts" :key="d.district_id" :label="d.district_name" :value="d.district_id" />
            </el-select>
          </el-form-item>
          <el-form-item label="趋势指标">
            <el-select
              v-model="multiTrendIds"
              multiple
              collapse-tags
              placeholder="选择多个指标"
              filterable
              remote
              :remote-method="handleIndicatorSearch"
              :loading="indicatorSearchLoading"
              style="width: 380px;"
            >
              <el-option v-for="item in indicatorOptions" :key="item.indicator_id" :label="item.indicator_name" :value="item.indicator_id" />
            </el-select>
          </el-form-item>
        </el-form>
        <div v-if="!trendDistrictId" style="padding: 24px; text-align:center; color:#909399;">请选择趋势区县</div>
        <div v-else>
          <template v-if="multiTrendIds.length > 0">
            <el-row :gutter="12">
              <el-col v-for="id in multiTrendIds" :key="id" :span="12">
                <el-card shadow="never" style="margin-bottom:12px;">
                  <IndicatorChart :indicator-id="id" :indicator-name="indicatorNameMap.get(id) || ('指标 ' + id)" :district-id="trendDistrictId" />
                </el-card>
              </el-col>
            </el-row>
          </template>
          <template v-else>
            <div v-if="!form.indicator_id" style="padding: 24px; text-align:center; color:#909399;">请选择指标</div>
            <IndicatorChart v-else :indicator-id="form.indicator_id!" :indicator-name="indicatorName" :district-id="trendDistrictId" />
          </template>
        </div>
      </div>
  </el-card>

  <el-card shadow="never">
    <div style="font-weight:600;margin-bottom:6px;display:flex;justify-content:space-between;align-items:center;">
      <span>多指标图表（考核类型：{{ types.find(t=>t.type_id===form.type_id)?.type_name || '-' }}）</span>
      <el-radio-group v-model="multiChartType" size="small">
        <el-radio-button value="bar">柱状图</el-radio-button>
        <el-radio-button value="line">折线图</el-radio-button>
      </el-radio-group>
    </div>
    <div v-if="multiIndicators.length === 0" style="padding:12px;color:#909399;">选择考核类型后将自动展示该类型下所有指标的区县对比图</div>
    <el-row :gutter="12">
      <el-col v-for="ind in multiIndicators" :key="ind.indicator_id" :span="12">
        <el-card shadow="never" style="margin-bottom:12px;">
          <div style="font-weight:600;margin-bottom:6px;">{{ ind.indicator_name }}</div>
          <div :ref="el => setMultiChartRef(ind.indicator_id, el)" style="width:100%;height:320px;"></div>
        </el-card>
      </el-col>
    </el-row>
  </el-card>
</div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, nextTick, computed } from 'vue'
import * as echarts from 'echarts'
import { getIndicatorLatestById, getEvaluationTypes, getDistricts, getIndicatorSuggestions, getIndicatorsByType, getIndicatorsList, type IndicatorSimple, type EvaluationType, type District } from '@/api/indicator'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import IndicatorChart from '@/components/IndicatorChart.vue'

const route = useRoute()
const initialIndicatorId = Number(route.query.indicator_id || 0)
const indicatorName = ref<string>((route.query.indicator_name as string) || '')
const unit = (route.query.unit as string) || ''

const chartType = ref<'bar' | 'line'>('bar')
const chartRef = ref<HTMLElement | null>(null)
let chart: echarts.ECharts | null = null

const viewMode = ref<'compare' | 'trend'>('compare')
const trendDistrictId = ref<number | undefined>(undefined)

const items = ref<Array<{ name: string; value: number | null }>>([])
const loading = ref(false)
const displayedDate = ref('')
const types = ref<EvaluationType[]>([])
const districts = ref<District[]>([])
const indicatorOptions = ref<IndicatorSimple[]>([])
const indicatorSearchLoading = ref(false)
// 多指标图表
const multiChartType = ref<'bar' | 'line'>('bar')
const multiIndicators = ref<IndicatorSimple[]>([])
const multiChartRefs = ref<Record<number, HTMLElement | null>>({})
const multiChartMap = new Map<number, echarts.ECharts>()
const multiIndicatorIds = ref<number[]>([])
const indicatorNameMap = new Map<number, string>()
const multiTrendIds = ref<number[]>([])
const form = ref<{ indicator_id?: number; type_id?: number; stat_date?: string; district_ids: number[]; circle_id?: number }>({
  indicator_id: initialIndicatorId || undefined,
  type_id: undefined,
  stat_date: (route.query.stat_date as string) || '',
  district_ids: [],
  circle_id: undefined
})
const selectAll = computed({
  get() {
    const allIds = rawItems.map(i => i.id)
    if (allIds.length === 0) return false
    if (form.value.district_ids.length !== allIds.length) return false
    const set = new Set(form.value.district_ids)
    return allIds.every(id => set.has(id))
  },
  set(v: boolean) {
    const allIds = rawItems.map(i => i.id)
    form.value.district_ids = v ? allIds : []
  }
})
let rawItems: Array<{ id: number; name: string; value: number | null; circle_id: number }> = []
const layers = ref<number[]>([])

const fetchOptions = async () => {
  try {
    const [t, d] = await Promise.all([getEvaluationTypes(), getDistricts()])
    types.value = t
    districts.value = d
  } catch (e) {}
}

const fetchData = async () => {
  loading.value = true
  try {
    const res = await getIndicatorLatestById({ indicator_id: form.value.indicator_id, stat_date: form.value.stat_date || undefined })
    const arr: any[] = Array.isArray(res) ? res : []
    displayedDate.value = form.value.stat_date || (arr.length ? String(arr[0].stat_date) : '')
    if (arr.length && (arr[0] as any).indicator_name) {
      indicatorName.value = (arr[0] as any).indicator_name || indicatorName.value
    }
    rawItems = arr.map(it => ({ name: it.district_name, value: (it.value ?? null) as any, id: it.district_id, circle_id: it.circle_id }))
    layers.value = Array.from(new Set(rawItems.map(i => i.circle_id))).sort((a,b)=>a-b)
    applyFilters()
    await nextTick()
    renderChart()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '加载失败')
  } finally {
    loading.value = false
  }
}

const handleIndicatorSearch = async (q: string) => {
  if (!q || q.length < 2) { indicatorOptions.value = []; return }
  indicatorSearchLoading.value = true
  try {
    indicatorOptions.value = await getIndicatorSuggestions({ q, type_id: form.value.type_id, size: 20 })
    for (const it of indicatorOptions.value) indicatorNameMap.set(it.indicator_id, it.indicator_name)
  } catch { indicatorOptions.value = [] } finally { indicatorSearchLoading.value = false }
}

const applyFilters = () => {
  let tmp = rawItems.slice()
  if (form.value.district_ids && form.value.district_ids.length) {
    const set = new Set(form.value.district_ids)
    tmp = tmp.filter(i => set.has(i.id))
  }
  items.value = tmp.map(i => ({ name: i.name, value: i.value }))
}

const query = () => {
  if (form.value.indicator_id) {
    fetchData()
  } else {
    ElMessage.warning('请选择指标')
  }
}
const reset = () => {
  form.value = { indicator_id: undefined, type_id: undefined, stat_date: '', district_ids: [] }
  indicatorOptions.value = []
  items.value = []
  rawItems = []
}
const renderChart = () => {
  if (viewMode.value !== 'compare') return
  if (!chartRef.value) return
  
  if (chart && chart.getDom() !== chartRef.value) {
    chart.dispose()
    chart = null
  }
  
  if (!chart) chart = echarts.init(chartRef.value)
  const x = items.value.map(i => i.name)
  const y = items.value.map(i => i.value)
  const option: echarts.EChartsOption = {
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: x, axisLabel: { interval: 0, rotate: 30 } },
    yAxis: { type: 'value' },
    series: [{
      name: '数值',
      type: chartType.value,
      data: y
    }],
    grid: { left: '6%', right: '6%', bottom: '16%', containLabel: true },
    title: { text: `${indicatorName.value || ''} 区县对比` }
  }
  chart.clear()
  chart.setOption(option)
  chart.resize()
}

const setMultiChartRef = (id: number, el: any) => {
  const dom = (el && (el instanceof Element || el instanceof HTMLElement)) ? (el as HTMLElement) : null
  multiChartRefs.value[id] = dom
  if (!dom) return
  const exists = multiChartMap.get(id)
  if (exists) {
    if (exists.getDom() !== dom) {
      exists.dispose()
      multiChartMap.delete(id)
    } else {
      return
    }
  }
  const inst = echarts.init(dom)
  multiChartMap.set(id, inst)
}

const fetchAndRenderOne = async (id: number, name: string) => {
  const res = await getIndicatorLatestById({ indicator_id: id, stat_date: form.value.stat_date || undefined })
  const arr: any[] = Array.isArray(res) ? res : []
  let tmp = arr.map(it => ({ name: it.district_name, value: (it.value ?? null) as any, id: it.district_id }))
  if (form.value.district_ids && form.value.district_ids.length) {
    const set = new Set(form.value.district_ids)
    tmp = tmp.filter(i => set.has(i.id))
  }
  const x = tmp.map(i => i.name)
  const y = tmp.map(i => i.value)
  const inst = multiChartMap.get(id)
  if (!inst) return
  const option: echarts.EChartsOption = {
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: x, axisLabel: { interval: 0, rotate: 30 } },
    yAxis: { type: 'value' },
    series: [{ type: multiChartType.value, data: y }],
    grid: { left: '6%', right: '6%', bottom: '16%', containLabel: true },
    title: { text: `${name} 区县对比` }
  }
  inst.clear()
  inst.setOption(option)
  inst.resize()
}

const loadTypeIndicators = async () => {
  if (!form.value.type_id) { multiIndicators.value = []; return }
  try {
    const list = await getIndicatorsByType(form.value.type_id)
    multiIndicators.value = list
    for (const it of list) indicatorNameMap.set(it.indicator_id, it.indicator_name)
    // 等下一帧确保容器挂载
    await nextTick()
    for (const ind of list) {
      await fetchAndRenderOne(ind.indicator_id, ind.indicator_name)
    }
  } catch (e) {
    ElMessage.error('加载类型指标失败')
    multiIndicators.value = []
  }
}

const loadSelectedIndicators = async () => {
  if (!multiIndicatorIds.value.length) { multiIndicators.value = []; return }
  // 用当前搜索结果映射名称，若缺失可回退为ID
  // 优先使用持久缓存
  let missing: number[] = []
  const pairs: IndicatorSimple[] = []
  for (const id of multiIndicatorIds.value) {
    const name = indicatorNameMap.get(id)
    if (!name) missing.push(id)
    pairs.push({ indicator_id: id, indicator_name: name || `指标 ${id}` })
  }
  if (missing.length) {
    try {
      const all = await getIndicatorsList()
      for (const it of all) indicatorNameMap.set(it.indicator_id, it.indicator_name)
      for (const p of pairs) {
        if (p.indicator_name.startsWith('指标 ')) {
          const n = indicatorNameMap.get(p.indicator_id)
          if (n) p.indicator_name = n
        }
      }
    } catch {}
  }
  multiIndicators.value = pairs
  await nextTick()
  for (const ind of multiIndicators.value) {
    await fetchAndRenderOne(ind.indicator_id, ind.indicator_name)
  }
}

onMounted(() => {
  fetchOptions()
  if (form.value.indicator_id) fetchData()
  window.addEventListener('resize', () => chart?.resize())
})

onUnmounted(() => {
  if (chart) {
    chart.dispose()
    chart = null
  }
  for (const inst of multiChartMap.values()) inst.dispose()
  multiChartMap.clear()
})

watch(chartType, async () => {
  if (viewMode.value !== 'compare') return
  await nextTick()
  renderChart()
})
watch(multiChartType, async () => {
  await nextTick()
  for (const ind of multiIndicators.value) {
    await fetchAndRenderOne(ind.indicator_id, ind.indicator_name)
  }
})
watch(() => [form.value.indicator_id, form.value.stat_date], ([id]) => {
  if (viewMode.value === 'compare' && id) fetchData()
})
watch(() => [form.value.type_id, form.value.stat_date], () => {
  loadTypeIndicators()
})
watch(multiIndicatorIds, () => {
  loadSelectedIndicators()
})
watch(() => form.value.district_ids, async () => {
  if (viewMode.value !== 'compare') return
  applyFilters()
  await nextTick()
  renderChart()
  // 同步更新多图
  for (const ind of multiIndicators.value) {
    await fetchAndRenderOne(ind.indicator_id, ind.indicator_name)
  }
})

watch(viewMode, async (m) => {
  if (m === 'compare') {
    await nextTick()
    renderChart()
  }
})
</script>

<style scoped>
.compare-container { padding: 10px; }
</style>
