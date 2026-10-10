<script setup>
/**
 * 图片预览缩略图条。
 *
 * 类图片查看器的底部胶片：横向排列、可滚动、点击切换，
 * 当前项自动滚动到可视区域中间，并显示该图的批注数量。
 */
const props = defineProps({
  images: { type: Array, default: () => [] },
  currentIndex: { type: Number, default: 0 },
  /** { [imageId]: number } —— 每张图上的批注数量 */
  annotationCounts: { type: Object, default: () => ({}) },
})

const emit = defineEmits(['select'])

const stripRef = ref(null)

/** 切换图片后把当前缩略图滚进视野 */
async function scrollActiveIntoView() {
  await nextTick()
  const active = stripRef.value?.querySelector('.thumb.is-active')
  active?.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' })
}

watch(() => props.currentIndex, scrollActiveIntoView)

function countOf(image) {
  return props.annotationCounts[image.id] ?? 0
}
</script>

<template>
  <div v-if="images.length" class="strip">
    <div ref="stripRef" class="strip__track">
      <button
        v-for="(image, index) in images"
        :key="image.id"
        type="button"
        class="thumb"
        :class="{ 'is-active': index === currentIndex }"
        :title="`第 ${index + 1} 张 · ${image.original_name || '截图'}`"
        @click="emit('select', index)"
      >
        <img class="thumb__img" :src="image.thumb_url" :alt="image.original_name || ''" />

        <span class="thumb__index">{{ index + 1 }}</span>

        <span v-if="countOf(image)" class="thumb__count" :title="`${countOf(image)} 条批注`">
          {{ countOf(image) }}
        </span>
      </button>
    </div>

    <div class="strip__meta">{{ currentIndex + 1 }} / {{ images.length }}</div>
  </div>
</template>

<style scoped>
.strip {
  position: relative;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  border: 1px solid var(--tl-surface-border);
  border-radius: 12px;
  background: var(--tl-surface);
}

.strip__track {
  display: flex;
  flex: 1 1 auto;
  gap: 8px;
  overflow-x: auto;
  padding: 4px 2px;
  scrollbar-width: thin;
}

.thumb {
  position: relative;
  flex: 0 0 auto;
  width: 96px;
  height: 62px;
  padding: 0;
  overflow: hidden;
  border: 2px solid transparent;
  border-radius: 8px;
  background: var(--tl-board);
  cursor: pointer;
  transition:
    border-color 0.2s ease,
    transform 0.2s ease;
}

.thumb:hover {
  transform: translateY(-2px);
  border-color: var(--anno-accent-ring);
}

.thumb.is-active {
  border-color: var(--anno-accent);
  box-shadow: 0 0 0 2px var(--anno-accent-ring);
}

.thumb__img {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: cover;
  /* 缩略图本身可能带透明区域，统一铺白底，深浅主题下观感一致 */
  background: #fff;
}

.thumb__index {
  position: absolute;
  left: 4px;
  bottom: 3px;
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 16px;
  height: 16px;
  padding: 0 4px;
  border-radius: 4px;
  background: rgba(0, 0, 0, 0.62);
  color: #fff;
  font-size: 11px;
  font-weight: 600;
  line-height: 1;
}

.thumb__count {
  position: absolute;
  right: 4px;
  top: 3px;
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 16px;
  height: 16px;
  padding: 0 4px;
  border: 1px solid #fff;
  border-radius: 999px;
  background: var(--anno-accent);
  color: #fff;
  font-size: 11px;
  font-weight: 700;
  line-height: 1;
}

.strip__meta {
  flex: 0 0 auto;
  color: var(--tl-text-muted);
  font-size: 12px;
  font-variant-numeric: tabular-nums;
}
</style>
