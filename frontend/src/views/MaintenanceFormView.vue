<template>
  <van-form @submit="onSubmit">
    <van-cell-group inset title="记录信息">
      <van-field label="日期" :model-value="form.occurred_at" placeholder="选择日期" readonly is-link
                 @click="datePopup = true" :rules="[{ required: true, message: '请选择日期' }]" />
      <van-field v-model.number="form.mileage" type="number" label="里程" placeholder="km" />
      <van-field v-model="form.shop_name" label="门店" placeholder="如：沃尔沃4S店" />
      <van-field label="类型">
        <template #input>
          <van-radio-group v-model="form.record_type" direction="horizontal">
            <van-radio name="保养">保养</van-radio>
            <van-radio name="维修">维修</van-radio>
            <van-radio name="年检">年检</van-radio>
            <van-radio name="其他">其他</van-radio>
          </van-radio-group>
        </template>
      </van-field>
      <van-field v-model="form.title" label="标题" placeholder="如：4.5万公里保养" />
      <van-field v-model="form.category" label="类别" placeholder="如：基础保养/大保养" />
      <van-field v-model="form.description" label="描述" type="textarea" rows="2" autosize placeholder="选填" />
      <van-field v-model="form.invoice_no" label="发票号" placeholder="选填" />
      <van-field label="客户确认时间" :model-value="form.confirmed_at || ''" placeholder="选择日期和时间" readonly is-link
                 @click="openConfirmPicker" />
    </van-cell-group>

    <van-cell-group inset title="项目明细" style="margin-top:12px;">
      <div v-for="(it, idx) in form.items" :key="idx" style="padding:8px 16px;border-bottom:1px solid #f2f2f2;">
        <div style="display:flex;gap:6px;align-items:center;">
          <van-radio-group v-model="it.item_type" direction="horizontal" style="flex-shrink:0;">
            <van-radio name="材料">材料</van-radio>
            <van-radio name="工时">工时</van-radio>
          </van-radio-group>
          <van-button size="mini" type="danger" plain icon="delete-o" @click="removeItem(idx)" />
        </div>
        <van-field v-model="it.item_name" placeholder="项目名（如：机油及机油滤清器）" style="margin-top:4px;" />
        <div style="display:flex;gap:6px;margin-top:4px;">
          <van-field v-model.number="it.quantity" type="number" label="数量" placeholder="1" />
          <van-field v-model.number="it.unit_price" type="number" label="单价" placeholder="0" />
        </div>
        <div style="display:flex;gap:6px;margin-top:4px;">
          <van-field v-model.number="it.part_cost" type="number" label="材料费" placeholder="0" />
          <van-field v-model.number="it.labor_cost" type="number" label="工时费" placeholder="0" />
        </div>
        <div style="display:flex;gap:16px;margin-top:4px;padding:0 4px;">
          <van-cell title="原厂件" v-if="it.item_type === '材料'" style="flex:1;padding:0;">
            <template #right-icon><van-switch v-model="it.is_original" size="20" /></template>
          </van-cell>
          <van-cell title="定期保养项" style="flex:1;padding:0;">
            <template #right-icon><van-switch v-model="it.is_routine" size="20" /></template>
          </van-cell>
        </div>
      </div>
      <van-cell is-link @click="addItem">
        <van-icon name="plus" style="margin-right:4px;" />添加项目
      </van-cell>
    </van-cell-group>

    <van-cell-group inset title="折扣明细" style="margin-top:12px;">
      <div v-for="(d, idx) in form.discounts" :key="idx" style="padding:8px 16px;border-bottom:1px solid #f2f2f2;display:flex;gap:6px;align-items:center;">
        <van-field v-model="d.name" placeholder="折扣名称（如：基础保养券）" style="flex:1;" />
        <van-field v-model.number="d.amount" type="number" placeholder="金额" style="width:110px;" />
        <van-button size="mini" type="danger" plain icon="delete-o" @click="removeDiscount(idx)" />
      </div>
      <van-cell is-link @click="addDiscount">
        <van-icon name="plus" style="margin-right:4px;" />添加折扣
      </van-cell>
    </van-cell-group>

    <van-cell-group inset title="费用（手填）" style="margin-top:12px;">
      <van-field v-model.number="form.original_total_cost" type="number" label="原价合计" placeholder="0" />
      <van-field v-model.number="form.discount_amount" type="number" label="折扣金额" placeholder="0（正数）" />
      <van-field v-model.number="form.total_cost" type="number" label="总金额" placeholder="0" />
      <van-field v-model.number="form.paid_amount" type="number" label="已支付" placeholder="0" />
      <van-field label="是否质保内">
        <template #input>
          <van-switch v-model="form.warranty" size="20" />
        </template>
      </van-field>
      <van-field v-model="form.notes" label="备注" type="textarea" rows="2" autosize placeholder="选填" />
    </van-cell-group>

    <van-cell-group inset title="本次未做项目" style="margin-top:12px;">
      <van-field v-model="form.skipped_note" type="textarea" rows="3" autosize
                 placeholder="如：建议更换后刹车片，客户暂不处理；没有则留空" />
    </van-cell-group>

    <van-popup v-model:show="datePopup" position="bottom" round>
      <van-date-picker :min-date="new Date(2000, 0, 1)" :max-date="new Date(2035, 11, 31)"
                       title="选择日期" @confirm="onDateConfirm" @cancel="datePopup = false" />
    </van-popup>
    <van-popup v-model:show="confirmDatePopup" position="bottom" round>
      <van-date-picker :min-date="new Date(2000, 0, 1)" :max-date="new Date(2035, 11, 31)"
                       title="选择确认日期" @confirm="onConfirmDateConfirm" @cancel="confirmDatePopup = false" />
    </van-popup>
    <van-popup v-model:show="confirmTimePopup" position="bottom" round>
      <van-time-picker title="选择确认时间" @confirm="onConfirmTimeConfirm" @cancel="confirmTimePopup = false" />
    </van-popup>

    <div style="margin:24px 16px;">
      <van-button round block type="primary" native-type="submit" :loading="loading">保 存</van-button>
      <van-button v-if="recordId" round block plain type="danger" style="margin-top:8px;" icon="delete-o" @click="onDelete">删 除</van-button>
    </div>
  </van-form>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { showSuccessToast, showFailToast, showConfirmDialog } from 'vant'
