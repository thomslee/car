<template>
  <div>
    <van-notice-bar v-if="!hasModel" left-icon="info-o" wrapable>
      未配置可用大模型（可在「设置」中填入 DeepSeek API Key 启用），以下为规则引擎结果，同样有依据可查。
    </van-notice-bar>

    <van-tabs v-model:active="tab" sticky>
      <van-tab title="保养预测" name="plan" />
      <van-tab title="过度保养" name="over" />
      <van-tab title="价格估算" name="price" />
      <van-tab title="健康报告" name="health" />
    </van-tabs>

    <!-- 保养预测 -->
    <div v-if="tab === 'plan'">
      <van-button round block type="primary" style="margin:12px 0;" :loading="planLoading" @click="runPlan">生成保养预测</van-button>
      <template v-if="plan">
        <div style="display:flex;gap:8px;margin-bottom:12px;flex-wrap:wrap;">
          <div style="flex:1 1 130px;background:#fff;border-radius:10px;padding:12px;text-align:center;">
            <div style="font-size:11px;color:#969799;">预计下次保养</div>
            <div style="font-size:15px;font-weight:600;color:#1989fa;margin-top:4px;">{{ plan.next_maintenance_date || '暂无' }}</div>
            <div style="font-size:11px;color:#969799;">或 {{ plan.next_maintenance_mileage || '--' }} km</div>
          </div>
          <div style="flex:1 1 130px;background:#fff;border-radius:10px;padding:12px;text-align:center;">
            <div style="font-size:11px;color:#969799;">月均里程估算</div>
            <div style="font-size:15px;font-weight:600;margin-top:4px;">{{ plan.monthly_km_estimate }}</div>
            <div style="font-size:11px;color:#969799;">km/月</div>
          </div>
        </div>
        <van-cell-group inset title="临期项目">
          <van-cell v-for="i in plan.due_items" :key="i.item_name"
                    :title="i.item_name" :label="`下次：${i.due_date} 或 ${i.due_mileage}km · ${i.manual_note}`">
            <template #value>
              <van-tag :type="i.status === '已到期' ? 'danger' : 'warning'">{{ i.status }}</van-tag>
            </template>
          </van-cell>
          <van-empty v-if="!plan.due_items.length" description="暂无临期项目" image-size="60" />
        </van-cell-group>
        <van-cell-group inset title="全部项目周期" style="margin-top:12px;">
          <van-cell v-for="i in plan.plan_items" :key="i.item_name" :title="i.item_name"
                    :label="`上次：${i.last_date || '未记录'} · 下次：${i.due_date} 或 ${i.due_mileage}km`">
            <template #value>
              <van-tag plain :type="tagType(i.status)">{{ i.status }}</van-tag>
            </template>
          </van-cell>
        </van-cell-group>
        <div v-if="plan.narration" style="margin-top:12px;background:#fff;border-radius:10px;padding:12px;font-size:13px;line-height:1.6;white-space:pre-wrap;">
          <div style="font-weight:600;margin-bottom:6px;">AI 解读</div>{{ plan.narration }}
        </div>
        <div style="font-size:11px;color:#969799;margin-top:8px;">{{ plan.estimate_note }}</div>
      </template>
    </div>

    <!-- 过度保养 -->
    <div v-if="tab === 'over'">
      <van-button round block type="primary" style="margin:12px 0;" :loading="overLoading" @click="runOver">检测过度保养</van-button>
      <template v-if="over">
        <div v-if="over.early_count" style="background:#fff8e6;border-radius:10px;padding:12px;font-size:13px;margin-bottom:12px;">
          发现 {{ over.early_count }} 项可能过早保养，可适当延长间隔，节省费用。
        </div>
        <van-cell-group inset>
          <van-cell v-for="f in over.findings" :key="f.item_name + f.cur_date" :title="f.item_name"
                    :label="`${f.prev_date} → ${f.cur_date} · 实际间隔 ${f.km_interval ?? '--'}km/${f.month_interval}月 · 建议 ${f.manual_interval_km}km/${f.manual_interval_months}月`">
            <template #value>
              <van-tag :type="f.judgment === '可能过早' ? 'warning' : 'success'">{{ f.judgment }}</van-tag>
            </template>
            <template #extra>
              <div style="font-size:12px;color:#969799;white-space:normal;line-height:1.5;">{{ f.suggestion }}</div>
            </template>
          </van-cell>
          <van-empty v-if="!over.findings.length" description="记录不足或暂无异常（至少需同一项目两次记录）" image-size="60" />
        </van-cell-group>
        <div v-if="over.narration" style="margin-top:12px;background:#fff;border-radius:10px;padding:12px;font-size:13px;line-height:1.6;white-space:pre-wrap;">
          <div style="font-weight:600;margin-bottom:6px;">AI 解读</div>{{ over.narration }}
        </div>
      </template>
    </div>

    <!-- 价格估算 -->
    <div v-if="tab === 'price'">
      <van-cell-group inset style="margin-top:12px;">
        <van-field v-model="priceItems" label="项目" type="textarea" rows="3"
                   placeholder="输入项目名，逗号分隔&#10;如：机油及机油滤清器,火花塞,制动液" />
      </van-cell-group>
      <van-button round block type="primary" style="margin:12px 0;" :loading="priceLoading" @click="runPrice">估算价格</van-button>
      <van-cell-group inset v-if="price">
        <van-cell v-for="i in price.items" :key="i.item_name" :title="i.item_name"
                  :label="`来源：${i.source}${i.sample_count ? '（' + i.sample_count + '次记录）' : ''}`">
          <template #value>
            <span v-if="i.avg !== null" style="font-weight:600;">¥{{ i.avg }}</span>
            <span v-else style="color:#969799;">暂无参考</span>
          </template>
          <template #extra>
            <div style="font-size:12px;color:#969799;">
              {{ i.price_min !== null ? `区间 ¥${i.price_min}~${i.price_max}` : '' }}
            </div>
          </template>
        </van-cell>
      </van-cell-group>
      <div v-if="price" style="font-size:11px;color:#969799;">{{ price.note }}</div>
      <div v-if="price?.narration" style="margin-top:12px;background:#fff;border-radius:10px;padding:12px;font-size:13px;line-height:1.6;white-space:pre-wrap;">
        <div style="font-weight:600;margin-bottom:6px;">AI 解读</div>{{ price.narration }}
      </div>
    </div>

    <!-- 健康报告 -->
    <div v-if="tab === 'health'">
      <van-button round block type="primary" style="margin:12px 0;" :loading="healthLoading" @click="runHealth">生成健康报告</van-button>
      <template v-if="health">
        <div style="background:#fff;border-radius:10px;padding:16px;text-align:center;margin-bottom:12px;">
          <div style="font-size:11px;color:#969799;">车辆健康评分</div>
          <div :style="`font-size:40px;font-weight:700;color:${scoreColor(health.score)};`">{{ health.score }}</div>
          <div style="font-size:11px;color:#969799;margin-top:4px;">
            月均 {{ health.monthly_km }}km · 保养 {{ health.maintenance_count }} 次 · 维修 {{ health.repair_count }} 次 · 过早保养 {{ health.early_maintenance_count }} 项
          </div>
        </div>
        <van-cell-group inset>
          <van-cell title="下次保养日期" :value="health.next_maintenance_date || '暂无'" />
          <van-cell title="下次保养里程" :value="health.next_maintenance_mileage ? health.next_maintenance_mileage + ' km' : '暂无'" />
        </van-cell-group>
        <div v-if="health.narration" style="margin-top:12px;background:#fff;border-radius:10px;padding:12px;font-size:13px;line-height:1.6;white-space:pre-wrap;">
          <div style="font-weight:600;margin-bottom:6px;">AI 解读</div>{{ health.narration }}
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { showFailToast } from 'vant'
import api from '../api'

