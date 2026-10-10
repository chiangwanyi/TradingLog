<script setup>
import { useRouter } from 'vue-router'

defineOptions({ name: 'NotFoundView' })

const router = useRouter()
</script>

<template>
  <div class="notfound">
    <n-result
      status="404"
      title="404 页面走丢了"
      description="你访问的地址不存在，或者已经被移动到别处。"
    >
      <template #footer>
        <n-space justify="center">
          <n-button type="primary" @click="router.push('/home')">返回首页</n-button>
          <n-button quaternary @click="router.back()">返回上一页</n-button>
        </n-space>
      </template>
    </n-result>
  </div>
</template>

<style scoped>
.notfound {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  padding: 24px;
}
</style>
