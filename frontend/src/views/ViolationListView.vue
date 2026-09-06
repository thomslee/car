<template>
  <div>
    <van-tabs v-model:active="statusTab" sticky @change="load">
      <van-tab title="全部" name="" />
      <van-tab title="未处理" name="未处理" />
      <van-tab title="已处理" name="已处理" />
    </van-tabs>

    <van-skeleton title :row="3" v-if="loading" />
    <template v-else>
      <van-empty v-if="!records.length" description="还没有违章记录" />
      <van-cell-group inset v-for="p in records" :key="p.id" style="margin-top:10px;">
        <van-cell :title="(p.occurred_at || '未填日期') + ' · ' + (p.location || '未填地点')"
                  :label="`${p.behavior || ''} · 扣${p.points}分 · ¥${p.fine}`"
                  is-link @click="openEdit(p)">
          <template #value>
            <van-tag :type="p.status === '未处理' ? 'danger' : 'success'">{{ p.status }}</van-tag>
          </template>
        </van-cell>
      </van-cell-group>
      <van-button round block type="primary" icon="plus" style="margin-top:16px;" @click="openAdd">添加违章</van-button>
    </template>

    <van-popup v-model:show="popup" position="bottom" round>
      <div style="padding:16px;">
        <div style="font-size:16px;font-weight:600;margin-bottom:12px;">{{ editingId ? '编辑违章' : '添加违章' }}</div>
        <van-form @submit="onSubmit">
          <van-cell-group inset>
            <van-field label="违章日期" :model-value="form.occurred_at" readonly is-link @click="pick('occurred_at')" />
            <van-field v-model="form.location" label="违章地点" placeholder="如：北京三环" />
            <van-field v-model="form.behavior" label="违章行为" placeholder="如：违反禁止标线指示" />
            <van-field v-model.number="form.points" type="number" label="扣分" placeholder="0" />
            <van-field v-model.number="form.fine" type="number" label="罚款" placeholder="元" />
            <van-field label="处理状态">
              <template #input>
                <van-radio-group v-model="form.status" direction="horizontal">
                  <van-radio name="未处理">未处理</van-radio>
                  <van-radio name="已处理">已处理</van-radio>
                </van-radio-group>
              </template>
            </van-field>
            <van-field label="处理日期" :model-value="form.handle_date" readonly is-link @click="pick('handle_date')" />
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
const statusTab = ref('')
const picking = ref('occurred_at')

const form = ref(blank())
function blank() {
  return { vehicle_id: Number(vehicleId), occurred_at: '', location: '', behavior: '', points: 0, fine: 0, status: '未处理', handle_date: '', note: '' }
}

async function load() {
  loading.value = true
  try {
    records.value = await api.get('/violations', { params: { vehicle_id: vehicleId, status: statusTab.value } })
  } catch (e) { showFailToast(e.message) } finally { loading.value = false }
}
onMounted(load)

function openAdd() { editingId.value = null; form.value = blank(); popup.value = true }
function openEdit(p) {
  editingId.value = p.id
  form.value = { ...p, points: Number(p.points) || 0, fine: Number(p.fine) || 0, occurred_at: p.occurred_at || '', handle_date: p.handle_date || '' }
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
    const payload = { ...form.value, occurred_at: form.value.occurred_at || null, handle_date: form.value.handle_date || null, points: form.value.points || 0, fine: form.value.fine || 0 }
    if (editingId.value) { await api.put(`/violations/${editingId.value}`, payload); showSuccessToast('已保存') }
    else { await api.post('/violations', payload); showSuccessToast('已添加') }
    popup.value = false
    load()
  } catch (e) { showFailToast(e.message) } finally { saving.value = false }
}
async function onDelete() {
  try {
    await api.delete(`/violations/${editingId.value}`)
    showSuccessToast('已删除')
    popup.value = false
    load()
  } catch (e) { showFailToast(e.message) }
}
</script>
