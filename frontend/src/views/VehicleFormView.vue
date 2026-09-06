<template>
  <van-form @submit="onSubmit">
    <van-cell-group inset title="基本信息">
      <van-field v-model="form.name" label="爱车昵称" placeholder="如：大白（选填）" />
      <van-field v-model="form.brand" label="品牌" placeholder="沃尔沃" />
      <van-field v-model="form.series" label="车系" placeholder="如：XC60" />
      <van-field v-model="form.model_name" label="车型" placeholder="如：XC60 B5" />
      <van-field v-model="form.model_year" label="年款" placeholder="如：2022" />
      <van-field v-model="form.plate_no" label="车牌号" placeholder="如：京A12345" />
      <van-field v-model="form.vin" label="车架号 VIN" placeholder="17位车架号" />
      <van-field v-model="form.engine_no" label="发动机号" placeholder="选填" />
      <van-field label="购车日期" :model-value="form.purchase_date" placeholder="选择日期"
                 readonly is-link @click="datePickerVisible = true" />
    </van-cell-group>
    <van-popup v-model:show="datePickerVisible" position="bottom" round>
      <van-date-picker :min-date="new Date(1990, 0, 1)" :max-date="new Date(2035, 11, 31)"
                       title="选择购车日期" @confirm="onDateConfirm" @cancel="datePickerVisible = false" />
    </van-popup>

    <van-cell-group inset title="里程与配置" style="margin-top:12px;">
      <van-field v-model.number="form.initial_mileage" type="number" label="购车里程" placeholder="km" />
      <van-field v-model.number="form.current_mileage" type="number" label="当前里程" placeholder="km" />
      <van-field label="燃料类型">
        <template #input>
          <van-radio-group v-model="form.fuel_type" direction="horizontal">
            <van-radio name="汽油">汽油</van-radio>
            <van-radio name="柴油">柴油</van-radio>
            <van-radio name="插混">插混</van-radio>
            <van-radio name="纯电">纯电</van-radio>
          </van-radio-group>
        </template>
      </van-field>
      <van-field v-model="form.displacement" label="排量" placeholder="如：2.0T" />
      <van-field v-model="form.transmission" label="变速箱" placeholder="如：自动" />
      <van-field v-model="form.color" label="颜色" placeholder="选填" />
      <van-field v-model="form.notes" label="备注" type="textarea" rows="2" autosize placeholder="选填" />
    </van-cell-group>

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
const loading = ref(false)
const datePickerVisible = ref(false)

const form = ref({
  name: '', brand: '沃尔沃', series: '', model_name: '', model_year: '',
  plate_no: '', vin: '', engine_no: '', purchase_date: '',
  initial_mileage: 0, current_mileage: 0, fuel_type: '汽油',
  displacement: '', transmission: '', color: '', notes: ''
})

onMounted(async () => {
  if (vehicleId) {
    try {
      const v = await api.get(`/vehicles/${vehicleId}`)
      form.value = { ...form.value, ...v, purchase_date: v.purchase_date || '' }
    } catch (e) {
      showFailToast(e.message)
    }
  }
})

function onDateConfirm({ selectedValues }) {
  form.value.purchase_date = selectedValues.join('-')
  datePickerVisible.value = false
}

async function onSubmit() {
  loading.value = true
  try {
    const payload = { ...form.value, purchase_date: form.value.purchase_date || null }
    if (vehicleId) {
      await api.put(`/vehicles/${vehicleId}`, payload)
      showSuccessToast('已保存')
    } else {
      await api.post('/vehicles', payload)
      showSuccessToast('车辆已添加')
    }
    router.back()
  } catch (e) {
    showFailToast(e.message)
  } finally {
    loading.value = false
  }
}
</script>
