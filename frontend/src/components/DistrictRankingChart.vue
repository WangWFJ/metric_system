<template>
  <div ref="chartRef" :style="{ width: '100%', height: height + 'px' }"></div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'
import * as echarts from 'echarts'

type Item = { name: string; value: number | null }

const props = withDefaults(defineProps<{
  title?: string
  items: Item[]
  height?: number
  valueSuffix?: string
}>(), {
  title: '',
  height: 360,
  valueSuffix: '',
})

const chartRef = ref<HTMLElement | null>(null)
let chart: echarts.ECharts | null = null
let ro: ResizeObserver | null = null

const render = () => {
  if (!chart) return
  const names = props.items.map(i => i.name)
  const values = props.items.map(i => i.value)
  const fmt = (v: any) => {
    if (v === null || v === undefined || Number.isNaN(Number(v))) return ''
    return `${v}${props.valueSuffix || ''}`
  }
  const option: echarts.EChartsOption = {
    backgroundColor: 'transparent',
    title: props.title ? { text: props.title, left: 10, top: 10, textStyle: { color: '#E5E7EB', fontSize: 14, fontWeight: 600 } } : undefined,
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      formatter: (params: any) => {
        const arr = Array.isArray(params) ? params : [params]
        const first = arr[0]
        const name = first?.axisValueLabel ?? first?.name ?? ''
        const val = first?.value
        return `${name}<br/>${fmt(val)}`
      },
    },
    grid: { left: 12, right: 12, top: props.title ? 44 : 16, bottom: 12, containLabel: true },
    xAxis: {
      type: 'value',
      axisLabel: { color: '#9CA3AF', formatter: (v: any) => fmt(v) },
      splitLine: { lineStyle: { color: 'rgba(148,163,184,0.15)' } },
    },
    yAxis: {
      type: 'category',
      data: names,
      inverse: true,
      axisLabel: { color: '#E5E7EB', width: 120, overflow: 'truncate' },
      axisTick: { show: false },
      axisLine: { show: false },
    },
    series: [
      {
        type: 'bar',
        data: values,
        barWidth: 14,
        itemStyle: {
          borderRadius: [4, 4, 4, 4],
          color: new echarts.graphic.LinearGradient(1, 0, 0, 0, [
            { offset: 0, color: '#22C55E' },
            { offset: 0.55, color: '#60A5FA' },
            { offset: 1, color: '#A855F7' },
          ]),
        },
        label: { show: true, position: 'right', color: '#E5E7EB', formatter: (p: any) => fmt(p.value) },
      },
    ],
  }
  chart.setOption(option, true)
  nextTick(() => chart?.resize())
}

onMounted(() => {
  if (chartRef.value) {
    chart = echarts.init(chartRef.value)
    ro = new ResizeObserver(() => chart?.resize())
    ro.observe(chartRef.value)
    window.addEventListener('resize', handleResize)
    render()
  }
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  ro?.disconnect()
  ro = null
  chart?.dispose()
  chart = null
})

const handleResize = () => {
  chart?.resize()
}

watch(() => props.items, () => render(), { deep: true })
watch(() => props.title, () => render())
watch(() => props.height, () => nextTick(() => chart?.resize()))
</script>
