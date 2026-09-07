<template>
  <div>
    <van-skeleton title :row="5" v-if="loading" />

    <template v-else-if="vehicle">
      <!-- 头部 -->
      <van-cell-group inset>
        <van-cell>
          <template #title>
            <div style="font-size:17px;font-weight:700;">{{ vehicle.name || vehicle.brand }}</div>
            <div style="font-size:12px;color:#969799;margin-top:2px;">
              {{ vehicle.brand }} {{ vehicle.series }} {{ vehicle.model_name }}
              <span v-if="vehicle.model_year"> · {{ vehicle.model_year }}款</span>
            </div>
          </template>
          <template #value>
            <div style="text-align:right;">
              <div style="font-size:20px;font-weight:700;">{{ vehicle.current_mileage || 0 }}</div>
              <div style="font-size:11px;color:#969799;">当前里程 km</div>
            </div>
          </template>
        </van-cell>
      </van-cell-group>

      <!-- 基本信息 -->
      <van-cell-group inset title="基本信息" style="margin-top:12px;">
        <van-cell title="车牌号" :value="vehicle.plate_no || '未填'" />
        <van-cell title="车架号 VIN" :value="vehicle.vin || '未填'" />
        <van-cell title="发动机号" :value="vehicle.engine_no || '未填'" />
        <van-cell title="购车日期" :value="vehicle.purchase_date || '未填'" />
        <van-cell title="注册登记日期" :value="vehicle.registration_date || '未填'" />
        <van-cell title="年款" :value="vehicle.model_year || '未填'" />
      </van-cell-group>

      <!-- 里程与配置 -->
      <van-cell-group inset title="里程与配置" style="margin-top:12px;">
        <van-cell title="购车里程" :value="(vehicle.initial_mileage || 0) + ' km'" />
        <van-cell title="当前里程" :value="(vehicle.current_mileage || 0) + ' km'" />
        <van-cell title="燃料类型" :value="vehicle.fuel_type || '未填'" />
        <van-cell title="排量" :value="vehicle.displacement || '未填'" />
        <van-cell title="变速箱" :value="vehicle.transmission || '未填'" />
        <van-cell title="颜色" :value="vehicle.color || '未填'" />
      </van-cell-group>

      <!-- 保养周期 -->
      <van-cell-group inset title="保养周期" style="margin-top:12px;">
        <van-cell title="时间周期" :value="(vehicle.maint_interval_months || 12) + ' 个月'" />
        <van-cell title="里程周期" :value="(vehicle.maint_interval_km || 10000) + ' 公里'" />
        <div style="padding:8px 16px;font-size:12px;color:#969799;">
          时间或里程任一先到即需保养（或的关系）
        </div>
      </van-cell-group>

      <!-- 备注 -->
      <van-cell-group v-if="vehicle.notes" inset title="备注" style="margin-top:12px;">
        <van-cell :value="vehicle.notes" />
      </van-cell-group>

      <!-- 底部操作 -->
      <div style="margin:24px 16px;display:flex;gap:12px;">
        <van-button round block type="primary" icon="edit" @click="router.push(`/vehicle/${vehicleId}/edit`)">编辑车辆档案</van-button>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '../api'

const route = useRoute()
const router = useRouter()
const vehicleId = route.params.id
const loading = ref(true)
const vehicle = ref(null)

onMounted(load)

async function load() {
  try {
    vehicle.value = await api.get(`/vehicles/${vehicleId}`)
  } finally {
    loading.value = false
  }
}
</script>
