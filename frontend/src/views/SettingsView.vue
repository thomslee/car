<template>
  <div>
    <!-- 账号 -->
    <van-cell-group inset>
      <van-cell title="当前账号" :value="auth.user?.display_name || auth.user?.username" />
      <van-cell title="用户名" :value="auth.user?.username" />
      <van-cell is-link title="退出登录" @click="onLogout" />
    </van-cell-group>

    <!-- 模型管理 -->
    <van-cell-group inset title="大模型配置" style="margin-top:12px;">
      <div style="font-size:12px;color:#969799;padding:8px 16px;">
        系统支持多品牌大模型（OpenAI 兼容协议）。已内置 DeepSeek 模板，填入 API Key 并启用即可；规则引擎无需模型也能工作。
      </div>
      <van-cell v-for="p in providers" :key="p.id" :title="p.name" is-link @click="openEdit(p)"
                :label="`模型：${p.model_name} · ${p.capabilities}`">
        <template #value>
          <van-tag :type="p.is_enabled ? 'success' : 'default'" style="margin-right:4px;">{{ p.is_enabled ? '启用' : '停用' }}</van-tag>
          <van-tag v-if="p.is_default" type="primary">默认</van-tag>
        </template>
      </van-cell>
      <van-cell is-link @click="openAdd">
        <van-icon name="plus" style="margin-right:4px;" />添加模型
      </van-cell>
    </van-cell-group>

    <div style="font-size:11px;color:#969799;padding:12px 16px;line-height:1.6;">
      部署目标：腾讯云服务器，端口 8090。AI 分析数据为规则引擎结果，价格区间为估算，实际以门店报价为准。
    </div>

    <van-popup v-model:show="popup" position="bottom" round>
      <div style="padding:16px;">
        <div style="font-size:16px;font-weight:600;margin-bottom:12px;">{{ editingId ? '编辑模型' : '添加模型' }}</div>
        <van-form @submit="onSaveProvider">
          <van-cell-group inset>
            <van-field v-model="pform.name" label="名称" placeholder="如：DeepSeek" :rules="[{ required: true, message: '必填' }]" />
            <van-field v-model="pform.base_url" label="Base URL" placeholder="https://api.deepseek.com" :rules="[{ required: true, message: '必填' }]" />
            <van-field v-model="pform.api_key" label="API Key" placeholder="sk-..." />
            <van-field v-model="pform.model_name" label="模型名" placeholder="deepseek-chat" :rules="[{ required: true, message: '必填' }]" />
            <van-field label="能力">
              <template #input>
                <van-radio-group v-model="pform.capabilities" direction="horizontal">
                  <van-radio name="text">文本</van-radio>
                  <van-radio name="vision">视觉(读图)</van-radio>
                </van-radio-group>
              </template>
            </van-field>
            <van-cell title="启用">
              <template #right-icon><van-switch v-model="pform.is_enabled" size="20" /></template>
            </van-cell>
            <van-cell title="设为默认（AI 分析优先调用）">
              <template #right-icon><van-switch v-model="pform.is_default" size="20" /></template>
            </van-cell>
          </van-cell-group>
          <div style="margin:16px;">
            <van-button round block type="primary" native-type="submit" :loading="saving">保 存</van-button>
            <van-button v-if="editingId" round block plain type="danger" style="margin-top:8px;" @click="onDeleteProvider">删 除</van-button>
          </div>
        </van-form>
      </div>
    </van-popup>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { showSuccessToast, showFailToast, showConfirmDialog } from 'vant'
import { useAuthStore } from '../stores/auth'
import api from '../api'

const auth = useAuthStore()
const router = useRouter()
const providers = ref([])
const popup = ref(false)
const editingId = ref(null)
const saving = ref(false)
const pform = ref(blank())

function blank() {
  return { name: '', base_url: '', api_key: '', model_name: '', capabilities: 'text', is_enabled: false, is_default: false }
}

onMounted(load)

async function load() {
  try { providers.value = await api.get('/ai/providers') } catch (e) { showFailToast(e.message) }
}
function openAdd() { editingId.value = null; pform.value = blank(); popup.value = true }
function openEdit(p) {
  editingId.value = p.id
  pform.value = { name: p.name, base_url: p.base_url, api_key: p.api_key, model_name: p.model_name, capabilities: p.capabilities, is_enabled: p.is_enabled, is_default: p.is_default }
  popup.value = true
}
async function onSaveProvider() {
  saving.value = true
  try {
    if (editingId.value) { await api.put(`/ai/providers/${editingId.value}`, pform.value); showSuccessToast('已保存') }
    else { await api.post('/ai/providers', pform.value); showSuccessToast('已添加') }
    popup.value = false
    load()
  } catch (e) { showFailToast(e.message) } finally { saving.value = false }
}
async function onDeleteProvider() {
  try {
    await showConfirmDialog({ title: '删除模型', message: '确定删除该配置？' })
    await api.delete(`/ai/providers/${editingId.value}`)
    showSuccessToast('已删除')
    popup.value = false
    load()
  } catch (e) { if (e !== 'cancel') showFailToast(e.message || '已取消') }
}
function onLogout() {
  auth.logout()
  showSuccessToast('已退出')
  router.push('/login')
}
</script>