import api from '../api'

const route = useRoute()
const router = useRouter()
const vehicleId = route.params.id
const recordId = route.params.mid
const loading = ref(false)
const datePopup = ref(false)
const confirmDatePopup = ref(false)
const confirmTimePopup = ref(false)
const _confirmDate = ref('')

const form = ref({
  vehicle_id: Number(vehicleId), occurred_at: '', mileage: null, shop_name: '',
  record_type: '保养', category: '', title: '', description: '',
  total_cost: 0, original_total_cost: 0, discount_amount: 0, paid_amount: 0,
  confirmed_at: null, skipped_note: '',
  invoice_no: '', warranty: false, notes: '', items: [], discounts: []
})

function addItem() {
  form.value.items.push({
    item_type: '材料', item_name: '', quantity: 1, unit_price: 0,
    part_cost: 0, labor_cost: 0, is_original: false, is_routine: true
  })
}
function removeItem(idx) {
  form.value.items.splice(idx, 1)
}
function addDiscount() {
  form.value.discounts.push({ name: '', amount: 0 })
}
function removeDiscount(idx) {
  form.value.discounts.splice(idx, 1)
}

function openConfirmPicker() {
  confirmDatePopup.value = true
}
function onConfirmDateConfirm({ selectedValues }) {
  _confirmDate.value = selectedValues.join('-')
  confirmDatePopup.value = false
  confirmTimePopup.value = true
}
function onConfirmTimeConfirm({ selectedValues }) {
  form.value.confirmed_at = `${_confirmDate.value} ${selectedValues.join(':')}`
  confirmTimePopup.value = false
}

onMounted(async () => {
  if (recordId) {
    try {
      const r = await api.get(`/maintenance/${recordId}`)
      form.value = {
        vehicle_id: r.vehicle_id, occurred_at: r.occurred_at, mileage: r.mileage,
        shop_name: r.shop_name, record_type: r.record_type, category: r.category,
        title: r.title, description: r.description,
        total_cost: Number(r.total_cost) || 0,
        original_total_cost: Number(r.original_total_cost) || 0,
        discount_amount: Number(r.discount_amount) || 0,
        paid_amount: Number(r.paid_amount) || 0,
        confirmed_at: r.confirmed_at ? String(r.confirmed_at).replace('T', ' ').replace(/\.\d+$/, '').slice(0, 16) : null,
        skipped_note: r.skipped_note || '',
        invoice_no: r.invoice_no, warranty: r.warranty, notes: r.notes,
        items: (r.items || []).map(i => ({
          item_type: i.item_type || '材料', item_name: i.item_name,
          quantity: Number(i.quantity) || 1, unit_price: Number(i.unit_price) || 0,
          part_cost: Number(i.part_cost) || 0, labor_cost: Number(i.labor_cost) || 0,
          is_original: !!i.is_original, is_routine: !!i.is_routine
        })),
        discounts: (r.discounts || []).map(d => ({
          name: d.name, amount: Number(d.amount) || 0
        }))
      }
    } catch (e) {
      showFailToast(e.message)
    }
  } else {
    const today = new Date()
    form.value.occurred_at = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`
  }
})

function onDateConfirm({ selectedValues }) {
  form.value.occurred_at = selectedValues.join('-')
  datePopup.value = false
}

async function onSubmit() {
  loading.value = true
  try {
    const payload = {
      ...form.value,
      mileage: form.value.mileage || 0,
      items: form.value.items.filter(i => i.item_name),
      discounts: form.value.discounts.filter(d => d.name)
    }
    if (recordId) {
      await api.put(`/maintenance/${recordId}`, payload)
      showSuccessToast('已保存')
    } else {
      await api.post('/maintenance', payload)
      showSuccessToast('已录入')
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
    await showConfirmDialog({ title: '删除记录', message: '删除后不可恢复，确定删除这条记录？' })
    await api.delete(`/maintenance/${recordId}`)
    showSuccessToast('已删除')
    router.back()
  } catch (e) {
    if (e !== 'cancel') showFailToast(e.message || '已取消')
  }
}
</script>
