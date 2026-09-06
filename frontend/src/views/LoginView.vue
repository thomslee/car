<template>
  <div style="min-height:100vh;display:flex;flex-direction:column;justify-content:center;padding:32px;box-sizing:border-box;background:#F7F8FA;">
    <div style="text-align:center;margin-bottom:32px;">
      <div style="font-size:28px;font-weight:700;color:#1989fa;">汽车档案</div>
      <div style="font-size:13px;color:#969799;margin-top:8px;">爱车的全生命周期管家</div>
    </div>
    <van-form @submit="onSubmit">
      <van-cell-group inset>
        <van-field v-model="username" name="username" label="用户名" placeholder="请输入用户名"
                   :rules="[{ required: true, message: '请输入用户名' }]" />
        <van-field v-model="password" type="password" name="password" label="密码" placeholder="请输入密码"
                   :rules="[{ required: true, message: '请输入密码' }]" />
      </van-cell-group>
      <div style="margin:24px 16px;">
        <van-button round block type="primary" native-type="submit" :loading="loading">登 录</van-button>
      </div>
      <div style="text-align:center;font-size:12px;color:#969799;margin-top:-8px;">
        账号由管理员创建，如无账号请联系管理员
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
const password = ref('')
const loading = ref(false)

async function onSubmit() {
  loading.value = true
  try {
    await auth.login(username.value, password.value)
    showSuccessToast('登录成功')
    router.push('/')
  } catch (e) {
    showFailToast(e.message)
  } finally {
    loading.value = false
  }
}
</script>
