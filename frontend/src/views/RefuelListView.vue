<template>
  <div>
    <!-- 油耗概览 -->
    <div style="display:flex;gap:8px;margin-bottom:12px;flex-wrap:wrap;" v-if="stats">
      <div style="flex:1 1 96px;background:#fff;border-radius:10px;padding:12px;text-align:center;">
        <div style="font-size:11px;color:#969799;">平均油耗</div>
        <div style="font-size:16px;font-weight:600;margin-top:4px;">{{ stats.overall_l100 ?? '--' }}</div>
        <div style="font-size:11px;color:#969799;">L/100km</div>
      </div>
      <div style="flex:1 1 96px;background:#fff;border-radius:10px;padding:12px;text-align:center;">
        <div style="font-size:11px;color:#969799;">加油总额</div>
        <div style="font-size:16px;font-weight:600;margin-top:4px;">{{ stats.total_cost }}</div>
        <div style="font-size:11px;color:#969799;">元 · {{ stats.record_count }} 次</div>
      </div>
    </div>

    <van-skeleton title :row="3" v-if="loading" />
    <template v-else>
      <van-empty v-if="!records.length" description="还没有加油记录">
        <van-button round type="primary" size="small" @click="router.push(`/vehicle/${vehicleId}/refuels/new`)">记一笔</van-button>
      </van-empty>

      <!-- 加油记录卡片（参照订单列表样式） -->
      <div v-for="r in records" :key="r.id"
           style="background:#fff;border-radius:10px;padding:14px 16px;margin-top:10px;"
           @click="router.push(`/vehicle/${vehicleId}/refuels/${r.id}`)">
        <!-- 第一行：加油站名称 -->
        <div style="font-size:16px;font-weight:700;color:#1a1a1a;">{{ r.station || '未填加油站' }}</div>
        <!-- 第二行：油标 + 实付金额 -->
        <div style="display:flex;justify-content:space-between;align-items:center;margin-top:6px;">
          <span style="font-size:14px;color:#646566;">{{ r.fuel_grade || '95' }}号{{ r.fuel_type || '汽油' }}</span>
          <span style="font-size:18px;font-weight:700;color:#1a1a1a;">实付 ¥{{ r.paid_amount != null && r.paid_amount > 0 ? r.paid_amount : r.total_cost }}</span>
        </div>
        <!-- 第三行：单价 · 数量 · 应付 -->
        <div style="font-size:12px;color:#969799;margin-top:4px;">
          单价 ¥{{ r.unit_price }}/L · {{ r.fuel_amount_l }}L · 应付 ¥{{ r.total_cost }}
        </div>
        <!-- 第四行：日期时间 -->
        <div style="font-size:12px;color:#969799;margin-top:4px;">{{ formatDateTime(r.refueled_at) }}</div>
      </div>

      <van-button round block type="primary" icon="plus" style="margin-top:16px;"
        @click="router.push(`/vehicle/${vehicleId}/refuels/new`)">记一笔加油</van-button>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { showFailToast } from 'vant'
import api from '../api'

const route = useRoute()
const router = useRouter()
const vehicleId = route.params.id
const records = ref([])
const stats = ref(null)
const loading = ref(true)

function formatDateTime(v) {
  if (!v) return ''
  return String(v).replace('T', ' ').replace(/\.\d+$/, '').slice(0, 16)
}

onMounted(async () => {
  try {
    records.value = await api.get('/refuels', { params: { vehicle_id: vehicleId } })
    stats.value = await api.get(`/refuels/${vehicleId}/stats`)
  } catch (e) {
    showFailToast(e.message)
  } finally {
    loading.value = false
  }
})
</script>
