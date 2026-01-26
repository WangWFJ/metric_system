<template>
  <div ref="chartRef" style="width: 100%; height: 380px;"></div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue'
import * as echarts from 'echarts'
import { getCenterSeries } from '@/api/indicator'

const props = defineProps<{
  indicatorId: number
  centerId?: number
  title?: string
  startDate?: string
  endDate?: string
}>()

const chartRef = ref<HTMLElement | null>(null)
let chart: echarts.ECharts | null = null
let ro: ResizeObserver | null = null

const render = async () => {
  if (!chart) return
  if (!props.indicatorId) return
  const res = await getCenterSeries({
    indicator_id: props.indicatorId,
    center_id: props.centerId,
    start_date: props.startDate,
    end_date: props.endDate,
    size: 500,
  })
  const items = res.items || []
  const x = items.map((i: any) => i.stat_date)
  const y = items.map((i: any) => (i.value ?? null))

  const option: echarts.EChartsOption = {
    title: props.title ? { text: props.title, left: 10, top: 10 } : undefined,
    tooltip: { trigger: 'axis' },
    grid: { left: 12, right: 12, top: props.title ? 44 : 16, bottom: 24, containLabel: true },
    xAxis: { type: 'category', data: x, axisLabel: { rotate: 35 } },
    yAxis: { type: 'value' },
    series: [{ type: 'line', data: y, smooth: true, showSymbol: false, connectNulls: false }],
  }
  chart.setOption(option, true)
}

const init = () => {
  if (!chartRef.value) return
  chart = echarts.init(chartRef.value)
  ro = new ResizeObserver(() => chart?.resize())
  ro.observe(chartRef.value)
  window.addEventListener('resize', handleResize)
  render()
}

const destroy = () => {
  window.removeEventListener('resize', handleResize)
  ro?.disconnect()
  ro = null
  chart?.dispose()
  chart = null
}

const handleResize = () => chart?.resize()

onMounted(init)
onUnmounted(destroy)

watch(
  () => [props.indicatorId, props.centerId, props.startDate, props.endDate],
  () => render()
)
</script>
