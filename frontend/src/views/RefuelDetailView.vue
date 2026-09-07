<template>
  <div>
    <van-skeleton v-if="loading" title :row="6" />
    <template v-else-if="rec">
      <!-- 头部 -->
      <van-cell-group inset>
        <van-cell>
          <template #title>
            <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;">
              <van-tag type="primary" size="medium">{{ rec.fuel_grade || '95' }}号</van-tag>
              <span style="font-size:16px;font-weight:700;">{{ rec.station || '加油记录' }}</span>
            </div>
            <div style="font-size:12px;color:#969799;margin-top:4px;">{{ formatDateTime(rec.refueled_at) }}</div>
          </template>
          <template #value>
            <div style="text-align:right;">
              <div style="font-size:18px;font-weight:700;">¥{{ rec.paid_amount != null && rec.paid_amount > 0 ? rec.paid_amount : rec.total_cost }}</div>
              <div style="font-size:11px;color:#969799;">实付金额</div>
            </div>
          </template>
        </van-cell>
      </van-cell-group>

      <!-- 基本信息 -->
      <van-cell-group inset title="基本信息" style="margin-top:12px;">
        <van-cell title="加油时间" :value="formatDateTime(rec.refueled_at)" />
        <van-cell title="里程" :value="rec.mileage ? rec.mileage + ' km' : '未填'" />
        <van-cell title="油标" :value="(rec.fuel_grade || '95') + '号'" />
        <van-cell title="油品" :value="rec.fuel_type || '汽油'" />
        <van-cell title="是否加满" :value="rec.is_full ? '是' : '否'" />
      </van-cell-group>

      <!-- 费用信息 -->
      <van-cell-group inset title="费用信息" style="margin-top:12px;">
        <van-cell title="单价" :value="'¥' + rec.unit_price + '/L'" />
        <van-cell title="加油量" :value="rec.fuel_amount_l + ' L'" />
        <van-cell title="应付金额" :value="'¥' + rec.total_cost" />
        <van-cell title="实付金额">
          <template #value><span style="color:#ee0a24;font-weight:600;">¥{{ rec.paid_amount != null && rec.paid_amount > 0 ? rec.paid_amount : rec.total_cost }}</span></template>
        </van-cell>
      </van-cell-group>

      <!-- 备注 -->
      <van-cell-group v-if="rec.note" inset title="备注" style="margin-top:12px;">
        <div style="padding:12px 16px;font-size:13px;color:#323233;white-space:pre-wrap;">{{ rec.note }}</div>
      </van-cell-group>

      <!-- 操作 -->
      <div style="margin:20px 16px;display:flex;gap:8px;">
        <van-button round block type="primary" icon="edit" style="flex:1;" @click="onEdit">编 辑</van-button>
        <van-button round block plain type="danger" icon="delete-o" style="flex:1;" @click="onDelete">删 除</van-button>
      </div>
    </template>
    <van-empty v-else description="记录不存在或已删除" />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { showSuccessToast, showFailToast, showConfirmDialog } from 'vant'
import api from '../api'

const route = useRoute()
const router = useRouter()
const vehicleId = route.params.id
const rid = route.params.rid
const rec = ref(null)
const loading = ref(true)

function formatDateTime(v) {
  if (!v) return ''
  return String(v).replace('T', ' ').replace(/\.\d+$/, '').slice(0, 16)
}

onMounted(async () => {
  try {
    const list = await api.get('/refuels', { params: { vehicle_id: vehicleId } })
    rec.value = list.find(r => r.id === Number(rid)) || null
  } catch (e) {
    showFailToast(e.message)
  } finally {
    loading.value = false
  }
})

function onEdit() {
  router.push(`/vehicle/${vehicleId}/refuels/new?id=${rid}`)
}

async function onDelete() {
  try {
    await showConfirmDialog({ title: '删除记录', message: '确定删除这条加油记录？' })
    await api.delete(`/refuels/${rid}`)
    showSuccessToast('已删除')
    router.back()
  } catch (e) {
    if (e !== 'cancel') showFailToast(e.message || '已取消')
  }
}
</script>
