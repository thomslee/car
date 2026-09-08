<template>
  <div>
    <!-- 油耗概览 -->
    <div style="display:flex;gap:8px;margin-bottom:12px;flex-wrap:wrap;" v-if="stats">
      <div style="flex:1 1 96px;background:#fff;border-radius:10px;padding:12px;text-align:center;">
        <div style="font-size:11px;color:#969799;">平均油耗</div>
        <div style="font-size:16px;font-weight:600;margin-top:4px;">{{ stats.overall_l100 ?? '--' }}</div>
        <div style="font-size:11px;color:#969799;">L/100km</div>
      </div>
      <div style="flex:1 1 96px;background:#fff;border-radius:10px;padding:12px;text-align:center;">
        <div style="font-size:11px;color:#969799;">加油总额</div>
        <div style="font-size:16px;font-weight:600;margin-top:4px;">{{ stats.total_cost }}</div>
        <div style="font-size:11px;color:#969799;">元 · {{ stats.record_count }} 次</div>
      </div>
    </div>

    <van-skeleton title :row="3" v-if="loading" />
    <template v-else>
      <van-empty v-if="!records.length" description="还没有加油记录">
        <van-button round type="primary" size="small" @click="router.push(`/vehicle/${vehicleId}/refuels/new`)">记一笔</van-button>
      </van-empty>

      <!-- 加油记录卡片（参照订单列表样式） -->
      <div v-for="r in records" :key="r.id"
           style="background:#fff;border-radius:10px;padding:14px 16px;margin-top:10px;"
           @click="router.push(`/vehicle/${vehicleId}/refuels/${r.id}`)">
        <!-- 第一行：加油站名称 -->
        <div style="font-size:16px;font-weight:700;color:#1a1a1a;">{{ r.station || '未填加油站' }}</div>
        <!-- 第二行：油标 + 实付金额 -->
        <div style="display:flex;justify-content:space-between;align-items:center;margin-top:6px;">
          <span style="font-size:14px;color:#646566;">{{ r.fuel_grade || '95' }}号{{ r.fuel_type || '汽油' }}</span>
          <span style="font-size:18px;font-weight:700;color:#1a1a1a;">实付 ¥{{ r.paid_amount != null && r.paid_amount > 0 ? r.paid_amount : r.total_cost }}</span>
        </div>
        <!-- 第三行：单价 · 数量 · 应付 -->
        <div style="font-size:12px;color:#969799;margin-top:4px;">
          单价 ¥{{ r.unit_price }}/L · {{ r.fuel_amount_l }}L · 应付 ¥{{ r.total_cost }}
        </div>
        <!-- 第四行：日期时间 -->
        <div style="font-size:12px;color:#969799;margin-top:4px;">{{ formatDateTime(r.refueled_at) }}</div>
      </div>

      <div style="display:flex;gap:8px;margin-top:16px;">
        <van-button round block plain type="primary" icon="mic" @click="openVoice">语音录入</van-button>
        <van-button round block type="primary" icon="plus" @click="router.push(`/vehicle/${vehicleId}/refuels/new`)">记一笔加油</van-button>
      </div>
    </template>

    <!-- 语音录入弹窗 -->
    <van-popup v-model:show="voicePopup" position="bottom" round style="max-height:90vh;">
      <div style="padding:16px;">
        <div style="font-size:16px;font-weight:600;margin-bottom:12px;text-align:center;">语音录入加油记录</div>

        <!-- 麦克风 -->
        <div style="text-align:center;margin:16px 0;">
          <van-button round type="primary" size="large" icon="mic" :loading="listening"
                      @click="toggleListen" :style="{ background: listening ? '#ee0a24' : '' }">
            {{ listening ? '正在聆听...点击停止' : '点击开始说话' }}
          </van-button>
          <div style="font-size:11px;color:#969799;margin-top:8px;" v-if="!voiceSupported">
            当前浏览器不支持语音识别，请手动输入文字
          </div>
        </div>

        <!-- 识别文字 -->
        <van-field v-model="voiceText" type="textarea" rows="3" autosize
                   label="识别文字" placeholder="说出加油信息，如：今天下午3点在中石化加了300元95号汽油，加了40升，单价7.5元" />
        <van-cell>
          <van-button size="small" round type="primary" :loading="parsing" @click="onParseVoice">AI 提取字段</van-button>
        </van-cell>

        <!-- 草稿表单 -->
        <template v-if="voiceDraft">
          <van-cell-group inset title="核对信息" style="margin-top:12px;">
            <van-field v-model="voiceDraft.refueled_at" label="加油时间" placeholder="YYYY-MM-DD HH:MM" />
            <van-field v-model="voiceDraft.station_name" label="加油站" placeholder="如：中石化" />
            <van-field label="油标">
              <template #input>
                <van-radio-group v-model="voiceDraft.fuel_grade" direction="horizontal">
                  <van-radio name="92">92</van-radio>
                  <van-radio name="95">95</van-radio>
                  <van-radio name="98">98</van-radio>
                </van-radio-group>
              </template>
            </van-field>
            <van-field v-model.number="voiceDraft.liters" type="number" label="升数" placeholder="L" />
            <van-field v-model.number="voiceDraft.unit_price" type="number" label="单价" placeholder="元/L" />
            <van-field v-model.number="voiceDraft.total_cost" type="number" label="应付金额" placeholder="元" />
            <van-field v-model.number="voiceDraft.paid_amount" type="number" label="实付金额" placeholder="元（优惠后）" />
            <van-field v-model.number="voiceDraft.mileage" type="number" label="里程" placeholder="km（选填）" />
          </van-cell-group>

          <div style="display:flex;gap:8px;margin:16px 0;">
            <van-button round block type="primary" :loading="saving" @click="onSaveVoice">保存加油记录</van-button>
            <van-button round block plain @click="closeVoice">放弃</van-button>
          </div>
        </template>

        <van-button round block plain style="margin-top:8px;" @click="voicePopup = false">关闭</van-button>
      </div>
    </van-popup>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { showFailToast, showSuccessToast } from 'vant'
