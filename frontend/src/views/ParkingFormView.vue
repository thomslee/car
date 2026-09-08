<template>
  <van-form @submit="onSubmit">
    <van-cell-group inset title="车位信息">
      <van-field v-model="form.parking_address" label="车位地址" placeholder="如：北京市朝阳区XX小区B1层" />
      <van-field v-model="form.parking_no" label="车位号码" placeholder="如：B1-088" />
      <van-field v-model="form.charge_company" label="收费单位" placeholder="如：XX物业管理有限公司" />
    </van-cell-group>

    <van-cell-group inset title="租期信息" style="margin-top:12px;">
      <van-field label="起始时间" :model-value="form.start_date" placeholder="选择日期"
                 readonly is-link @click="datePickerVisible = true" />
      <van-field v-model.number="form.duration_months" type="number" label="租期" placeholder="月" />
      <van-field label="结束时间" :model-value="calcEndDate" readonly>
        <template #input>
          <span :style="{ color: calcEndDate ? '#323233' : '#c8c9cc' }">{{ calcEndDate || '自动计算' }}</span>
        </template>
      </van-field>
      <div style="padding:8px 16px;font-size:12px;color:#969799;">
        结束时间 = 起始时间 + 租期（月），自动计算
      </div>
    </van-cell-group>

    <van-popup v-model:show="datePickerVisible" position="bottom" round>
      <van-date-picker :min-date="new Date(2000, 0, 1)" :max-date="new Date(2035, 11, 31)"
                       title="选择起始时间" @confirm="onDateConfirm" @cancel="datePickerVisible = false" />
    </van-popup>

    <van-cell-group inset title="费用" style="margin-top:12px;">
      <van-field v-model.number="form.amount" type="number" label="总金额" placeholder="元（精确到元）">
        <template #button>
          <span style="color:#969799;">元</span>
        </template>
      </van-field>
    </van-cell-group>

    <van-cell-group inset title="备注" style="margin-top:12px;">
      <van-field v-model="form.note" type="textarea" rows="2" autosize placeholder="选填" />
    </van-cell-group>

    <div style="margin:24px 16px;">
      <van-button round block type="primary" native-type="submit" :loading="loading">保 存</van-button>
    </div>
  </van-form>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { showSuccessToast, showFailToast } from 'vant'
import api from '../api'

const route = useRoute()
const router = useRouter()
const vehicleId = route.params.id
const parkingId = route.params.pid
const isEdit = !!parkingId
const loading = ref(false)
const datePickerVisible = ref(false)

const form = ref({
  vehicle_id: Number(vehicleId),
  parking_address: '',
  parking_no: '',
  charge_company: '',
  start_date: '',
  duration_months: 12,
  amount: 0,
  note: '',
})

const calcEndDate = computed(() => {
  if (!form.value.start_date || !form.value.duration_months) return ''
  const d = new Date(form.value.start_date)
  const months = Number(form.value.duration_months)
  const day = d.getDate()
  d.setMonth(d.getMonth() + months)
  // 月末溢出处理
  if (d.getDate() < day) {
    d.setDate(0)
  }
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const dd = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${dd}`
})

onMounted(async () => {
  if (isEdit) {
    try {
      const p = await api.get(`/parking/${parkingId}`)
      form.value = {
        vehicle_id: p.vehicle_id,
        parking_address: p.parking_address || '',
        parking_no: p.parking_no || '',
        charge_company: p.charge_company || '',
        start_date: p.start_date || '',
        duration_months: p.duration_months || 12,
        amount: p.amount || 0,
        note: p.note || '',
      }
    } catch (e) {
      showFailToast(e.message)
    }
  }
})

function onDateConfirm({ selectedValues }) {
  form.value.start_date = selectedValues.join('-')
  datePickerVisible.value = false
}

async function onSubmit() {
  try {
    loading.value = true
    const payload = { ...form.value, start_date: form.value.start_date || null }
    if (isEdit) {
      await api.put(`/parking/${parkingId}`, payload)
      showSuccessToast('已保存')
      router.back()
    } else {
      await api.post('/parking', payload)
      showSuccessToast('已添加')
      router.push(`/vehicle/${vehicleId}/parking`)
    }
  } catch (e) {
    showFailToast(e.message)
  } finally {
    loading.value = false
  }
}
</script>
