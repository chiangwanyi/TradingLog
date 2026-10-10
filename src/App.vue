<script setup>
import { computed } from 'vue'
import { darkTheme, zhCN, dateZhCN } from 'naive-ui'
import { useAppStore } from '@/stores'
import { darkThemeOverrides, lightThemeOverrides } from '@/theme'
import NaiveApiBridge from '@/components/NaiveApiBridge.vue'

defineOptions({ name: 'App' })

const appStore = useAppStore()

/** 传入 null 表示使用 Naive UI 默认浅色主题 */
const theme = computed(() => (appStore.isDark ? darkTheme : null))

/** 按当前模式切换主题覆盖变量 */
const themeOverrides = computed(() =>
  appStore.isDark ? darkThemeOverrides : lightThemeOverrides,
)
</script>

<template>
  <!-- NConfigProvider 是全局主题 / 语言的总开关 -->
  <n-config-provider
    :theme="theme"
    :theme-overrides="themeOverrides"
    :locale="zhCN"
    :date-locale="dateZhCN"
    inline-theme-disabled
  >
    <!-- 下面四个 Provider 层层包裹业务内容，提供对应 API 的注入环境 -->
    <n-loading-bar-provider>
      <n-message-provider>
        <n-dialog-provider>
          <n-notification-provider>
            <NaiveApiBridge />
          </n-notification-provider>
        </n-dialog-provider>
      </n-message-provider>
    </n-loading-bar-provider>
  </n-config-provider>
</template>
