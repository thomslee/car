<template>
  <div>
    <van-skeleton v-if="loading" title :row="6" />
    <template v-else-if="rec">
      <!-- 头部 -->
      <van-cell-group inset>
        <van-cell>
          <template #title>
            <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;">
              <van-tag :type="rec.policy_type === '交强险' ? 'danger' : 'primary'" size="medium">{{ rec.policy_type }}</van-tag>
              <span style="font-size:16px;font-weight:700;">{{ rec.company }}</span>
            </div>
            <div style="font-size:12px;color:#969799;margin-top:4px;">保单号：{{ rec.policy_no || '未填' }}</div>
          </template>
          <template #value>
            <div style="text-align:right;">
              <div style="font-size:18px;font-weight:700;">¥{{ rec.premium }}</div>
              <div style="font-size:11px;color:#969799;">保费</div>
            </div>
          </template>
        </van-cell>
      </van-cell-group>

      <!-- 基本信息 -->
      <van-cell-group inset title="基本信息" style="margin-top:12px;">
        <van-cell title="保险公司" :value="rec.company" />
        <van-cell title="保单号" :value="rec.policy_no || '未填'" />
        <van-cell title="险种类型" :value="rec.policy_type" />
        <van-cell title="起保日期" :value="rec.start_date || '未填'" />
        <van-cell title="到期日期" :value="rec.end_date || '未填'" />
        <van-cell title="服务电话">
          <template #value>
            <a :href="'tel:' + rec.service_phone" style="color:#1989fa;text-decoration:none;">{{ rec.service_phone || '未填' }}</a>
          </template>
        </van-cell>
      </van-cell-group>

      <!-- 费用信息 -->
      <van-cell-group inset title="费用信息" style="margin-top:12px;">
        <van-cell title="保费" :value="'¥' + rec.premium" />
        <van-cell v-if="rec.policy_type === '交强险'" title="车船税">
          <template #value><span style="color:#ee0a24;font-weight:600;">¥{{ rec.vehicle_tax || 0 }}</span></template>
        </van-cell>
        <van-cell v-if="rec.policy_type === '交强险'" title="合计（保费+车船税）">
          <template #value><span style="font-weight:700;">¥{{ Number(rec.premium) + Number(rec.vehicle_tax || 0) }}</span></template>
        </van-cell>
      </van-cell-group>

      <!-- 险种明细 -->
      <van-cell-group inset title="险种明细" style="margin-top:12px;" v-if="items.length">
        <van-cell v-for="(item, idx) in items" :key="idx" :title="item" />
      </van-cell-group>

      <!-- 备注 -->
      <van-cell-group v-if="rec.note" inset title="备注" style="margin-top:12px;">
        <div style="padding:12px 16px;font-size:13px;color:#323233;white-space:pre-wrap;">{{ rec.note }}</div>
      </van-cell-group>

      <!-- 操作 -->
      <div style="margin:20px 16px;display:flex;gap:8px;">
        <van-button round block type="primary" icon="edit" style="flex:1;" @click="openEdit">编 辑</van-button>
        <van-button round block plain type="danger" icon="delete-o" style="flex:1;" @click="onDelete">删 除</van-button>
      </div>
    </template>
    <van-empty v-else description="保单不存在或已删除" />

    <!-- 编辑弹窗 -->
    <van-popup v-model:show="popup" position="bottom" round style="max-height:85vh;">
      <div style="padding:16px;">
        <div style="font-size:16px;font-weight:600;margin-bottom:12px;">编辑保单</div>
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
            <van-field v-model.number="form.vehicle_tax" type="number" label="车船税" placeholder="元（仅交强险）" />
            <van-field v-model="form.service_phone" label="服务电话" placeholder="如：95518" />
            <van-field label="起保日期" :model-value="form.start_date" readonly is-link @click="pick('start')" />
            <van-field label="到期日期" :model-value="form.end_date" readonly is-link @click="pick('end')" />
            <van-field v-model="form.items_text" label="险种明细" type="textarea" rows="2"
                       placeholder="如：第三者责任险200万、车损险（逗号分隔）" />
            <van-field v-model="form.note" label="备注" placeholder="选填" />
          </van-cell-group>
          <div style="margin:16px;">
            <van-button round block type="primary" native-type="submit" :loading="saving">保 存</van-button>
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
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { showSuccessToast, showFailToast, showConfirmDialog } from 'vant'
import api from '../api'

const route = useRoute()
const router = useRouter()
const vehicleId = route.params.id
const iid = route.params.iid
const rec = ref(null)
const loading = ref(true)
const popup = ref(false)
const saving = ref(false)
const picking = ref('start')
const datePopup = ref(false)

const form = ref(blank())

const items = computed(() => {
  try { return JSON.parse(rec.value?.items_json || '[]') } catch { return [] }
})

function blank() {
  return { vehicle_id: Number(vehicleId), company: '', policy_no: '', policy_type: '商业险',
    premium: 0, vehicle_tax: 0, service_phone: '', start_date: '', end_date: '', items_text: '', note: '' }
}

onMounted(async () => {
  try {
    const list = await api.get('/insurance', { params: { vehicle_id: vehicleId } })
    rec.value = list.find(r => r.id === Number(iid)) || null
  } catch (e) {
    showFailToast(e.message)
  } finally {
    loading.value = false
  }
})

function openEdit() {
  form.value = {
    vehicle_id: rec.value.vehicle_id, company: rec.value.company, policy_no: rec.value.policy_no,
    policy_type: rec.value.policy_type, premium: Number(rec.value.premium) || 0,
    vehicle_tax: Number(rec.value.vehicle_tax) || 0, service_phone: rec.value.service_phone || '',
    start_date: rec.value.start_date || '', end_date: rec.value.end_date || '',
    items_text: (() => { try { return JSON.parse(rec.value.items_json || '[]').join('、') } catch { return '' } })(),
    note: rec.value.note
  }
  popup.value = true
}

function pick(which) {
  picking.value = which
  datePopup.value = true
}

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
      vehicle_tax: form.value.vehicle_tax || 0,
      start_date: form.value.start_date || null,
      end_date: form.value.end_date || null,
      items_json: JSON.stringify(form.value.items_text.split(/[、,，]/).map(s => s.trim()).filter(Boolean))
    }
    await api.put(`/insurance/${iid}`, payload)
    showSuccessToast('已保存')
    popup.value = false
    // 刷新详情
    const list = await api.get('/insurance', { params: { vehicle_id: vehicleId } })
    rec.value = list.find(r => r.id === Number(iid)) || null
  } catch (e) { showFailToast(e.message) } finally { saving.value = false }
}

async function onDelete() {
  try {
    await showConfirmDialog({ title: '删除保单', message: '确定删除这条保单？' })
    await api.delete(`/insurance/${iid}`)
    showSuccessToast('已删除')
    router.back()
  } catch (e) {
    if (e !== 'cancel') showFailToast(e.message || '已取消')
  }
}
</script>