const route = useRoute()
const vehicleId = route.params.id
const tab = ref('plan')
const hasModel = ref(false)
const plan = ref(null)
const over = ref(null)
const price = ref(null)
const health = ref(null)
const priceItems = ref('机油及机油滤清器,火花塞,制动液')
const planLoading = ref(false)
const overLoading = ref(false)
const priceLoading = ref(false)
const healthLoading = ref(false)

onMounted(async () => {
  try {
    const providers = await api.get('/ai/providers')
    hasModel.value = providers.some(p => p.is_enabled && p.api_key)
  } catch (e) { /* ignore */ }
})

function tagType(s) {
  return { 已到期: 'danger', 临期: 'warning', 未到期: 'success', 未记录: 'default' }[s] || 'default'
}
function scoreColor(s) {
  return s >= 80 ? '#07c160' : s >= 60 ? '#ff976a' : '#ee0a24'
}

async function runPlan() {
  planLoading.value = true
  try { plan.value = await api.post('/ai/maintenance-plan', { vehicle_id: vehicleId }) }
  catch (e) { showFailToast(e.message) } finally { planLoading.value = false }
}
async function runOver() {
  overLoading.value = true
  try { over.value = await api.post('/ai/over-maintenance', { vehicle_id: vehicleId }) }
  catch (e) { showFailToast(e.message) } finally { overLoading.value = false }
}
async function runPrice() {
  priceLoading.value = true
  try {
    const items = priceItems.value.split(/[、,，]/).map(s => s.trim()).filter(Boolean)
    price.value = await api.post('/ai/price-estimate', { vehicle_id: vehicleId, items })
  } catch (e) { showFailToast(e.message) } finally { priceLoading.value = false }
}
async function runHealth() {
  healthLoading.value = true
  try { health.value = await api.post('/ai/health-report', { vehicle_id: vehicleId }) }
  catch (e) { showFailToast(e.message) } finally { healthLoading.value = false }
}
</script>
