<template>
  <van-form @submit="onSubmit">
    <van-cell-group inset title="记录信息">
      <van-field label="加油时间" :model-value="form.refueled_at" placeholder="选择日期时间" readonly is-link
                 @click="datePopup = true" :rules="[{ required: true, message: '请选择加油时间' }]" />
      <van-field v-model.number="form.mileage" type="number" label="里程" placeholder="当前表显里程 km（选填）" />
      <van-field label="油标">
        <template #input>
          <van-radio-group v-model="form.fuel_grade" direction="horizontal">
            <van-radio name="92">92号</van-radio>
            <van-radio name="95">95号</van-radio>
            <van-radio name="98">98号</van-radio>
          </van-radio-group>
        </template>
      </van-field>
      <van-field v-model="form.station" label="加油站" placeholder="如：中国石化安宁庄加油站" />
    </van-cell-group>

    <van-cell-group inset title="加油量与费用" style="margin-top:12px;">
      <van-field v-model.number="form.fuel_amount_l" type="number" label="加油量" placeholder="升" />
      <van-field v-model.number="form.unit_price" type="number" label="单价" placeholder="元/升" />
      <van-field v-model.number="form.total_cost" type="number" label="应付金额" placeholder="元（优惠前）" />
      <van-field v-model.number="form.paid_amount" type="number" label="实付金额" placeholder="元（优惠后，默认=应付）" />
    </van-cell-group>

    <van-cell-group inset title="其他" style="margin-top:12px;">
      <van-cell title="本次是否加满（用于油耗计算）">
        <template #right-icon>
          <van-switch v-model="form.is_full" size="20" />
        </template>
      </van-cell>
      <van-field v-model="form.note" label="备注" placeholder="选填" />
    </van-cell-group>

    <!-- 日期选择 -->
    <van-popup v-model:show="datePopup" position="bottom" round>
      <van-date-picker :min-date="new Date(2000, 0, 1)" :max-date="new Date(2035, 11, 31)"
                       title="选择日期" @confirm="onDateConfirm" @cancel="datePopup = false" />
    </van-popup>
    <!-- 时间选择 -->
    <van-popup v-model:show="timePopup" position="bottom" round>
      <van-time-picker title="选择时间" :columns-type="['hour','minute']"
                        @confirm="onTimeConfirm" @cancel="timePopup = false" />
    </van-popup>

    <div style="margin:24px 16px;">
      <van-button round block type="primary" native-type="submit" :loading="loading">保 存</van-button>
      <van-button v-if="recordId" round block plain type="danger" style="margin-top:8px;" icon="delete-o" @click="onDelete">删 除</van-button>
    </div>
  </van-form>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { showSuccessToast, showFailToast, showConfirmDialog } from 'vant'
import api from '../api'

const route = useRoute()
const router = useRouter()
const vehicleId = route.params.id
const recordId = route.query.id
const loading = ref(false)
const datePopup = ref(false)
const timePopup = ref(false)
const pendingDate = ref('')

const form = ref({
  vehicle_id: Number(vehicleId), refueled_at: '', mileage: null,
  fuel_amount_l: null, unit_price: null, total_cost: null, paid_amount: null,
  fuel_grade: '95', station: '', fuel_type: '汽油', is_full: true, note: ''
})

// 实付金额默认跟随应付金额（用户未手动改过时）
watch(() => form.value.total_cost, (newVal, oldVal) => {
  if (form.value.paid_amount == null || Number(form.value.paid_amount) === 0 || Number(form.value.paid_amount) === Number(oldVal)) {
    form.value.paid_amount = newVal
  }
})

onMounted(async () => {
  const now = new Date()
  form.value.refueled_at = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')} ${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`
  if (recordId) {
    const list = await api.get('/refuels', { params: { vehicle_id: vehicleId } })
    const r = list.find(x => x.id === Number(recordId))
    if (r) {
      form.value = {
        vehicle_id: r.vehicle_id,
        refueled_at: r.refueled_at ? String(r.refueled_at).replace('T', ' ').replace(/\.\d+$/, '').slice(0, 16) : '',
        mileage: r.mileage,
        fuel_amount_l: Number(r.fuel_amount_l),
        unit_price: Number(r.unit_price),
        total_cost: Number(r.total_cost),
        paid_amount: r.paid_amount != null && r.paid_amount > 0 ? Number(r.paid_amount) : Number(r.total_cost),
        fuel_grade: r.fuel_grade || '95',
        station: r.station,
        fuel_type: r.fuel_type || '汽油',
        is_full: !!r.is_full,
        note: r.note
      }
    }
  }
})

function onDateConfirm({ selectedValues }) {
  pendingDate.value = selectedValues.join('-')
  datePopup.value = false
  timePopup.value = true
}

function onTimeConfirm({ selectedValues }) {
  form.value.refueled_at = `${pendingDate.value} ${selectedValues.join(':')}`
  timePopup.value = false
}

async function onSubmit() {
  loading.value = true
  try {
    const payload = {
      ...form.value,
      mileage: form.value.mileage || null,
      fuel_amount_l: form.value.fuel_amount_l || 0,
      unit_price: form.value.unit_price || 0,
      total_cost: form.value.total_cost || 0,
      paid_amount: form.value.paid_amount != null ? form.value.paid_amount : (form.value.total_cost || 0)
    }
    if (recordId) {
      await api.put(`/refuels/${recordId}`, payload)
      showSuccessToast('已保存')
    } else {
      await api.post('/refuels', payload)
      showSuccessToast('已记录')
    }
    router.back()
  } catch (e) {
    showFailToast(e.message)
  } finally {
    loading.value = false
  }
}

async function onDelete() {
  try {
    await showConfirmDialog({ title: '删除记录', message: '删除后不可恢复，确定删除这笔加油记录？' })
    await api.delete(`/refuels/${recordId}`)
    showSuccessToast('已删除')
    router.back()
  } catch (e) {
    if (e !== 'cancel') showFailToast(e.message || '已取消')
  }
}
</script>
