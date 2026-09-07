<template>
  <div>
    <!-- 待办提醒 -->
    <div v-if="pending.length" style="margin-bottom:12px;">
      <van-notice-bar left-icon="bell" :scrollable="false" wrapable
        @click="router.push('/reminders')">
        <span v-for="(r, i) in pending.slice(0, 3)" :key="r.id">
          {{ i + 1 }}.{{ r.title }}（{{ r.target_date || '近期' }}）
        </span>
      </van-notice-bar>
    </div>

    <van-skeleton title :row="3" v-if="loading" />

    <template v-else>
      <van-empty v-if="!vehicles.length" description="还没有车辆，先添加第一辆车吧">
        <van-button round type="primary" @click="router.push('/vehicle/new')">添加车辆</van-button>
      </van-empty>

      <div v-for="v in vehicles" :key="v.id" style="margin-bottom:12px;">
        <van-cell is-link center @click="router.push(`/vehicle/${v.id}`)">
          <template #title>
            <div style="font-size:16px;font-weight:600;">
              {{ v.name || v.brand }}
              <van-tag v-if="!v.is_active" type="warning" size="mini" style="margin-left:6px;">已停用</van-tag>
            </div>
            <div style="font-size:12px;color:#969799;margin-top:2px;">
              {{ v.brand }} {{ v.series }} {{ v.model_name }} · {{ v.plate_no || '未填车牌' }}
            </div>
          </template>
          <template #value>
            <div style="text-align:right;">
              <div style="font-size:16px;font-weight:600;">{{ v.current_mileage || 0 }}<span style="font-size:11px;color:#969799;"> km</span></div>
              <div style="font-size:11px;color:#969799;">点击进入</div>
            </div>
          </template>
        </van-cell>
      </div>

      <div style="display:flex;align-items:center;justify-content:space-between;padding:0 4px;margin-top:8px;">
        <van-button v-if="vehicles.length" round block icon="plus" style="flex:1;margin-right:8px;"
          @click="router.push('/vehicle/new')">添加车辆</van-button>
        <van-cell :value="showArchived ? '隐藏已停用' : '显示已停用'" center style="flex:0 0 auto;padding:0 12px;">
          <template #right-icon>
            <van-switch :model-value="showArchived" size="20px" @update:model-value="toggleArchived" />
          </template>
        </van-cell>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { showFailToast } from 'vant'
import api from '../api'

const router = useRouter()
const vehicles = ref([])
const pending = ref([])
const loading = ref(true)
const showArchived = ref(false)

onMounted(load)

async function load() {
  try {
    vehicles.value = await api.get('/vehicles', { params: { include_inactive: showArchived.value } })
    const reminders = await api.get('/reminders', { params: { status: '待处理' } })
    pending.value = reminders
  } catch (e) {
    showFailToast(e.message)
  } finally {
    loading.value = false
  }
}

function toggleArchived(val) {
  showArchived.value = val
  loading.value = true
  load()
}
</script>
