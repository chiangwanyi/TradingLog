<script setup>
/**
 * 图片舞台：单张图片的查看与批注绘制。
 *
 * 关键设计——坐标系
 *   批注坐标全部以「归一化值（0~1）」存储，因此这里必须精确知道图片**实际渲染区域**。
 *   做法：按图片原始宽高比在画布内做等比内缩，算出 box（left/top/width/height），
 *   再把 <img> 与批注层都贴到这个 box 上。这样缩放窗口、换分辨率都不会让批注漂移。
 *
 * 关键设计——选中 / 编辑分离
 *   selectedId 只负责「高亮」，editingId 才决定「是否弹出说明编辑框」。
 *   两者分开的原因：从批注清单点一条批注时，只应该把用户的目光引过去（高亮 + 闪烁），
 *   而不是立刻弹出编辑框打断浏览；要改内容得专门点「修改」。
 *   两个状态都由父组件持有，本组件只负责渲染与回报意图。
 *
 * 交互
 *   - 查看模式：点序号图标 = 选中并打开编辑框
 *   - 批注模式：点批注 = 单击落点；矩形批注 = 按住拖动，序号落在起点
 */
import { IconChevronLeft, IconChevronRight, IconClose } from '@/components/icons'
import {
  DEFAULT_ANNOTATION_COLOR,
  PRESET_ANNOTATION_COLORS,
  annotationColorVars,
  normalizeAnnotationColor,
} from '@/utils/color'

const props = defineProps({
  image: { type: Object, default: null },
  annotations: { type: Array, default: () => [] },
  mode: { type: String, default: 'view' }, // 'view' | 'annotate'
  tool: { type: String, default: 'point' }, // 'point' | 'rect'
  /** 当前高亮的批注（只影响观感，不弹编辑框） */
  selectedId: { type: String, default: null },
  /** 正在编辑说明的批注；null 表示编辑框关闭 */
  editingId: { type: String, default: null },
  /** 需要「呼吸闪烁」引导视线的批注 */
  pulseId: { type: String, default: null },
  /** 每次触发闪烁自增，用于强制重放动画（同一个批注连点两次也能再次闪烁） */
  pulseToken: { type: Number, default: 0 },
  /** 最近使用过的颜色，第一个会作为新建批注的默认色 */
  recentColors: { type: Array, default: () => [] },
  hasPrev: { type: Boolean, default: false },
  hasNext: { type: Boolean, default: false },
  positionLabel: { type: String, default: '' },
  loading: { type: Boolean, default: false },
})

const emit = defineEmits([
  'create',
  'select',
  'update',
  'remove',
  'prev',
  'next',
  'update:editingId',
])

// ---------------------------------------------------------------- 尺寸计算

const canvasRef = ref(null)
const canvasSize = reactive({ width: 0, height: 0 })
const box = reactive({ left: 0, top: 0, width: 0, height: 0 })

const isAnnotating = computed(() => props.mode === 'annotate')

/** 按图片宽高比在画布内等比内缩，得到图片的精确渲染矩形 */
function measure() {
  const el = canvasRef.value
  if (!el) return

  const width = el.clientWidth
  const height = el.clientHeight
  canvasSize.width = width
  canvasSize.height = height
  if (!width || !height) return

  const naturalWidth = Number(props.image?.width) || 0
  const naturalHeight = Number(props.image?.height) || 0
  if (!naturalWidth || !naturalHeight) {
    Object.assign(box, { left: 0, top: 0, width, height })
    return
  }

  const scale = Math.min(width / naturalWidth, height / naturalHeight)
  const renderedWidth = Math.max(1, naturalWidth * scale)
  const renderedHeight = Math.max(1, naturalHeight * scale)
  Object.assign(box, {
    width: renderedWidth,
    height: renderedHeight,
    left: (width - renderedWidth) / 2,
    top: (height - renderedHeight) / 2,
  })
}

/** 图片与批注层共用同一套定位，避免两者错位 */
const layerStyle = computed(() => ({
  left: `${box.left}px`,
  top: `${box.top}px`,
  width: `${box.width}px`,
  height: `${box.height}px`,
}))

