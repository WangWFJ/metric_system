<template>
  <div ref="chartRef" :style="{ width: '100%', height: chartHeight + 'px' }"></div>
  </template>

<script setup lang="ts">
import { ref, onMounted, watch, onUnmounted, nextTick } from 'vue'
import * as echarts from 'echarts'
import { getIndicatorSeries } from '@/api/indicator'
// no dayjs; use native Date formatting

const props = defineProps<{
  indicatorId: number
  indicatorName: string
  districtId?: number
}>()

const chartRef = ref<HTMLElement | null>(null)
let chartInstance: echarts.ECharts | null = null
const chartHeight = ref(400)
const zoomStart = ref(0)

const initChart = () => {
  if (chartRef.value) {
    chartInstance = echarts.init(chartRef.value)
  }
}

const fetchDataAndRender = async () => {
  if (!props.indicatorId) return
  
  chartInstance?.showLoading()
  try {
    const res = await getIndicatorSeries({
      indicator_id: props.indicatorId,
      district_id: props.districtId,
      size: 180
    })
    const items = Array.isArray(res) ? res : res.items
    const len = items.length || 0
    // auto adjust height
    chartHeight.value = len <= 30 ? 340 : len <= 60 ? 400 : len <= 120 ? 480 : 560
    // auto set initial dataZoom to show last N points
    const windowSize = len <= 60 ? len : 60
    zoomStart.value = len > windowSize ? Math.max(0, 100 - Math.round(windowSize / len * 100)) : 0
    if (props.districtId) {
      const seriesData = items.map((item: any) => [item.stat_date as string, (item.value ?? null) as number | null] as [string, number | null])
      renderOption([{ name: props.indicatorName, data: seriesData }])
    } else {
      const groups: Record<string, Array<[string, number | null]>> = {}
      for (const it of items as any[]) {
        const key = it.district_name || ''
        if (!groups[key]) groups[key] = []
        groups[key].push([it.stat_date as string, it.value ?? null])
      }
      const seriesArr = Object.keys(groups).map(k => ({
        name: k,
        data: groups[k].sort((a, b) => (a[0] > b[0] ? 1 : -1))
      }))
      renderOption(seriesArr)
    }
    
    
  } catch (e) {
    console.error(e)
  } finally {
  chartInstance?.hideLoading()
  }
}

const renderOption = (seriesArr: Array<{ name: string, data: Array<[string, number | null]> }>) => {
  const option = {
    title: { text: props.indicatorName + ' 趋势（折线图）', left: 'center', top: 8 },
    tooltip: { trigger: 'axis' },
    legend: { top: 36 },
    grid: { left: '6%', right: '6%', top: 80, bottom: '14%', containLabel: true },
    xAxis: { type: 'time', boundaryGap: false, axisLabel: { rotate: 45, hideOverlap: true, formatter: (value: number) => {
      const d = new Date(value)
      const mm = String(d.getMonth() + 1).padStart(2, '0')
      const dd = String(d.getDate()).padStart(2, '0')
      return `${mm}月${dd}日`
    } } },
    yAxis: { type: 'value' },
    dataZoom: [
      { type: 'slider', start: zoomStart.value, end: 100 },
      { type: 'inside' }
    ],
    series: seriesArr.map(s => ({
      name: s.name,
      type: 'line',
      smooth: true,
      symbol: 'circle',
      symbolSize: 4,
      data: s.data
    }))
  }
  chartInstance?.setOption(option)
  nextTick(() => chartInstance?.resize())
}
onMounted(() => {
  initChart()
  fetchDataAndRender()
  if (chartRef.value) {
    const ro = new ResizeObserver(() => chartInstance?.resize())
    ro.observe(chartRef.value)
  }
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  chartInstance?.dispose()
})

const handleResize = () => {
  chartInstance?.resize()
}

watch(() => [props.indicatorId, props.districtId], () => {
  fetchDataAndRender()
})
</script>
