<template>
  <div>
    <van-cell-group inset>
      <van-cell title="统计年份" :value="year + ' 年'">
        <template #right-icon>
          <van-stepper v-model="year" min="2015" :max="2099" integer style="margin-left:8px;" @change="load" />
        </template>
      </van-cell>
      <van-cell title="年度总花费" :value="'¥' + (cost?.total ?? 0)" />
    </van-cell-group>

    <div style="margin-top:12px;background:#fff;border-radius:10px;padding:12px;">
      <div style="font-size:14px;font-weight:600;margin-bottom:8px;">年度费用分类（元）</div>
      <div ref="costChart" style="width:100%;height:220px;"></div>
    </div>

    <div style="margin-top:12px;background:#fff;border-radius:10px;padding:12px;">
      <div style="font-size:14px;font-weight:600;margin-bottom:8px;">油耗趋势（L/100km）</div>
      <div v-if="fuel?.points?.length" ref="fuelChart" style="width:100%;height:220px;"></div>
      <van-empty v-else description="暂无油耗数据（需两次加满记录）" image-size="60" />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import * as echarts from 'echarts'
import { showFailToast } from 'vant'
import api from '../api'

const route = useRoute()
const vehicleId = route.params.id
const year = ref(new Date().getFullYear())
const cost = ref(null)
const fuel = ref(null)
const costChart = ref(null)
const fuelChart = ref(null)
let charts = []

onMounted(load)

async function load() {
  try {
    cost.value = await api.get('/stats/annual-cost', { params: { vehicle_id: vehicleId, year: year.value } })
    fuel.value = await api.get('/stats/fuel-trend', { params: { vehicle_id: vehicleId } })
    await nextTick()
    renderCharts()
  } catch (e) { showFailToast(e.message) }
}

function renderCharts() {
  charts.forEach(c => c.dispose())
  charts = []
  if (costChart.value) {
    const c = echarts.init(costChart.value)
    c.setOption({
      tooltip: { trigger: 'item' },
      xAxis: { type: 'category', data: cost.value.categories.map(x => x.name), axisLabel: { color: '#666', fontSize: 11 } },
      yAxis: { type: 'value', axisLabel: { color: '#666', fontSize: 11 } },
      series: [{
        type: 'bar',
        data: cost.value.categories.map(x => x.amount),
        itemStyle: { color: '#1989fa', borderRadius: [4, 4, 0, 0] },
        label: { show: true, position: 'top', fontSize: 10, color: '#666' }
      }]
    })
    charts.push(c)
  }
  if (fuelChart.value && fuel.value.points.length) {
    const c = echarts.init(fuelChart.value)
    c.setOption({
      tooltip: { trigger: 'axis' },
      xAxis: { type: 'category', data: fuel.value.points.map(p => p.date), axisLabel: { color: '#666', fontSize: 10, rotate: 30 } },
      yAxis: { type: 'value', name: 'L/100km', axisLabel: { color: '#666', fontSize: 11 } },
      series: [{
        type: 'line', smooth: true,
        data: fuel.value.points.map(p => p.l100),
        itemStyle: { color: '#ff976a' }, lineStyle: { color: '#ff976a' },
        areaStyle: { opacity: 0.1 },
        markLine: fuel.value.overall_l100 ? { data: [{ yAxis: fuel.value.overall_l100 }], label: { formatter: '均值 ' + fuel.value.overall_l100, fontSize: 10 } } : undefined
      }]
    })
    charts.push(c)
  }
}

onBeforeUnmount(() => charts.forEach(c => c.dispose()))
</script>