let resizeObserver = null

onMounted(() => {
  measure()
  if (typeof ResizeObserver !== 'undefined' && canvasRef.value) {
    resizeObserver = new ResizeObserver(measure)
    resizeObserver.observe(canvasRef.value)
  } else {
    window.addEventListener('resize', measure)
  }
})

onBeforeUnmount(() => {
  resizeObserver?.disconnect()
  window.removeEventListener('resize', measure)
  clearTimeout(pulseTimer)
})

watch(() => props.image?.id, () => nextTick(measure))

// ---------------------------------------------------------------- 绘制交互

const drag = reactive({ active: false, startX: 0, startY: 0, x: 0, y: 0, moved: false })

const clamp01 = (value) => Math.min(1, Math.max(0, value))

/** 事件坐标 -> 归一化图片坐标（以批注层自身的矩形为基准） */
function toNormalized(event) {
  const rect = event.currentTarget.getBoundingClientRect()
  if (!rect.width || !rect.height) return { x: 0, y: 0 }
  return {
    x: clamp01((event.clientX - rect.left) / rect.width),
    y: clamp01((event.clientY - rect.top) / rect.height),
  }
}

function onPointerDown(event) {
  if (!isAnnotating.value || !props.image || event.button !== 0) return
  const { x, y } = toNormalized(event)
  drag.active = true
  drag.startX = x
  drag.startY = y
  drag.x = x
  drag.y = y
  drag.moved = false
  // 捕获指针，拖出图片区域后仍能收到 move / up
  event.currentTarget.setPointerCapture?.(event.pointerId)
}

function onPointerMove(event) {
  if (!drag.active) return
  const { x, y } = toNormalized(event)
  drag.x = x
  drag.y = y
  if (Math.abs(x - drag.startX) > 0.004 || Math.abs(y - drag.startY) > 0.004) drag.moved = true
}

const MIN_RECT = 0.012

function onPointerUp(event) {
  if (!drag.active) return
  drag.active = false

  const { x, y } = toNormalized(event)
  event.currentTarget.releasePointerCapture?.(event.pointerId)

  if (props.tool === 'point') {
    // 有明显拖动时不当作点批注，避免误落点
    if (Math.hypot(x - drag.startX, y - drag.startY) > 0.02) return
    emit('create', { kind: 'point', x, y, w: 0, h: 0 })
    return
  }

  const w = x - drag.startX
  const h = y - drag.startY
  // 太小的矩形视为误触，直接忽略
  if (Math.abs(w) < MIN_RECT || Math.abs(h) < MIN_RECT) return
  // (x, y) 就是拖拽起点，序号据此落位；w/h 带符号，向左上拖为负
  emit('create', { kind: 'rect', x: drag.startX, y: drag.startY, w, h })
}

/** 拖拽过程中的矩形预览 */
const draftRect = computed(() => {
  if (!drag.active || props.tool !== 'rect' || !drag.moved) return null
  return { x: drag.startX, y: drag.startY, w: drag.x - drag.startX, h: drag.y - drag.startY }
})

/** 下一条批注将要使用的颜色：沿用最近用过的那个，让预览与最终结果一致 */
const nextAnnotationColor = computed(() =>
  normalizeAnnotationColor(props.recentColors[0] ?? DEFAULT_ANNOTATION_COLOR),
)

function rectStyle(annotation) {
  return {
    left: `${Math.min(annotation.x, annotation.x + annotation.w) * 100}%`,
    top: `${Math.min(annotation.y, annotation.y + annotation.h) * 100}%`,
    width: `${Math.abs(annotation.w) * 100}%`,
    height: `${Math.abs(annotation.h) * 100}%`,
    ...annotationColorVars(annotation.color),
  }
}

const draftRectStyle = computed(() =>
  draftRect.value
    ? { ...rectStyle(draftRect.value), ...annotationColorVars(nextAnnotationColor.value) }
    : null,
)

