<template>
  <div>
    <van-skeleton title :row="3" v-if="loading" />
    <template v-else>
      <van-empty v-if="!records.length" description="还没有年检记录" />
      <van-cell-group inset v-for="p in records" :key="p.id" style="margin-top:10px;">
        <van-cell :title="'检测：' + (p.inspected_at || '未填')"
                  :label="`有效期至 ${p.expire_at || '未填'} · ${p.station || ''} · ¥${p.cost}`"
                  is-link @click="openEdit(p)">
          <template #value>
            <van-tag :type="expiring(p.expire_at) ? 'danger' : 'success'">{{ p.result }}</van-tag>
          </template>
        </van-cell>
      </van-cell-group>
      <van-button round block type="primary" icon="plus" style="margin-top:16px;" @click="openAdd">添加年检</van-button>
    </template>

    <van-popup v-model:show="popup" position="bottom" round>
      <div style="padding:16px;">
        <div style="font-size:16px;font-weight:600;margin-bottom:12px;">{{ editingId ? '编辑年检' : '添加年检' }}</div>
        <van-form @submit="onSubmit">
          <van-cell-group inset>
            <van-field label="检测日期" :model-value="form.inspected_at" readonly is-link @click="pick('inspected_at')" />
            <van-field label="到期日期" :model-value="form.expire_at" readonly is-link @click="pick('expire_at')" />
            <van-field label="结果">
              <template #input>
                <van-radio-group v-model="form.result" direction="horizontal">
                  <van-radio name="合格">合格</van-radio>
                  <van-radio name="不合格">不合格</van-radio>
                </van-radio-group>
              </template>
            </van-field>
            <van-field v-model="form.station" label="检测站" placeholder="选填" />
            <van-field v-model.number="form.cost" type="number" label="费用" placeholder="元" />
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
const datePopup = ref(false)
const editingId = ref(null)
const saving = ref(false)
const picking = ref('inspected_at')

const form = ref({ vehicle_id: Number(vehicleId), inspected_at: '', expire_at: '', result: '合格', station: '', cost: 0, note: '' })

function expiring(d) {
  if (!d) return false
  const days = (new Date(d) - new Date()) / 86400000
  return days >= 0 && days <= 60
}

async function load() {
  try {
    records.value = await api.get('/inspections', { params: { vehicle_id: vehicleId } })
  } catch (e) { showFailToast(e.message) } finally { loading.value = false }
}
onMounted(load)

function openAdd() {
  editingId.value = null
  form.value = { vehicle_id: Number(vehicleId), inspected_at: '', expire_at: '', result: '合格', station: '', cost: 0, note: '' }
  popup.value = true
}
function openEdit(p) {
  editingId.value = p.id
  form.value = { ...p, cost: Number(p.cost) || 0, inspected_at: p.inspected_at || '', expire_at: p.expire_at || '' }
  popup.value = true
}
function pick(which) { picking.value = which; datePopup.value = true }
function onDateConfirm({ selectedValues }) {
  form.value[picking.value] = selectedValues.join('-')
  datePopup.value = false
}
async function onSubmit() {
  saving.value = true
  try {
    const payload = { ...form.value, inspected_at: form.value.inspected_at || null, expire_at: form.value.expire_at || null, cost: form.value.cost || 0 }
    if (editingId.value) { await api.put(`/inspections/${editingId.value}`, payload); showSuccessToast('已保存') }
    else { await api.post('/inspections', payload); showSuccessToast('已添加') }
    popup.value = false
    load()
  } catch (e) { showFailToast(e.message) } finally { saving.value = false }
}
async function onDelete() {
  try {
    await api.delete(`/inspections/${editingId.value}`)
    showSuccessToast('已删除')
    popup.value = false
    load()
  } catch (e) { showFailToast(e.message) }
}
</script>