import api from '../api'

const route = useRoute()
const router = useRouter()
const vehicleId = route.params.id
const records = ref([])
const stats = ref(null)
const loading = ref(true)

// 语音录入
const voicePopup = ref(false)
const listening = ref(false)
const voiceText = ref('')
const voiceDraft = ref(null)
const parsing = ref(false)
const saving = ref(false)
let recognition = null

const voiceSupported = ref(typeof window !== 'undefined' && (window.SpeechRecognition || window.webkitSpeechRecognition))

function formatDateTime(v) {
  if (!v) return ''
  return String(v).replace('T', ' ').replace(/\.\d+$/, '').slice(0, 16)
}

function openVoice() {
  voicePopup.value = true
  voiceText.value = ''
  voiceDraft.value = null
}

function closeVoice() {
  stopListen()
  voicePopup.value = false
}

function toggleListen() {
  if (listening.value) {
    stopListen()
  } else {
    startListen()
  }
}

function startListen() {
  if (!voiceSupported.value) {
    showFailToast('当前浏览器不支持语音识别，请手动输入文字')
    return
  }
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition
  recognition = new SR()
  recognition.lang = 'zh-CN'
  recognition.interimResults = true
  recognition.continuous = true
  recognition.onresult = (event) => {
    let text = ''
    for (let i = 0; i < event.results.length; i++) {
      text += event.results[i][0].transcript
    }
    voiceText.value = text
  }
  recognition.onerror = (e) => {
    if (e.error !== 'no-speech') {
      showFailToast('语音识别出错：' + e.error)
    }
    listening.value = false
  }
  recognition.onend = () => {
    listening.value = false
  }
  try {
    recognition.start()
    listening.value = true
  } catch (e) {
    showFailToast('启动语音识别失败')
  }
}

function stopListen() {
  if (recognition) {
    try { recognition.stop() } catch (e) {}
    recognition = null
  }
  listening.value = false
}

async function onParseVoice() {
  if (!voiceText.value.trim()) { showFailToast('请先说话或输入文字'); return }
  parsing.value = true
  try {
    const fd = new FormData()
    fd.append('text', voiceText.value)
    fd.append('vehicle_id', vehicleId)
    fd.append('doc_type', 'refuel')
    const res = await api.post('/ocr/parse-text', fd)
    if (res.draft) {
      voiceDraft.value = normalizeRefuelDraft(res.draft)
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

function normalizeRefuelDraft(d) {
  const now = new Date()
  const defaultTime = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')} ${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`
  return {
    refueled_at: d.refueled_at || defaultTime,
    station_name: d.station_name || '',
    fuel_grade: ['92', '95', '98'].includes(d.fuel_grade) ? d.fuel_grade : '95',
    liters: Number(d.liters) || null,
    unit_price: Number(d.unit_price) || null,
    total_cost: Number(d.total_cost) || 0,
    paid_amount: Number(d.paid_amount) || Number(d.total_cost) || 0,
    mileage: Number(d.mileage) || null,
  }
}

async function onSaveVoice() {
  saving.value = true
  try {
    await api.post('/refuels', {
      vehicle_id: Number(vehicleId),
      refueled_at: voiceDraft.value.refueled_at,
      station: voiceDraft.value.station_name,
      fuel_grade: voiceDraft.value.fuel_grade,
      fuel_amount_l: voiceDraft.value.liters || 0,
      unit_price: voiceDraft.value.unit_price || 0,
      total_cost: voiceDraft.value.total_cost || 0,
      paid_amount: voiceDraft.value.paid_amount || voiceDraft.value.total_cost || 0,
      mileage: voiceDraft.value.mileage || null,
    })
    showSuccessToast('已保存')
    closeVoice()
    load()
  } catch (e) {
    showFailToast(e.message)
  } finally {
    saving.value = false
  }
}

async function load() {
  loading.value = true
  try {
    records.value = await api.get('/refuels', { params: { vehicle_id: vehicleId } })
    stats.value = await api.get(`/refuels/${vehicleId}/stats`)
  } catch (e) {
    showFailToast(e.message)
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>