function pointStyle(x, y) {
  return { left: `${x * 100}%`, top: `${y * 100}%` }
}

function markerStyle(annotation) {
  return { ...pointStyle(annotation.x, annotation.y), ...annotationColorVars(annotation.color) }
}

/** 查看模式下点击空白处取消选中；批注模式下不处理（交给绘制逻辑） */
function onOverlayClick() {
  if (isAnnotating.value) return
  emit('select', null)
  emit('update:editingId', null)
}

/** 点图片上的序号图标：既选中也打开编辑框（这是对批注的直接操作意图） */
function onMarkerClick(annotation) {
  emit('select', annotation.id)
  emit('update:editingId', annotation.id)
}

// ---------------------------------------------------------------- 序号闪烁引导

/** 单次呼吸时长，需与下面 .anno-marker.is-pulsing 的 animation 时长保持一致 */
const PULSE_DURATION = 700
/** 呼吸两次，够引导视线又不会一直闪 */
const PULSE_REPEAT = 2

const pulsingId = ref(null)
let pulseTimer = null

watch(
  () => props.pulseToken,
  () => {
    if (!props.pulseId) return
    pulsingId.value = props.pulseId
    clearTimeout(pulseTimer)
    pulseTimer = setTimeout(() => {
      pulsingId.value = null
    }, PULSE_DURATION * PULSE_REPEAT)
  },
)

/**
 * 让闪烁动画每次都能重放：
 * 把 token 混进 key，元素会重建，CSS 动画自然从头开始 ——
 * 否则同一个批注在 1.5 秒内被连点两次，class 没变化，第二次不会有任何反馈。
 */
function markerKey(annotation) {
  return pulsingId.value === annotation.id
    ? `marker-${annotation.id}-pulse-${props.pulseToken}`
    : `marker-${annotation.id}`
}

// ---------------------------------------------------------------- 说明编辑

const draftText = ref('')
const draftColor = ref(DEFAULT_ANNOTATION_COLOR)
const textInputRef = ref(null)

const editingAnnotation = computed(
  () => props.annotations.find((item) => item.id === props.editingId) ?? null,
)

const presetColors = PRESET_ANNOTATION_COLORS

function focusTextInput() {
  const input = textInputRef.value
  if (!input) return
  input.focus()
  // 光标落到末尾：编辑已有说明时可以直接续写，不必再按方向键
  const el = input.textareaElRef ?? input.inputElRef
  const end = draftText.value.length
  el?.setSelectionRange?.(end, end)
}

/**
 * 编辑框打开 / 切换目标时同步草稿。
 * 只有编辑框自己能触发聚焦，因此这里的 nextTick 不会被别处的选中操作误触发。
 */
watch(
  () => props.editingId,
  (id) => {
    const target = props.annotations.find((item) => item.id === id)
    if (!target) {
      draftText.value = ''
      draftColor.value = DEFAULT_ANNOTATION_COLOR
      return
    }
    draftText.value = target.text ?? ''
    draftColor.value = normalizeAnnotationColor(target.color)
    // 编辑框是 v-if 渲染的，要等它进 DOM 之后才能聚焦
    nextTick(focusTextInput)
  },
  { immediate: true },
)

const EDITOR_HALF_HEIGHT = 176

/** 编辑框贴着序号图标显示；靠近右/下边缘时自动翻转或夹紧，避免被裁掉 */
const editorStyle = computed(() => {
  const annotation = editingAnnotation.value
  if (!annotation || !box.width) return null

  const anchorX = box.left + annotation.x * box.width
  const anchorY = box.top + annotation.y * box.height
  const toLeft = annotation.x > 0.58
  const minY = EDITOR_HALF_HEIGHT + 10
  const maxY = Math.max(minY, canvasSize.height - EDITOR_HALF_HEIGHT - 10)
  const top = Math.min(Math.max(anchorY, minY), maxY)

  return {
    left: `${anchorX}px`,
    top: `${top}px`,
    transform: toLeft ? 'translate(calc(-100% - 18px), -50%)' : 'translate(18px, -50%)',
  }
})

