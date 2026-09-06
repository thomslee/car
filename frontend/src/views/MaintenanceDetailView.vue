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
              <div style="font-size:11px;color:#969799;">总费用</div>
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
        <van-cell v-for="it in rec.items" :key="it.id" :title="it.item_name">
          <template #label>
            <div style="margin-top:2px;">
              数量 {{ it.quantity }}<span v-if="it.part_cost"> · 材料 ¥{{ it.part_cost }}</span><span v-if="it.labor_cost"> · 工时 ¥{{ it.labor_cost }}</span>
            </div>
          </template>
          <template #value>
            <span v-if="it.part_cost || it.labor_cost" style="font-weight:600;">¥{{ (Number(it.part_cost) || 0) + (Number(it.labor_cost) || 0) }}</span>
          </template>
        </van-cell>
        <van-cell v-if="!rec.items.length" title="无项目明细" />
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
const attachments = ref([])
const previewShow = ref(false)
const previewIndex = ref(0)
const previewImages = ref([])

function typeColor(t) {
  return { 保养: 'primary', 维修: 'danger', 年检: 'warning', 其他: 'default' }[t] || 'default'
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
