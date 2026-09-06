<template>
  <div>
    <van-cell-group inset title="方式一：拍照/上传单据">
      <van-uploader v-model="fileList" :max-count="1" :after-read="onUpload" :loading="uploading" />
      <div style="font-size:11px;color:#969799;padding:8px 16px 12px;">
        支持 jpg/png。识别由已配置模型完成：支持视觉的模型直接读图；DeepSeek 为文本模型，请用方式二粘贴单据文字，原图会留存备查。
      </div>
    </van-cell-group>

    <van-cell-group inset title="方式二：粘贴单据文字（DeepSeek 适用）" style="margin-top:12px;">
      <van-field v-model="pasteText" type="textarea" rows="4" autosize
                 placeholder="把保养单上的文字复制粘贴到这里，如：&#10;2026年8月1日 里程44000公里 沃尔沃4S店 机油机滤 680元 工时费200元" />
      <van-cell>
        <van-button size="small" round type="primary" :loading="parsing" @click="onParseText">AI 提取字段</van-button>
      </van-cell>
    </van-cell-group>

    <!-- 识别草稿 -->
    <template v-if="draft">
      <van-cell-group inset title="识别结果（请核对后保存）" style="margin-top:12px;">
        <van-field label="日期" :model-value="draft.occurred_at || ''" readonly is-link @click="datePopup = true" />
        <van-field v-model.number="draft.mileage" type="number" label="里程" placeholder="km" />
        <van-field v-model="draft.shop_name" label="门店" placeholder="门店名称" />
        <van-field label="类型">
          <template #input>
            <van-radio-group v-model="draft.record_type" direction="horizontal">
              <van-radio name="保养">保养</van-radio>
              <van-radio name="维修">维修</van-radio>
            </van-radio-group>
          </template>
        </van-field>
        <van-field label="项目明细" type="textarea" rows="3" autosize :model-value="itemsText"
                   placeholder="每行一个：项目名 材料费 工时费" @update:model-value="setItemsText" />
      </van-cell-group>

      <van-cell-group inset title="费用（手填）" style="margin-top:12px;">
        <van-field v-model.number="draft.original_total_cost" type="number" label="原价合计" placeholder="0" />
        <van-field v-model.number="draft.discount_amount" type="number" label="折扣金额" placeholder="0（正数）" />
        <van-field label="折扣明细" type="textarea" rows="2" autosize :model-value="discountsText"
                   placeholder="每行一个：名称 金额" @update:model-value="setDiscountsText" />
        <van-field v-model.number="draft.total_cost" type="number" label="总金额" placeholder="0" />
        <van-field v-model.number="draft.paid_amount" type="number" label="已支付" placeholder="0" />
        <van-field v-model="draft.confirmed_at" label="确认时间" placeholder="YYYY-MM-DD HH:MM" />
        <van-field v-model="draft.skipped_note" label="未做项目" type="textarea" rows="2" autosize placeholder="选填" />
      </van-cell-group>

      <div style="display:flex;gap:8px;margin:16px 0;">
        <van-button round block type="primary" :loading="saving" @click="onSave">保存为保养记录</van-button>
        <van-button round block plain @click="draft = null">放弃</van-button>
      </div>
    </template>

    <van-popup v-model:show="datePopup" position="bottom" round>
      <van-date-picker :min-date="new Date(2000, 0, 1)" :max-date="new Date(2035, 11, 31)"
                       title="选择日期" @confirm="onDateConfirm" @cancel="datePopup = false" />
    </van-popup>

    <van-image-preview v-model:show="preview" :images="[previewUrl]" />
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { showSuccessToast, showFailToast } from 'vant'
import api from '../api'

const route = useRoute()
const router = useRouter()
const vehicleId = route.params.id

const fileList = ref([])
const uploading = ref(false)
const parsing = ref(false)
const saving = ref(false)
const pasteText = ref('')
const draft = ref(null)
const datePopup = ref(false)
const preview = ref(false)
const previewUrl = ref('')

const itemsText = computed({
  get: () => (draft.value?.items || []).map(i => `${i.item_name || ''} ${i.part_cost || 0} ${i.labor_cost || 0}`).join('\n'),
  set: () => {}
})

const discountsText = computed({
  get: () => (draft.value?.discounts || []).map(d => `${d.name || ''} ${d.amount || 0}`).join('\n'),
  set: () => {}
})

