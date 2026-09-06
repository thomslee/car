<template>
  <div>
    <van-cell-group inset>
      <van-cell v-for="u in users" :key="u.id" :title="u.display_name || u.username"
                :label="`@${u.username} · 创建于 ${(u.created_at || '').slice(0, 10)}`">
        <template #value>
          <van-tag :type="u.role === 'admin' ? 'primary' : 'default'" style="margin-right:4px;">{{ u.role === 'admin' ? '管理员' : '用户' }}</van-tag>
          <van-tag :type="u.is_active ? 'success' : 'danger'">{{ u.is_active ? '启用' : '禁用' }}</van-tag>
        </template>
        <template #right-icon>
          <van-icon name="edit" color="#1989fa" style="margin:0 12px;" @click="openEdit(u)" />
          <van-icon v-if="u.id !== auth.user?.id" name="delete-o" color="#ee0a24" @click="onDelete(u)" />
        </template>
      </van-cell>
      <van-cell v-if="!users.length" title="暂无用户" label="点击下方按钮创建账号" />
    </van-cell-group>

    <div style="margin:16px;">
      <van-button round block type="primary" icon="plus" @click="openCreate">新建用户</van-button>
    </div>
    <div style="font-size:12px;color:#969799;padding:0 16px;line-height:1.6;">
      账号由管理员统一创建；新用户用初始密码登录后可在「设置 → 修改密码」中自行更改。
    </div>

    <van-popup v-model:show="popup" position="bottom" round>
      <div style="padding:16px;">
        <div style="font-size:16px;font-weight:600;margin-bottom:12px;">{{ editingId ? '编辑用户' : '新建用户' }}</div>
        <van-form @submit="onSave">
          <van-cell-group inset>
            <van-field v-if="!editingId" v-model="form.username" label="用户名" placeholder="登录名，3-50 位"
                       :rules="[{ required: true, message: '必填' }, { validator: (v) => v.length >= 3, message: '至少 3 位' }]" />
            <van-field v-model="form.display_name" label="显示名" placeholder="如：家人、妻子（可留空）" />
            <van-field v-model="form.password" :type="showPwd ? 'text' : 'password'" :label="editingId ? '重置密码' : '初始密码'"
                       placeholder="至少 6 位（留空则不修改）">
              <template #button><van-icon :name="showPwd ? 'eye-o' : 'closed-eye'" @click="showPwd = !showPwd" /></template>
            </van-field>
            <van-field label="角色">
              <template #input>
                <van-radio-group v-model="form.role" direction="horizontal">
                  <van-radio name="user">普通用户</van-radio>
                  <van-radio name="admin">管理员</van-radio>
                </van-radio-group>
              </template>
            </van-field>
            <van-cell v-if="editingId" title="启用账号">
              <template #right-icon><van-switch v-model="form.is_active" size="20" /></template>
            </van-cell>
          </van-cell-group>
          <div style="margin:16px;">
            <van-button round block type="primary" native-type="submit" :loading="saving">{{ editingId ? '保 存' : '创 建' }}</van-button>
          </div>
        </van-form>
      </div>
    </van-popup>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { showSuccessToast, showFailToast, showConfirmDialog } from 'vant'
import { useAuthStore } from '../stores/auth'
import api from '../api'

const auth = useAuthStore()
const users = ref([])
const popup = ref(false)
const editingId = ref(null)
const saving = ref(false)
const showPwd = ref(false)
const form = ref(blank())

function blank() {
  return { username: '', display_name: '', password: '', role: 'user', is_active: true }
}

onMounted(load)

async function load() {
  try { users.value = await api.get('/admin/users') } catch (e) { showFailToast(e.message) }
}
function openCreate() {
  editingId.value = null
  form.value = blank()
  showPwd.value = false
  popup.value = true
}
function openEdit(u) {
  editingId.value = u.id
  form.value = { username: u.username, display_name: u.display_name, password: '', role: u.role, is_active: u.is_active }
  showPwd.value = false
  popup.value = true
}
async function onSave() {
  saving.value = true
  try {
    if (editingId.value) {
      const body = { display_name: form.value.display_name, role: form.value.role, is_active: form.value.is_active }
      if (form.value.password) body.password = form.value.password
      await api.put(`/admin/users/${editingId.value}`, body)
      showSuccessToast('已保存')
    } else {
      await api.post('/admin/users', { ...form.value, display_name: form.value.display_name || form.value.username })
      showSuccessToast('账号已创建')
    }
    popup.value = false
    load()
  } catch (e) { showFailToast(e.message) } finally { saving.value = false }
}
async function onDelete(u) {
  try {
    await showConfirmDialog({ title: '删除用户', message: `将删除 ${u.display_name || u.username} 及其名下全部车辆与记录，不可恢复。确定？` })
    await api.delete(`/admin/users/${u.id}`)
    showSuccessToast('已删除')
    load()
  } catch (e) { if (e !== 'cancel') showFailToast(e.message || '已取消') }
}
</script>
