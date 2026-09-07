<template>
  <div>
    <van-skeleton title :row="5" v-if="loading" />

    <template v-else>
      <!-- 概览卡片 -->
      <van-cell-group inset>
        <van-cell>
          <template #title>
            <div style="font-size:17px;font-weight:700;">{{ summary.vehicle.name || summary.vehicle.brand }}</div>
            <div style="font-size:12px;color:#969799;margin-top:2px;">
              {{ summary.vehicle.brand }} {{ summary.vehicle.series }} {{ summary.vehicle.model_name }}
              · {{ summary.vehicle.plate_no || '未填车牌' }}
            </div>
          </template>
          <template #value>
            <div style="text-align:right;">
              <div style="font-size:20px;font-weight:700;">{{ summary.current_mileage || 0 }}</div>
              <div style="font-size:11px;color:#969799;">当前里程 km</div>
            </div>
          </template>
        </van-cell>
      </van-cell-group>

      <!-- 关键指标 -->
      <div style="display:flex;gap:8px;margin:12px 0;flex-wrap:wrap;">
        <div style="flex:1 1 96px;background:#fff;border-radius:10px;padding:12px;text-align:center;" @click="router.push(`/vehicle/${vehicleId}/maintenance`)">
          <div style="font-size:11px;color:#969799;">下次保养</div>
          <div style="font-size:15px;font-weight:600;margin-top:4px;" :style="{color: mtStatusColor}">
            {{ summary.next_maintenance.next_date || '暂无' }}
          </div>
          <div style="font-size:11px;color:#969799;">
            {{ summary.next_maintenance.next_mileage ? summary.next_maintenance.next_mileage + ' km' : '' }}
          </div>
          <van-tag :type="mtStatusType" size="mini" style="margin-top:4px;">{{ summary.next_maintenance.status }}</van-tag>
        </div>
        <div style="flex:1 1 96px;background:#fff;border-radius:10px;padding:12px;text-align:center;">
          <div style="font-size:11px;color:#969799;">平均油耗</div>
          <div style="font-size:15px;font-weight:600;margin-top:4px;">
            {{ summary.fuel.overall_l100 ?? '--' }}
          </div>
          <div style="font-size:11px;color:#969799;">L/100km</div>
        </div>
        <div style="flex:1 1 96px;background:#fff;border-radius:10px;padding:12px;text-align:center;">
          <div style="font-size:11px;color:#969799;">本年花费</div>
          <div style="font-size:15px;font-weight:600;margin-top:4px;">{{ summary.year_cost }}</div>
          <div style="font-size:11px;color:#969799;">元</div>
        </div>
      </div>

      <!-- 待办提醒 -->
      <div v-if="summary.pending_reminders.length" style="margin-bottom:12px;">
        <van-cell-group inset title="待办提醒">
          <van-cell v-for="r in summary.pending_reminders" :key="r.id" :title="r.title"
                    :label="r.message" is-link @click="router.push('/reminders')" />
        </van-cell-group>
      </div>

      <!-- 快捷操作 -->
      <div style="display:flex;gap:8px;margin-bottom:12px;flex-wrap:wrap;">
        <van-button size="small" round type="primary" plain icon="scan" style="flex:1 1 30%;"
          @click="router.push(`/vehicle/${vehicleId}/ocr`)">扫描录入</van-button>
        <van-button size="small" round type="primary" plain icon="records" style="flex:1 1 30%;"
          @click="router.push(`/vehicle/${vehicleId}/maintenance`)">保养维修</van-button>
        <van-button size="small" round type="primary" plain icon="fire-o" style="flex:1 1 30%;"
          @click="router.push(`/vehicle/${vehicleId}/refuels`)">加油记录</van-button>
      </div>

      <!-- 功能入口 -->
      <van-cell-group inset>
        <van-cell icon="edit" title="车辆档案" is-link @click="router.push(`/vehicle/${vehicleId}/edit`)" />
        <van-cell icon="shield-o" title="保险" is-link @click="router.push(`/vehicle/${vehicleId}/insurance`)" />
        <van-cell icon="certificate" title="年检" is-link @click="router.push(`/vehicle/${vehicleId}/inspections`)" />
        <van-cell icon="warning-o" title="违章记录" is-link @click="router.push(`/vehicle/${vehicleId}/violations`)" />
        <van-cell icon="guide-o" title="AI 智能分析" is-link @click="router.push(`/vehicle/${vehicleId}/ai`)" />
        <van-cell icon="bar-chart-o" title="统计报表" is-link @click="router.push(`/vehicle/${vehicleId}/stats`)" />
      </van-cell-group>

      <div style="margin-top:16px;display:flex;gap:8px;">
        <van-button size="small" plain type="danger" style="flex:1;" @click="onArchive">归档车辆</van-button>
        <van-button size="small" plain type="primary" style="flex:1;" @click="onExport">导出数据</van-button>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { showSuccessToast, showFailToast, showConfirmDialog } from 'vant'
import api from '../api'

const route = useRoute()
const router = useRouter()
const vehicleId = route.params.id
const summary = ref(null)
const loading = ref(true)

const mtStatusColor = computed(() => {
  const s = summary.value?.next_maintenance?.status
  if (s === '已到期') return '#ee0a24'
  if (s === '临期') return '#ff976a'
  return '#07c160'
})
const mtStatusType = computed(() => {
  const s = summary.value?.next_maintenance?.status
  if (s === '已到期') return 'danger'
  if (s === '临期') return 'warning'
  return 'success'
})

onMounted(load)

async function load() {
  try {
    summary.value = await api.get(`/vehicles/${vehicleId}/summary`)
  } catch (e) {
    showFailToast(e.message)
  } finally {
    loading.value = false
  }
}

async function onArchive() {
  try {
    await showConfirmDialog({ title: '归档车辆', message: '归档后车辆将从主页隐藏，历史数据保留。确定归档？' })
    await api.delete(`/vehicles/${vehicleId}`)
    showSuccessToast('已归档')
    router.push('/')
  } catch (e) {
    if (e !== 'cancel') showFailToast(e.message || '已取消')
  }
}

async function onExport() {
  try {
    const blob = await api.get('/export', { params: { vehicle_id: vehicleId }, responseType: 'blob' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `car_${vehicleId}_export.zip`
    a.click()
    URL.revokeObjectURL(url)
    showSuccessToast('已导出')
  } catch (e) {
    showFailToast(e.message)
  }
}
</script>