function setItemsText(text) {
  const oldItems = draft.value.items || []
  draft.value.items = text.split('\n').map((line, idx) => {
    const parts = line.trim().split(/\s+/)
    const name = parts[0] || ''
    const part = parseFloat(parts[1]) || 0
    const labor = parseFloat(parts[2]) || 0
    const old = oldItems[idx] || {}
    return {
      item_name: name, quantity: 1,
      item_type: old.item_type || '材料',
      unit_price: Number(old.unit_price) || 0,
      part_cost: part, labor_cost: labor,
      is_original: !!old.is_original, is_routine: true
    }
  }).filter(i => i.item_name)
}

function setDiscountsText(text) {
  draft.value.discounts = text.split('\n').map(line => {
    const parts = line.trim().split(/\s+/)
    const name = parts.slice(0, -1).join(' ') || ''
    const amount = parseFloat(parts[parts.length - 1]) || 0
    return { name, amount }
  }).filter(d => d.name)
}

async function onUpload(item) {
  uploading.value = true
  try {
    const fd = new FormData()
    fd.append('file', item.file)
    fd.append('vehicle_id', vehicleId)
    const res = await api.post('/ocr/upload', fd, { headers: { 'Content-Type': 'multipart/form-data' } })
    previewUrl.value = res.image_path
    if (res.mode === 'parsed') {
      draft.value = normalizeDraft(res.draft)
      if (res.text) pasteText.value = res.text
      showSuccessToast('识别完成，请核对')
    } else {
      showFailToast(res.message || '请粘贴文字或手工录入')
    }
    fileList.value = []
  } catch (e) {
    showFailToast(e.message)
    fileList.value = []
  } finally {
    uploading.value = false
  }
}

function normalizeDraft(d) {
  const today = new Date()
  return {
    occurred_at: d.occurred_at || `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`,
    mileage: d.mileage || null,
    shop_name: d.shop_name || '',
    record_type: d.record_type === '维修' ? '维修' : '保养',
    total_cost: Number(d.total_cost) || 0,
    original_total_cost: Number(d.original_total_cost) || 0,
    discount_amount: Number(d.discount_amount) || 0,
    paid_amount: Number(d.paid_amount) || 0,
    confirmed_at: d.confirmed_at || '',
    skipped_note: d.skipped_note || '',
    discounts: Array.isArray(d.discounts) && d.discounts.length
      ? d.discounts.map(x => ({ name: x.name || '', amount: Number(x.amount) || 0 }))
      : [],
    items: Array.isArray(d.items) && d.items.length
      ? d.items.map(i => ({
          item_name: i.item_name || '', quantity: Number(i.quantity) || 1,
          item_type: i.item_type || '材料', unit_price: Number(i.unit_price) || 0,
          part_cost: Number(i.part_cost) || 0, labor_cost: Number(i.labor_cost) || 0,
          is_original: !!i.is_original, is_routine: true
        }))
      : [{ item_name: '', quantity: 1, item_type: '材料', unit_price: 0, part_cost: 0, labor_cost: 0, is_original: false, is_routine: true }]
  }
}

async function onParseText() {
  if (!pasteText.value.trim()) { showFailToast('请先粘贴单据文字'); return }
  parsing.value = true
  try {
    const fd = new FormData()
    fd.append('text', pasteText.value)
    fd.append('vehicle_id', vehicleId)
    const res = await api.post('/ocr/parse-text', fd)
    if (res.draft) {
      draft.value = normalizeDraft(res.draft)
      showSuccessToast('提取完成，请核对')
    } else {
      showFailToast(res.message || '未配置可用大模型')
    }
  } catch (e) {
    showFailToast(e.message)
  } finally {
    parsing.value = false
  }
}

function onDateConfirm({ selectedValues }) {
  draft.value.occurred_at = selectedValues.join('-')
  datePopup.value = false
}

async function onSave() {
  saving.value = true
  try {
    const items = (draft.value.items || []).filter(i => i.item_name)
    const discounts = (draft.value.discounts || []).filter(d => d.name)
    await api.post('/maintenance', {
      vehicle_id: Number(vehicleId),
      occurred_at: draft.value.occurred_at,
      mileage: draft.value.mileage || 0,
      shop_name: draft.value.shop_name,
      record_type: draft.value.record_type,
      category: '',
      title: `${draft.value.record_type}记录`,
      total_cost: draft.value.total_cost || 0,
      original_total_cost: draft.value.original_total_cost || 0,
      discount_amount: draft.value.discount_amount || 0,
      paid_amount: draft.value.paid_amount || 0,
      confirmed_at: draft.value.confirmed_at || null,
      skipped_note: draft.value.skipped_note || '',
      items, discounts
    })
    showSuccessToast('已保存')
    router.push(`/vehicle/${vehicleId}/maintenance`)
  } catch (e) {
    showFailToast(e.message)
  } finally {
    saving.value = false
  }
}
</script>
