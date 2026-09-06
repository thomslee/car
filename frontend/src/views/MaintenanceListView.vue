<template>
  <div>
    <van-tabs v-model:active="typeTab" sticky @change="load">
      <van-tab title="全部" name="" />
      <van-tab title="保养" name="保养" />
      <van-tab title="维修" name="维修" />
      <van-tab title="年检" name="年检" />
    </van-tabs>

    <van-skeleton title :row="3" v-if="loading" />

    <template v-else>
      <van-empty v-if="!records.length" description="还没有保养维修记录">
        <van-button round type="primary" size="small" @click="router.push(`/vehicle/${vehicleId}/maintenance/new`)">录入第一条</van-button>
      </van-empty>

      <van-cell-group inset v-for="r in records" :key="r.id" style="margin-top:10px;">
        <van-cell is-link @click="router.push(`/vehicle/${vehicleId}/maintenance/${r.id}/edit`)">
          <template #title>
            <div style="display:flex;align-items:center;gap:6px;">
              <van-tag :type="typeColor(r.record_type)" size="medium">{{ r.record_type }}</van-tag>
              <span style="font-weight:600;">{{ r.title || r.category || '保养记录' }}</span>
            </div>
            <div style="font-size:12px;color:#969799;margin-top:4px;">
              {{ r.occurred_at }} · {{ r.mileage }}km · {{ r.shop_name || '未填门店' }}
            </div>
            <div v-if="r.items.length" style="font-size:12px;color:#969799;margin-top:2px;">
              {{ r.items.map(i => i.item_name).join('、') }}
            </div>
          </template>
          <template #value>
            <span style="font-weight:600;">¥{{ r.total_cost }}</span>
          </template>
        </van-cell>
      </van-cell-group>

      <van-button round block type="primary" icon="plus" style="margin-top:16px;"
        @click="router.push(`/vehicle/${vehicleId}/maintenance/new`)">录入记录</van-button>
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
const typeTab = ref('')
const loading = ref(true)

function typeColor(t) {
  return { 保养: 'primary', 维修: 'danger', 年检: 'warning', 其他: 'default' }[t] || 'default'
}

async function load() {
  loading.value = true
  try {
    records.value = await api.get('/maintenance', {
      params: { vehicle_id: vehicleId, record_type: typeTab.value }
    })
  } catch (e) {
    showFailToast(e.message)
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>