function closeEditor() {
  emit('update:editingId', null)
}

function saveAnnotation() {
  const annotation = editingAnnotation.value
  if (!annotation) return
  emit('update', annotation.id, {
    text: draftText.value,
    color: normalizeAnnotationColor(draftColor.value),
  })
}

function removeEditing() {
  if (!editingAnnotation.value) return
  emit('remove', editingAnnotation.value.id)
}

defineExpose({ measure })
</script>

<template>
  <div class="stage">
    <div ref="canvasRef" class="stage__canvas" :class="{ 'is-annotating': isAnnotating }">
      <template v-if="image">
        <img
          class="stage__image"
          :src="image.url"
          :alt="image.original_name || '交易截图'"
          :style="layerStyle"
          draggable="false"
          @load="measure"
        />

        <div
          class="stage__overlay"
          :class="{ 'is-annotating': isAnnotating, 'is-drawing': drag.active && tool === 'rect' }"
          :style="layerStyle"
          @pointerdown="onPointerDown"
          @pointermove="onPointerMove"
          @pointerup="onPointerUp"
          @pointercancel="onPointerUp"
          @click="onOverlayClick"
        >
          <!-- 矩形批注 -->
          <div
            v-for="annotation in annotations"
            v-show="annotation.kind === 'rect'"
            :key="`rect-${annotation.id}`"
            class="anno-rect"
            :class="{ 'is-selected': annotation.id === selectedId }"
            :style="rectStyle(annotation)"
          />

          <!-- 绘制中的矩形预览：直接使用下一条批注将要采用的颜色 -->
          <div v-if="draftRectStyle" class="anno-rect anno-rect--draft" :style="draftRectStyle" />

          <!-- 序号图标：图集内统一编号 -->
          <button
            v-for="annotation in annotations"
            :key="markerKey(annotation)"
            type="button"
            class="anno-marker"
            :class="[
              `anno-marker--${annotation.kind}`,
              {
                'is-selected': annotation.id === selectedId,
                'is-pulsing': annotation.id === pulsingId,
              },
            ]"
            :style="markerStyle(annotation)"
            :title="annotation.text || `第 ${annotation.seq} 条批注`"
            @pointerdown.stop
            @click.stop="onMarkerClick(annotation)"
          >
            {{ annotation.seq }}
          </button>

          <!-- 起点提示点：让用户看清序号会落在哪里 -->
          <span
            v-if="draftRect"
            class="anno-origin"
            :style="{ ...pointStyle(drag.startX, drag.startY), ...annotationColorVars(nextAnnotationColor) }"
          />
        </div>

        <!-- 批注模式下的落点说明 -->
        <div v-if="isAnnotating" class="stage__hint">
          {{ tool === 'point' ? '单击图片放置点批注' : '按住左键拖动绘制矩形' }}
        </div>
      </template>

      <div v-else-if="!loading" class="stage__empty">
        <slot name="empty">这个图集还没有图片</slot>
      </div>
    </div>

    <!-- 左右切换控件 -->
    <n-button
      v-if="hasPrev"
      class="stage__nav stage__nav--prev"
      quaternary
      circle
      size="large"
      title="上一张（←）"
      @click="emit('prev')"
    >
      <template #icon>
        <component :is="IconChevronLeft" />
      </template>
    </n-button>

    <n-button
      v-if="hasNext"
      class="stage__nav stage__nav--next"
      quaternary
      circle
      size="large"
      title="下一张（→）"
      @click="emit('next')"
    >
      <template #icon>
        <component :is="IconChevronRight" />
      </template>
    </n-button>

    <div v-if="positionLabel" class="stage__position">{{ positionLabel }}</div>

    <!-- 批注说明编辑框 -->
    <div v-if="editorStyle" class="anno-editor" :style="editorStyle" @click.stop>
      <div class="anno-editor__head">
        <span class="anno-editor__badge" :style="annotationColorVars(draftColor)">
          {{ editingAnnotation.seq }}
        </span>
        <span class="anno-editor__kind">
          {{ editingAnnotation.kind === 'point' ? '点批注' : '矩形批注' }}
        </span>
        <n-button quaternary circle size="tiny" title="关闭" @click="closeEditor">
          <template #icon>
            <component :is="IconClose" />
          </template>
        </n-button>
      </div>

      <n-input
        ref="textInputRef"
        v-model:value="draftText"
        type="textarea"
        size="small"
        placeholder="补充说明，例如：这里放量突破"
        :autosize="{ minRows: 3, maxRows: 6 }"
      />

      <!-- 颜色：预设色盘 + 最近使用 + 自定义取色 -->
      <div class="anno-editor__colors">
        <div class="anno-editor__colors-head">
          <span>颜色</span>
          <n-color-picker
            v-model:value="draftColor"
            class="anno-editor__picker"
            size="small"
            :modes="['hex']"
            :show-alpha="false"
            :swatches="presetColors"
          />
        </div>

        <div class="anno-swatches">
          <button
            v-for="color in presetColors"
            :key="color"
            type="button"
            class="anno-swatch"
            :class="{ 'is-active': color === draftColor }"
            :style="{ background: color }"
            :title="color"
            @click="draftColor = color"
          />
        </div>

        <template v-if="recentColors.length">
          <div class="anno-editor__colors-head anno-editor__colors-head--sub">
            <span>最近使用</span>
          </div>
          <div class="anno-swatches">
            <button
              v-for="color in recentColors"
              :key="`recent-${color}`"
              type="button"
              class="anno-swatch"
              :class="{ 'is-active': color === draftColor }"
              :style="{ background: color }"
              :title="color"
              @click="draftColor = color"
            />
          </div>
        </template>
      </div>

      <div class="anno-editor__foot">
        <n-button size="small" type="primary" @click="saveAnnotation">保存</n-button>
        <n-button size="small" quaternary @click="closeEditor">取消</n-button>
        <n-button size="small" quaternary type="error" @click="removeEditing">删除</n-button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.stage {
  position: relative;
  flex: 1 1 auto;
  min-height: 0;
  border-radius: 12px;
  background: var(--tl-board);
  overflow: hidden;
}

