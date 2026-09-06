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

      <van-cell-group inset v-for="r in records" :key="r.id" style="margin-top:10px;">
        <van-cell :title="r.refueled_at + ' · ' + (r.station || '未填加油站')"
                  :label="`${r.mileage}km · ${r.fuel_amount_l}L × ¥${r.unit_price}`"
                  is-link @click="router.push(`/vehicle/${vehicleId}/refuels/new?id=${r.id}`)">
          <template #value>
            <span style="font-weight:600;">¥{{ r.total_cost }}</span>
          </template>
        </van-cell>
      </van-cell-group>

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
