import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getIndicatorData, type IndicatorData, type IndicatorParams } from '@/api/indicator'

export const useIndicatorStore = defineStore('indicator', () => {
  const indicators = ref<IndicatorData[]>([])
  const total = ref(0)
  const loading = ref(false)

  const fetchIndicators = async (params?: IndicatorParams) => {
    loading.value = true
    try {
      const res = await getIndicatorData(params)
      indicators.value = res.items
      total.value = res.total
    } catch (error) {
      console.error('Fetch indicators failed:', error)
    } finally {
      loading.value = false
    }
  }

  return { indicators, total, loading, fetchIndicators }
})
