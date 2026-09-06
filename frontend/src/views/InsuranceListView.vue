<template>
  <div>
    <van-skeleton title :row="3" v-if="loading" />
    <template v-else>
      <van-empty v-if="!records.length" description="还没有保单" />
      <van-cell-group inset v-for="p in records" :key="p.id" style="margin-top:10px;">
        <van-cell :title="p.company + ' · ' + p.policy_type"
                  :label="`${p.start_date || '?'} ~ ${p.end_date || '?'} · ¥${p.premium}`"
                  is-link @click="openEdit(p)">
          <template #value>
            <van-tag :type="expiring(p.end_date) ? 'danger' : 'default'">
              {{ expiring(p.end_date) ? '临期' : '有效' }}
            </van-tag>
          </template>
        </van-cell>
      </van-cell-group>
      <van-button round block type="primary" icon="plus" style="margin-top:16px;" @click="openAdd">添加保单</van-button>
    </template>

    <van-popup v-model:show="popup" position="bottom" round style="max-height:85vh;">
      <div style="padding:16px;">
        <div style="font-size:16px;font-weight:600;margin-bottom:12px;">{{ editingId ? '编辑保单' : '添加保单' }}</div>
        <van-form @submit="onSubmit">
          <van-cell-group inset>
            <van-field v-model="form.company" label="保险公司" placeholder="如：人保" :rules="[{ required: true, message: '必填' }]" />
            <van-field v-model="form.policy_no" label="保单号" placeholder="选填" />
            <van-field label="类型">
              <template #input>
                <van-radio-group v-model="form.policy_type" direction="horizontal">
                  <van-radio name="交强险">交强险</van-radio>
                  <van-radio name="商业险">商业险</van-radio>
                </van-radio-group>
              </template>
            </van-field>
            <van-field v-model.number="form.premium" type="number" label="保费" placeholder="元" />
            <van-field label="起保日期" :model-value="form.start_date" readonly is-link @click="pick('start')" />
            <van-field label="到期日期" :model-value="form.end_date" readonly is-link @click="pick('end')" />
            <van-field v-model="form.items_text" label="险种明细" type="textarea" rows="2"
                       placeholder="如：第三者责任险200万、车损险（逗号分隔）" />
            <van-field v-model="form.note" label="备注" placeholder="选填" />
          </van-cell-group>
          <div style="margin:16px;">
            <van-button round block type="primary" native-type="submit" :loading="saving">保 存</van-button>
            <van-button round block plain type="danger" style="margin-top:8px;" v-if="editingId" @click="onDelete">删 除</van-button>
          </div>
        </van-form>
      </div>
    </van-popup>
    <van-popup v-model:show="datePopup" position="bottom" round>
      <van-date-picker :min-date="new Date(2000, 0, 1)" :max-date="new Date(2040, 11, 31)"
                       title="选择日期" @confirm="onDateConfirm" @cancel="datePopup = false" />
    </van-popup>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { showSuccessToast, showFailToast } from 'vant'
import api from '../api'

const route = useRoute()
const vehicleId = route.params.id
const records = ref([])
const loading = ref(true)
const popup = ref(false)
const editingId = ref(null)
const saving = ref(false)
const picking = ref('start')

const form = ref(blank())

function blank() {
  return { vehicle_id: Number(vehicleId), company: '', policy_no: '', policy_type: '商业险',
    premium: 0, start_date: '', end_date: '', items_text: '', note: '' }
}

function expiring(d) {
  if (!d) return false
  const days = (new Date(d) - new Date()) / 86400000
  return days >= 0 && days <= 30
}

async function load() {
  try {
    records.value = await api.get('/insurance', { params: { vehicle_id: vehicleId } })
  } catch (e) { showFailToast(e.message) } finally { loading.value = false }
}
onMounted(load)

function openAdd() {
  editingId.value = null
  form.value = blank()
  popup.value = true
}
function openEdit(p) {
  editingId.value = p.id
  form.value = {
    vehicle_id: p.vehicle_id, company: p.company, policy_no: p.policy_no,
    policy_type: p.policy_type, premium: Number(p.premium) || 0,
    start_date: p.start_date || '', end_date: p.end_date || '',
    items_text: (() => { try { return JSON.parse(p.items_json || '[]').join('、') } catch { return '' } })(),
    note: p.note
  }
  popup.value = true
}

function pick(which) {
  picking.value = which
  datePopup.value = true
}

const datePopup = ref(false)

function onDateConfirm({ selectedValues }) {
  const v = selectedValues.join('-')
  if (picking.value === 'start') form.value.start_date = v
  else form.value.end_date = v
  datePopup.value = false
}

async function onSubmit() {
  saving.value = true
  try {
    const payload = {
      ...form.value,
      premium: form.value.premium || 0,
      start_date: form.value.start_date || null,
      end_date: form.value.end_date || null,
      items_json: JSON.stringify(form.value.items_text.split(/[、,，]/).map(s => s.trim()).filter(Boolean))
    }
    if (editingId.value) {
      await api.put(`/insurance/${editingId.value}`, payload)
      showSuccessToast('已保存')
    } else {
      await api.post('/insurance', payload)
      showSuccessToast('已添加')
    }
    popup.value = false
    load()
  } catch (e) { showFailToast(e.message) } finally { saving.value = false }
}

async function onDelete() {
  try {
    await api.delete(`/insurance/${editingId.value}`)
    showSuccessToast('已删除')
    popup.value = false
    load()
  } catch (e) { showFailToast(e.message) }
}
</script>
