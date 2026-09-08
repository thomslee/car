<template>
  <div>
    <van-skeleton title :row="5" v-if="loading" />

    <template v-else-if="rec">
      <!-- 头部 -->
      <van-cell-group inset>
        <van-cell>
          <template #title>
            <div style="font-size:17px;font-weight:700;">
              {{ rec.parking_address || '未填地址' }}
              <span v-if="rec.parking_no" style="color:#1989fa;margin-left:6px;font-size:14px;">{{ rec.parking_no }}</span>
            </div>
            <div style="font-size:12px;color:#969799;margin-top:2px;">
              {{ rec.charge_company || '未填收费单位' }}
            </div>
          </template>
          <template #value>
            <div style="text-align:right;">
              <div style="font-size:22px;font-weight:700;color:#ee0a24;">¥{{ rec.amount || 0 }}</div>
              <div style="font-size:11px;color:#969799;">总金额</div>
            </div>
          </template>
        </van-cell>
      </van-cell-group>

      <!-- 租期信息 -->
      <van-cell-group inset title="租期信息" style="margin-top:12px;">
        <van-cell title="起始时间" :value="rec.start_date || '未填'" />
        <van-cell title="租期" :value="(rec.duration_months || 0) + ' 个月'" />
        <van-cell title="结束时间" :value="rec.end_date || '未填'" />
      </van-cell-group>

      <!-- 基本信息 -->
      <van-cell-group inset title="基本信息" style="margin-top:12px;">
        <van-cell title="车位地址" :value="rec.parking_address || '未填'" />
        <van-cell title="车位号码" :value="rec.parking_no || '未填'" />
        <van-cell title="收费单位" :value="rec.charge_company || '未填'" />
      </van-cell-group>

      <!-- 备注 -->
      <van-cell-group v-if="rec.note" inset title="备注" style="margin-top:12px;">
        <van-cell :value="rec.note" />
      </van-cell-group>

      <!-- 底部操作 -->
      <div style="margin:24px 16px;display:flex;gap:12px;">
        <van-button round block plain type="primary" icon="edit" @click="router.push(`/vehicle/${vehicleId}/parking/${rec.id}/edit`)">编辑</van-button>
        <van-button round block plain type="danger" icon="delete" @click="onDelete">删除</van-button>
      </div>
    </template>
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
const parkingId = route.params.pid
const rec = ref(null)
const loading = ref(true)

onMounted(load)

async function load() {
  try {
    rec.value = await api.get(`/parking/${parkingId}`)
  } catch (e) {
    showFailToast(e.message)
  } finally {
    loading.value = false
  }
}

async function onDelete() {
  try {
    await showConfirmDialog({ title: '删除停车记录', message: '确定删除这条停车记录吗？删除后不可恢复。' })
    await api.delete(`/parking/${parkingId}`)
    showSuccessToast('已删除')
    router.push(`/vehicle/${vehicleId}/parking`)
  } catch (e) {
    if (e !== 'cancel') showFailToast(e.message || '已取消')
  }
}
</script>
