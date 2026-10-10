<script setup>
defineOptions({ name: 'HomeView' })
</script>

<template>
  <div class="page">
    <div class="page__head">
      <h2 class="page__title">首页</h2>
      <p class="page__desc">项目已完成初始化，可在此基础上开发业务功能。</p>
    </div>

    <n-card :bordered="false">
      <n-empty description="暂无内容">
        <template #extra>
          <n-text depth="3" style="font-size: 12px">
            编辑 src/views/HomeView.vue 开始开发
          </n-text>
        </template>
      </n-empty>
    </n-card>
  </div>
</template>
