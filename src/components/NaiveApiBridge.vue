<script setup>
import { useDialog, useLoadingBar, useMessage, useNotification } from 'naive-ui'
import { registerNaiveApi } from '@/utils/naive'

/**
 * 该组件位于所有 Naive UI Provider 内部，
 * 因此可以在这里调用 useXxx() 并把实例注册到全局，供非组件环境复用。
 */
defineOptions({ name: 'NaiveApiBridge' })

registerNaiveApi({
  message: useMessage(),
  dialog: useDialog(),
  notification: useNotification(),
  loadingBar: useLoadingBar(),
})
</script>

<template>
  <router-view />
</template>
