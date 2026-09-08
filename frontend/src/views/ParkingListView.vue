<template>
  <div>
    <van-skeleton title :row="3" v-if="loading" />

    <template v-else>
      <van-empty v-if="!records.length" description="还没有停车记录">
        <van-button round type="primary" icon="plus" @click="router.push(`/vehicle/${vehicleId}/parking/new`)">添加车位</van-button>
      </van-empty>

      <div v-for="p in records" :key="p.id" style="margin-bottom:10px;">
        <van-cell is-link center @click="router.push(`/vehicle/${vehicleId}/parking/${p.id}`)">
          <template #title>
            <div style="font-size:15px;font-weight:600;">
              {{ p.parking_address || '未填地址' }}
              <span v-if="p.parking_no" style="color:#1989fa;margin-left:6px;">{{ p.parking_no }}</span>
            </div>
            <div style="font-size:12px;color:#969799;margin-top:2px;">
              {{ p.start_date || '?' }} ~ {{ p.end_date || '?' }} · 租期{{ p.duration_months }}个月
              <span v-if="p.charge_company"> · {{ p.charge_company }}</span>
            </div>
          </template>
          <template #value>
            <div style="text-align:right;">
              <div style="font-size:16px;font-weight:600;color:#ee0a24;">¥{{ p.amount || 0 }}</div>
              <div style="font-size:11px;color:#969799;">总金额</div>
            </div>
          </template>
        </van-cell>
      </div>

      <van-button v-if="records.length" round block icon="plus" type="primary" style="margin-top:12px;"
        @click="router.push(`/vehicle/${vehicleId}/parking/new`)">添加车位</van-button>
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
const loading = ref(true)

onMounted(load)

async function load() {
  try {
    records.value = await api.get('/parking', { params: { vehicle_id: vehicleId } })
  } catch (e) {
    showFailToast(e.message)
  } finally {
    loading.value = false
  }
}
</script>
