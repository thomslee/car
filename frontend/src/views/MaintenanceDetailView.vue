<template>
  <div>
    <van-skeleton v-if="loading" title :row="6" />
    <template v-else-if="rec">
      <!-- 头部 -->
      <van-cell-group inset>
        <van-cell>
          <template #title>
            <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;">
              <van-tag :type="typeColor(rec.record_type)" size="medium">{{ rec.record_type }}</van-tag>
              <span style="font-size:16px;font-weight:700;">{{ rec.title || rec.category || '保养记录' }}</span>
            </div>
            <div style="font-size:12px;color:#969799;margin-top:4px;">{{ rec.occurred_at }}</div>
          </template>
          <template #value>
            <div style="text-align:right;">
              <div style="font-size:18px;font-weight:700;">¥{{ rec.total_cost }}</div>
              <div style="font-size:11px;color:#969799;">总金额</div>
            </div>
          </template>
        </van-cell>
      </van-cell-group>

      <!-- 基本信息 -->
      <van-cell-group inset title="基本信息" style="margin-top:12px;">
        <van-cell title="日期" :value="rec.occurred_at" />
        <van-cell title="里程" :value="(rec.mileage || 0) + ' km'" />
        <van-cell title="门店" :value="rec.shop_name || '未填'" />
        <van-cell title="类别" :value="rec.category || '未填'" />
        <van-cell title="发票号" :value="rec.invoice_no || '未填'" v-if="rec.invoice_no" />
        <van-cell title="质保内" :value="rec.warranty ? '是' : '否'" />
      </van-cell-group>

      <!-- 描述 -->
      <van-cell-group v-if="rec.description" inset title="描述" style="margin-top:12px;">
        <div style="padding:12px 16px;font-size:13px;color:#323233;white-space:pre-wrap;">{{ rec.description }}</div>
      </van-cell-group>

      <!-- 项目明细 -->
      <van-cell-group inset title="项目明细" style="margin-top:12px;">
        <van-cell v-for="it in rec.items" :key="it.id" center>
          <template #title>
            <div style="display:flex;align-items:center;gap:6px;flex-wrap:wrap;">
              <span style="font-weight:600;">{{ it.item_name }}</span>
              <van-tag :type="it.item_type === '工时' ? 'warning' : 'primary'" size="small">{{ it.item_type || '材料' }}</van-tag>
              <van-tag v-if="it.is_original" type="success" size="small">原厂件</van-tag>
            </div>
            <div style="font-size:12px;color:#969799;margin-top:2px;">
              数量 {{ it.quantity }} · 单价 ¥{{ Number(it.unit_price) || 0 }} · 材料 ¥{{ Number(it.part_cost) || 0 }} · 工时 ¥{{ Number(it.labor_cost) || 0 }}
            </div>
          </template>
          <template #value>
            <span style="font-weight:600;">¥{{ (Number(it.part_cost) || 0) + (Number(it.labor_cost) || 0) }}</span>
          </template>
        </van-cell>
        <van-cell v-if="!rec.items.length" title="无项目明细" />
      </van-cell-group>

      <!-- 费用结算 -->
      <van-cell-group inset title="费用结算" style="margin-top:12px;">
        <van-cell title="原价合计" :value="'¥' + (rec.original_total_cost || 0)" />
        <van-cell title="折扣金额" is-link @click="showDiscounts = !showDiscounts">
          <template #value>
            <span style="color:#ee0a24;">-¥{{ rec.discount_amount || 0 }}</span>
          </template>
        </van-cell>
        <div v-if="showDiscounts && rec.discounts && rec.discounts.length" style="background:#f7f8fa;padding:8px 16px;">
          <div v-for="d in rec.discounts" :key="d.id" style="display:flex;justify-content:space-between;font-size:13px;padding:4px 0;color:#646566;">
            <span>{{ d.name }}</span>
            <span style="color:#ee0a24;">-¥{{ d.amount }}</span>
          </div>
        </div>
        <van-cell title="总金额" :value="'¥' + (rec.total_cost || 0)">
          <template #title><span style="font-weight:600;">总金额</span></template>
        </van-cell>
        <van-cell title="已支付" :value="'¥' + (rec.paid_amount || 0)" />
        <van-cell title="客户确认时间" :value="formatDateTime(rec.confirmed_at)" v-if="rec.confirmed_at" />
      </van-cell-group>

      <!-- 本次未做项目 -->
      <van-cell-group v-if="rec.skipped_note" inset title="本次未做项目" style="margin-top:12px;">
        <div style="padding:12px 16px;font-size:13px;color:#323233;white-space:pre-wrap;">{{ rec.skipped_note }}</div>
      </van-cell-group>

      <!-- 备注 -->
      <van-cell-group v-if="rec.notes" inset title="备注" style="margin-top:12px;">
        <div style="padding:12px 16px;font-size:13px;color:#323233;white-space:pre-wrap;">{{ rec.notes }}</div>
      </van-cell-group>

      <!-- 单据图片 -->
      <van-cell-group v-if="attachments.length" inset title="单据图片" style="margin-top:12px;">
        <div style="display:flex;flex-wrap:wrap;gap:8px;padding:12px 16px;">
          <van-image v-for="a in attachments" :key="a.id" :src="a.url" width="96" height="96" fit="cover"
                     style="border-radius:8px;overflow:hidden;" @click="previewIndex = 0" />
        </div>
      </van-cell-group>
      <van-image-preview v-model:show="previewShow" :images="previewImages" :start-position="previewIndex" />

      <!-- 操作 -->
      <div style="margin:20px 16px;display:flex;gap:8px;">
        <van-button round block type="primary" icon="edit" style="flex:1;" @click="onEdit">编 辑</van-button>
        <van-button round block plain type="danger" icon="delete-o" style="flex:1;" @click="onDelete">删 除</van-button>
      </div>
    </template>
    <van-empty v-else description="记录不存在或已删除" />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { showSuccessToast, showFailToast, showConfirmDialog } from 'vant'
import api from '../api'

const route = useRoute()
const router = useRouter()
const vehicleId = route.params.id
const mid = route.params.mid
const rec = ref(null)
const loading = ref(true)
const showDiscounts = ref(false)
const attachments = ref([])
const previewShow = ref(false)
const previewIndex = ref(0)
const previewImages = ref([])

function typeColor(t) {
  return { 保养: 'primary', 维修: 'danger', 年检: 'warning', 其他: 'default' }[t] || 'default'
}

function formatDateTime(v) {
  if (!v) return ''
  return String(v).replace('T', ' ').replace(/\.\d+$/, '').slice(0, 16)
}

onMounted(async () => {
  try {
    rec.value = await api.get(`/maintenance/${mid}`)
    attachments.value = await api.get('/attachments', { params: { vehicle_id: vehicleId, biz_id: mid } })
    previewImages.value = attachments.value.map(a => a.url)
  } catch (e) {
    showFailToast(e.message)
  } finally {
    loading.value = false
  }
})

function onEdit() {
  router.push(`/vehicle/${vehicleId}/maintenance/${mid}/edit`)
}

async function onDelete() {
  try {
    await showConfirmDialog({
      title: '删除记录',
      message: '删除后不可恢复，确定删除这条' + (rec.value.record_type || '保养') + '记录？'
    })
    await api.delete(`/maintenance/${mid}`)
    showSuccessToast('已删除')
    router.back()
  } catch (e) {
    if (e !== 'cancel') showFailToast(e.message || '已取消')
  }
}
</script>
