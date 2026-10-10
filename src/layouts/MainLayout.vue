<script setup>
import { computed, h } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAppStore } from '@/stores'
import { menuRoutes } from '@/router/routes'
import {
  IconAlbum,
  IconDashboard,
  IconMenu,
  IconMoon,
  IconSun,
} from '@/components/icons'

defineOptions({ name: 'MainLayout' })

const route = useRoute()
const router = useRouter()
const appStore = useAppStore()

/** 图标名 -> 组件映射，便于用配置驱动菜单 */
const iconMap = {
  dashboard: IconDashboard,
  album: IconAlbum,
}

/** NMenu 的 options 结构 */
const menuOptions = menuRoutes.map((item) => ({
  key: item.key,
  label: item.label,
  icon: () => h(iconMap[item.icon] ?? IconDashboard),
}))

/** 当前高亮项与路由保持一致；详情页用 meta.activeMenu 指回父级菜单 */
const activeKey = computed(() => route.meta?.activeMenu ?? route.path)

/** 详情页在面包屑前插一条可点击的父级 */
const parent = computed(() => route.meta?.parent ?? null)

function handleMenuSelect(key) {
  if (key !== route.path) router.push(key)
}
</script>

<template>
  <n-layout has-sider position="absolute">
    <!-- 侧边栏 -->
    <n-layout-sider
      bordered
      collapse-mode="width"
      :width="224"
      :collapsed-width="64"
      :collapsed="appStore.siderCollapsed"
      show-trigger="bar"
      @collapse="appStore.setSiderCollapsed(true)"
      @expand="appStore.setSiderCollapsed(false)"
    >
      <div class="app-logo">
        <div class="app-logo__mark">T</div>
        <transition name="fade">
          <span v-show="!appStore.siderCollapsed" class="app-logo__text">TradingLog</span>
        </transition>
      </div>

      <n-menu
        :value="activeKey"
        :options="menuOptions"
        :collapsed="appStore.siderCollapsed"
        :collapsed-width="64"
        :collapsed-icon-size="20"
        :indent="18"
        @update:value="handleMenuSelect"
      />
    </n-layout-sider>

    <!-- 主区域 -->
    <n-layout>
      <n-layout-header bordered class="app-header">
        <div class="app-header__left">
          <n-button quaternary circle title="折叠 / 展开侧边栏" @click="appStore.toggleSider">
            <template #icon>
              <component :is="IconMenu" />
            </template>
          </n-button>

          <n-breadcrumb>
            <n-breadcrumb-item v-if="parent" @click="router.push(parent.path)">
              <span class="app-breadcrumb__link">{{ parent.title }}</span>
            </n-breadcrumb-item>
            <n-breadcrumb-item>{{ route.meta?.title ?? '页面' }}</n-breadcrumb-item>
          </n-breadcrumb>
        </div>

        <div class="app-header__right">
          <n-button
            quaternary
            circle
            :title="`切换到${appStore.isDark ? '浅色' : '深色'}模式`"
            @click="appStore.toggleTheme"
          >
            <template #icon>
              <component :is="appStore.isDark ? IconSun : IconMoon" />
            </template>
          </n-button>
        </div>
      </n-layout-header>

      <!-- 页面内容：带路由切换过渡 -->
      <n-layout-content content-style="padding: 20px 24px 36px;" :native-scrollbar="false">
        <router-view v-slot="{ Component, route: current }">
          <transition name="fade-slide" mode="out-in">
            <component :is="Component" :key="current.path" />
          </transition>
        </router-view>
      </n-layout-content>
    </n-layout>
  </n-layout>
</template>

<style scoped>
.app-logo {
  display: flex;
  align-items: center;
  gap: 10px;
  height: 60px;
  padding: 0 20px;
  overflow: hidden;
  white-space: nowrap;
}

.app-logo__mark {
  display: flex;
  flex: 0 0 auto;
  align-items: center;
  justify-content: center;
  width: 30px;
  height: 30px;
  border-radius: 9px;
  background: linear-gradient(135deg, #2f6fed, #6aa2ff);
  color: #fff;
  font-size: 16px;
  font-weight: 700;
  box-shadow: 0 4px 12px rgba(47, 111, 237, 0.32);
}

.app-logo__text {
  font-size: 16px;
  font-weight: 600;
  letter-spacing: 0.2px;
}

.app-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  height: 60px;
  padding: 0 20px;
}

.app-header__left,
.app-header__right {
  display: flex;
  align-items: center;
  gap: 10px;
}

.app-breadcrumb__link {
  cursor: pointer;
  transition: color 0.2s;
}

.app-breadcrumb__link:hover {
  color: var(--brand-primary);
}
</style>