.stage__canvas {
  position: absolute;
  inset: 0;
  overflow: hidden;
}

.stage__canvas.is-annotating {
  cursor: crosshair;
}

.stage__image,
.stage__overlay {
  position: absolute;
  /* object-fit: contain 保证图片绝不被拉伸变形；正常情况图片正好铺满 overlay */
  object-fit: contain;
  user-select: none;
}

.stage__overlay {
  touch-action: none;
}

.stage__overlay.is-drawing {
  cursor: crosshair;
}

.stage__empty {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: var(--tl-text-muted);
  font-size: 14px;
}

.stage__hint {
  position: absolute;
  top: 12px;
  left: 50%;
  transform: translateX(-50%);
  padding: 5px 12px;
  border-radius: 999px;
  background: rgba(0, 0, 0, 0.6);
  color: #fff;
  font-size: 12px;
  pointer-events: none;
}

.stage__position {
  position: absolute;
  right: 12px;
  bottom: 10px;
  padding: 3px 10px;
  border-radius: 999px;
  background: rgba(0, 0, 0, 0.55);
  color: #fff;
  font-size: 12px;
  pointer-events: none;
}

.stage__nav {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  z-index: 3;
  background: rgba(0, 0, 0, 0.42) !important;
  color: #fff !important;
  backdrop-filter: blur(2px);
}

.stage__nav--prev {
  left: 12px;
}

.stage__nav--next {
  right: 12px;
}

/* ---------------------------------------------------------------- 批注图形 */

/* 每个批注的颜色通过内联 --anno-color 系列变量下发，
   这里只提供兜底值，让样式不依赖 JS 也能成立 */
.anno-rect {
  position: absolute;
  border: 2px solid var(--anno-color, var(--anno-accent));
  border-radius: 3px;
  background: var(--anno-color-soft, var(--anno-accent-soft));
  box-shadow: 0 0 0 1px rgba(0, 0, 0, 0.35);
  pointer-events: none;
}

