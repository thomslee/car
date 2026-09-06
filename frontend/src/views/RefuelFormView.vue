<template>
  <van-form @submit="onSubmit">
    <van-cell-group inset>
      <van-field label="加油日期" :model-value="form.refueled_at" placeholder="选择日期" readonly is-link
                 @click="datePopup = true" :rules="[{ required: true, message: '请选择日期' }]" />
      <van-field v-model.number="form.mileage" type="number" label="里程" placeholder="当前表显里程 km" />
      <van-field v-model.number="form.fuel_amount_l" type="number" label="加油量" placeholder="升" />
      <van-field v-model.number="form.unit_price" type="number" label="单价" placeholder="元/升" />
      <van-field v-model.number="form.total_cost" type="number" label="金额" placeholder="元" />
      <van-field v-model="form.station" label="加油站" placeholder="如：中石化" />
      <van-field label="油品">
        <template #input>
          <van-radio-group v-model="form.fuel_type" direction="horizontal">
            <van-radio name="汽油">汽油</van-radio>
            <van-radio name="柴油">柴油</van-radio>
            <van-radio name="其他">其他</van-radio>
          </van-radio-group>
        </template>
      </van-field>
      <van-cell title="本次是否加满（用于油耗计算）">
        <template #right-icon>
          <van-switch v-model="form.is_full" size="20" />
        </template>
      </van-cell>
      <van-field v-model="form.note" label="备注" placeholder="选填" />
    </van-cell-group>

    <van-popup v-model:show="datePopup" position="bottom" round>
      <van-date-picker :min-date="new Date(2000, 0, 1)" :max-date="new Date(2035, 11, 31)"
                       title="选择日期" @confirm="onDateConfirm" @cancel="datePopup = false" />
    </van-popup>

    <div style="margin:24px 16px;">
      <van-button round block type="primary" native-type="submit" :loading="loading">保 存</van-button>
    </div>
  </van-form>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { showSuccessToast, showFailToast } from 'vant'
import api from '../api'

const route = useRoute()
const router = useRouter()
const vehicleId = route.params.id
const recordId = route.query.id
const loading = ref(false)
const datePopup = ref(false)

const form = ref({
  vehicle_id: Number(vehicleId), refueled_at: '', mileage: null,
  fuel_amount_l: null, unit_price: null, total_cost: null,
  station: '', fuel_type: '汽油', is_full: true, note: ''
})

onMounted(async () => {
  const today = new Date()
  form.value.refueled_at = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`
  if (recordId) {
    const list = await api.get('/refuels', { params: { vehicle_id: vehicleId } })
    const r = list.find(x => x.id === Number(recordId))
    if (r) {
      form.value = {
        vehicle_id: r.vehicle_id, refueled_at: r.refueled_at, mileage: r.mileage,
        fuel_amount_l: Number(r.fuel_amount_l), unit_price: Number(r.unit_price),
        total_cost: Number(r.total_cost), station: r.station, fuel_type: r.fuel_type,
        is_full: !!r.is_full, note: r.note
      }
    }
  }
})

function onDateConfirm({ selectedValues }) {
  form.value.refueled_at = selectedValues.join('-')
  datePopup.value = false
}

async function onSubmit() {
  loading.value = true
  try {
    const payload = {
      ...form.value,
      mileage: form.value.mileage || 0,
      fuel_amount_l: form.value.fuel_amount_l || 0,
      unit_price: form.value.unit_price || 0,
      total_cost: form.value.total_cost || 0
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
</script>
