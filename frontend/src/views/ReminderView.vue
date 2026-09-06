<template>
  <div>
    <van-tabs v-model:active="tab" sticky @change="load">
      <van-tab title="待处理" name="待处理" />
      <van-tab title="已完成" name="已完成" />
      <van-tab title="已忽略" name="已忽略" />
    </van-tabs>

    <van-skeleton title :row="3" v-if="loading" />
    <template v-else>
      <van-empty v-if="!records.length" description="暂无提醒" />
      <van-cell-group inset v-for="r in records" :key="r.id" style="margin-top:10px;">
        <van-cell :title="r.title"
                  :label="`${r.remind_type} · ${r.target_date || '未设日期'} · ${r.message}`">
          <template #value>
            <van-button v-if="r.status === '待处理'" size="mini" type="primary" plain @click="handle(r, '已完成')">完成</van-button>
            <van-button v-if="r.status === '待处理'" size="mini" type="warning" plain style="margin-left:4px;" @click="handle(r, '已忽略')">忽略</van-button>
            <van-button v-else size="mini" plain type="danger" @click="del(r)">删</van-button>
          </template>
        </van-cell>
      </van-cell-group>
      <van-button round block type="primary" icon="plus" style="margin-top:16px;" @click="popup = true">添加提醒</van-button>
    </template>

    <van-popup v-model:show="popup" position="bottom" round>
      <div style="padding:16px;">
        <div style="font-size:16px;font-weight:600;margin-bottom:12px;">添加提醒</div>
        <van-form @submit="onAdd">
          <van-cell-group inset>
            <van-field v-model="newForm.title" label="标题" placeholder="如：轮胎更换" :rules="[{ required: true, message: '必填' }]" />
            <van-field label="类型">
              <template #input>
                <van-radio-group v-model="newForm.remind_type" direction="horizontal">
                  <van-radio name="自定义">自定义</van-radio>
                  <van-radio name="保养">保养</van-radio>
                  <van-radio name="保险">保险</van-radio>
                </van-radio-group>
              </template>
            </van-field>
            <van-field label="提醒日期" :model-value="newForm.target_date" readonly is-link @click="datePopup = true" />
            <van-field v-model.number="newForm.target_mileage" type="number" label="里程条件" placeholder="选填，km" />
            <van-field v-model="newForm.message" label="说明" placeholder="选填" />
          </van-cell-group>
          <div style="margin:16px;">
            <van-button round block type="primary" native-type="submit">添 加</van-button>
          </div>
        </van-form>
      </div>
    </van-popup>

    <van-popup v-model:show="datePopup" position="bottom" round>
      <van-date-picker :min-date="new Date(2020, 0, 1)" :max-date="new Date(2040, 11, 31)"
                       title="选择日期" @confirm="onDateConfirm" @cancel="datePopup = false" />
    </van-popup>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { showSuccessToast, showFailToast } from 'vant'
import api from '../api'

const records = ref([])
const loading = ref(true)
const tab = ref('待处理')
const popup = ref(false)
const datePopup = ref(false)
const newForm = ref({ title: '', remind_type: '自定义', target_date: '', target_mileage: null, message: '' })

async function load() {
  loading.value = true
  try {
    records.value = await api.get('/reminders', { params: { status: tab.value } })
  } catch (e) { showFailToast(e.message) } finally { loading.value = false }
}
onMounted(load)

async function handle(r, status) {
  try {
    await api.post(`/reminders/${r.id}/handle`, { status })
    showSuccessToast(status === '已完成' ? '已完成' : '已忽略')
    load()
  } catch (e) { showFailToast(e.message) }
}
async function del(r) {
  try {
    await api.delete(`/reminders/${r.id}`)
    showSuccessToast('已删除')
    load()
  } catch (e) { showFailToast(e.message) }
}
function onDateConfirm({ selectedValues }) {
  newForm.value.target_date = selectedValues.join('-')
  datePopup.value = false
}
async function onAdd() {
  try {
    await api.post('/reminders', {
      ...newForm.value,
      target_date: newForm.value.target_date || null,
      target_mileage: newForm.value.target_mileage || null
    })
    showSuccessToast('已添加')
    popup.value = false
    newForm.value = { title: '', remind_type: '自定义', target_date: '', target_mileage: null, message: '' }
    load()
  } catch (e) { showFailToast(e.message) }
}
</script>
