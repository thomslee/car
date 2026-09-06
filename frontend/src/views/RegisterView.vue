<template>
  <div style="min-height:100vh;padding:32px 24px;box-sizing:border-box;background:#F7F8FA;">
    <div style="font-size:20px;font-weight:700;margin-bottom:24px;">注册账号</div>
    <van-form @submit="onSubmit">
      <van-cell-group inset>
        <van-field v-model="username" name="username" label="用户名" placeholder="3-50位"
                   :rules="[{ required: true, message: '请输入用户名' }, { pattern: /^.{3,50}$/, message: '至少3个字符' }]" />
        <van-field v-model="displayName" name="displayName" label="昵称" placeholder="选填" />
        <van-field v-model="password" type="password" name="password" label="密码" placeholder="至少6位"
                   :rules="[{ required: true, message: '请输入密码' }, { pattern: /^.{6,100}$/, message: '至少6位' }]" />
      </van-cell-group>
      <div style="margin:24px 16px;">
        <van-button round block type="primary" native-type="submit" :loading="loading">注 册</van-button>
      </div>
    </van-form>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { showSuccessToast, showFailToast } from 'vant'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const auth = useAuthStore()
const username = ref('')
const displayName = ref('')
const password = ref('')
const loading = ref(false)

async function onSubmit() {
  loading.value = true
  try {
    await auth.register(username.value, password.value, displayName.value)
    showSuccessToast('注册成功')
    router.push('/')
  } catch (e) {
    showFailToast(e.message)
  } finally {
    loading.value = false
  }
}
</script>
