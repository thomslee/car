<template>
  <div style="max-width:480px;margin:0 auto;min-height:100vh;background:#F7F8FA;box-sizing:border-box;">
    <van-nav-bar
      :title="route.meta.title || '汽车档案'"
      left-arrow
      v-if="route.path !== '/'"
      @click-left="router.back()"
    />
    <router-view style="padding:12px 12px 70px;box-sizing:border-box;" />
    <van-tabbar route fixed v-if="!route.meta.hideTab">
      <van-tabbar-item replace to="/" icon="wap-home-o">车辆</van-tabbar-item>
      <van-tabbar-item replace to="/reminders" icon="bell-o">提醒</van-tabbar-item>
      <van-tabbar-item replace to="/settings" icon="setting-o">设置</van-tabbar-item>
    </van-tabbar>
  </div>
</template>

<script setup>
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()
</script>