.anno-rect.is-selected {
  border-width: 3px;
  background: var(--anno-color-strong, var(--anno-accent-soft-strong));
}

.anno-rect--draft {
  border-style: dashed;
}

.anno-marker {
  position: absolute;
  z-index: 2;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  padding: 0;
  transform: translate(-50%, -50%);
  border: 2px solid #fff;
  border-radius: 50%;
  background: var(--anno-color, var(--anno-accent));
  color: var(--anno-color-on, #fff);
  font-size: 12px;
  font-weight: 700;
  line-height: 1;
  cursor: pointer;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.45);
  transition:
    transform 0.15s ease,
    box-shadow 0.15s ease;
}

.anno-marker:hover {
  transform: translate(-50%, -50%) scale(1.15);
}

.anno-marker.is-selected {
  box-shadow:
    0 0 0 3px var(--anno-color-ring, var(--anno-accent-ring)),
    0 2px 8px rgba(0, 0, 0, 0.5);
  transform: translate(-50%, -50%) scale(1.15);
}

/* 从批注清单点过来时的引导动效：呼吸两次后自动停 */
.anno-marker.is-pulsing {
  z-index: 4;
  animation: anno-pulse 0.7s ease-out 2;
}

@keyframes anno-pulse {
  0% {
    transform: translate(-50%, -50%) scale(1);
    box-shadow: 0 0 0 0 var(--anno-color-ring, var(--anno-accent-ring));
  }

  60% {
    transform: translate(-50%, -50%) scale(1.45);
    box-shadow: 0 0 0 10px transparent;
  }

  100% {
    transform: translate(-50%, -50%) scale(1);
    box-shadow: 0 0 0 0 transparent;
  }
}

/* 矩形批注的序号用方形，与点批注一眼区分 */
.anno-marker--rect {
  border-radius: 6px;
}

.anno-origin {
  position: absolute;
  width: 8px;
  height: 8px;
  transform: translate(-50%, -50%);
  border-radius: 50%;
  background: #fff;
  box-shadow: 0 0 0 2px var(--anno-color, var(--anno-accent));
  pointer-events: none;
}

/* ---------------------------------------------------------------- 说明编辑框 */

.anno-editor {
  position: absolute;
  z-index: 5;
  display: flex;
  flex-direction: column;
  gap: 8px;
  width: 292px;
  padding: 10px 12px 12px;
  border: 1px solid var(--tl-surface-border);
  border-radius: 10px;
  background: var(--tl-surface);
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.28);
}

.anno-editor__head {
  display: flex;
  align-items: center;
  gap: 8px;
}

.anno-editor__badge {
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 22px;
  height: 22px;
  padding: 0 6px;
  border-radius: 6px;
  background: var(--anno-color, var(--anno-accent));
  color: var(--anno-color-on, #fff);
  font-size: 12px;
  font-weight: 700;
}

.anno-editor__kind {
  flex: 1 1 auto;
  color: var(--tl-text-dim);
  font-size: 12px;
}

.anno-editor__colors {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding-top: 2px;
}

.anno-editor__colors-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  color: var(--tl-text-dim);
  font-size: 12px;
}

.anno-editor__colors-head--sub {
  margin-top: 2px;
}

.anno-editor__picker {
  width: 96px;
}

.anno-swatches {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.anno-swatch {
  width: 18px;
  height: 18px;
  padding: 0;
  border: 1px solid rgba(128, 128, 128, 0.45);
  border-radius: 50%;
  cursor: pointer;
  transition:
    transform 0.12s ease,
    box-shadow 0.12s ease;
}

.anno-swatch:hover {
  transform: scale(1.14);
}

.anno-swatch.is-active {
  box-shadow:
    0 0 0 2px var(--tl-surface),
    0 0 0 3px var(--brand-primary);
}

.anno-editor__foot {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 2px;
}

.anno-editor__foot > :last-child {
  margin-left: auto;
}
</style>
