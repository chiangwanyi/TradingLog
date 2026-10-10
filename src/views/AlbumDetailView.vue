<script setup>
/**
 * 图集详情：图片浏览（左右切换 + 缩略图条）、图片上传（文件选择 / 剪贴板粘贴 / 拖拽）、
 * 以及查看模式与批注模式的切换。
 *
 * 数据组织：整个图集的图片与批注一次性拉取（GET /albums/{id} 返回嵌套结构），
 * 之后的新增 / 修改都做局部更新，避免每加一条批注就整页重载。
 */
import AlbumFormDialog from '@/components/album/AlbumFormDialog.vue'
import ImageStage from '@/components/album/ImageStage.vue'
import ThumbnailStrip from '@/components/album/ThumbnailStrip.vue'
import {
  IconArrowLeft,
  IconClipboard,
  IconClose,
  IconEdit,
  IconEye,
  IconList,
  IconPen,
  IconPoint,
  IconRect,
  IconTrash,
  IconUpload,
} from '@/components/icons'
import { albumApi } from '@/api'
import { formatDateTime } from '@/utils/datetime'

defineOptions({ name: 'AlbumDetailView' })

const route = useRoute()
const router = useRouter()
const message = useMessage()
const dialog = useDialog()

const albumId = computed(() => route.params.albumId)

const album = ref(null)
const loading = ref(false)
const uploading = ref(false)

const currentIndex = ref(0)
/** 'view' 只做浏览与查看说明；'annotate' 才能绘制新批注 */
const mode = ref('view')
/** 'point' 单击落点；'rect' 拖拽画框 */
const tool = ref('point')
const selectedId = ref(null)

const panelVisible = ref(true)
const editVisible = ref(false)
const submitting = ref(false)

const fileInputRef = ref(null)
const dragDepth = ref(0)
const dragging = computed(() => dragDepth.value > 0)

/**
 * 统一图片对象的结构。
 * 图片可能来自「图集详情」或「上传接口」，两者的 `annotations` 字段必须都存在 ——
 * 否则追加图片后立刻画批注时，`image.annotations.push(...)` 会抛
 * `Cannot read properties of undefined (reading 'push')`。
 */
function normalizeImage(image) {
  return { ...image, annotations: Array.isArray(image.annotations) ? image.annotations : [] }
}

// ---------------------------------------------------------------- 派生数据

const images = computed(() => album.value?.images ?? [])
const currentImage = computed(() => images.value[currentIndex.value] ?? null)
const currentAnnotations = computed(() => currentImage.value?.annotations ?? [])

const totalAnnotations = computed(() =>
  images.value.reduce((sum, image) => sum + (image.annotations?.length ?? 0), 0),
)

const annotationCounts = computed(() => {
  const counts = {}
  for (const image of images.value) counts[image.id] = image.annotations?.length ?? 0
  return counts
})

/** 全册批注按序号拉平，用于右侧清单（序号跨图片统一编号，因此可以直接排成一条线） */
const annotationList = computed(() =>
  images.value
    .flatMap((image, imageIndex) =>
      (image.annotations ?? []).map((annotation) => ({ ...annotation, imageIndex })),
    )
    .sort((a, b) => a.seq - b.seq),
)

// ---------------------------------------------------------------- 加载

async function load() {
  loading.value = true
  try {
    const detail = await albumApi.fetchAlbum(albumId.value)
    // 归一化一次，后续所有局部更新都建立在「images[].annotations 一定存在」之上
    album.value = { ...detail, images: (detail.images ?? []).map(normalizeImage) }
    if (currentIndex.value > images.value.length - 1) {
      currentIndex.value = Math.max(0, images.value.length - 1)
    }
  } catch (error) {
    message.error(error.message)
    router.replace('/albums')
  } finally {
    loading.value = false
  }
}

watch(
  albumId,
  () => {
    currentIndex.value = 0
    selectedId.value = null
    mode.value = 'view'
    load()
  },
  { immediate: true },
)

// ---------------------------------------------------------------- 浏览

function goTo(index) {
  if (index < 0 || index >= images.value.length || index === currentIndex.value) return
  currentIndex.value = index
  selectedId.value = null
}

const prev = () => goTo(currentIndex.value - 1)
const next = () => goTo(currentIndex.value + 1)

/** 从批注清单跳到某条批注：切到它所在的图片并选中 */
function focusAnnotation(item) {
  currentIndex.value = item.imageIndex
  selectedId.value = item.id
}

function onKeydown(event) {
  const target = event.target
  if (target?.tagName === 'INPUT' || target?.tagName === 'TEXTAREA' || target?.isContentEditable) {
    if (event.key === 'Escape') target.blur()
    return
  }
  if (event.key === 'ArrowLeft') {
    event.preventDefault()
    prev()
  } else if (event.key === 'ArrowRight') {
    event.preventDefault()
    next()
  } else if (event.key === 'Escape') {
    selectedId.value = null
  }
}

// ---------------------------------------------------------------- 上传

async function upload(fileList) {
  const files = Array.from(fileList ?? []).filter((file) => file?.type?.startsWith('image/'))
  if (!album.value || !files.length) return

  uploading.value = true
  try {
    const result = await albumApi.uploadImages(albumId.value, files)
    const firstNewIndex = images.value.length

    if (result.saved.length) {
      // 新图片的上传时间必然晚于已有图片，直接追加即可维持「按上传时间排序」。
      // 归一化 annotations：后端返回的图片对象必须与图集详情里的结构一致，
      // 这里再兜一次底，避免字段缺失导致后续 push 批注时抛 undefined。
      images.value.push(...result.saved.map(normalizeImage))
      album.value.image_count = images.value.length
      currentIndex.value = firstNewIndex
      selectedId.value = null
      message.success(`已添加 ${result.saved.length} 张截图`)
    }

    // 批量上传时单个文件失败不影响其它文件，这里逐条提示原因
    for (const failure of result.failed) {
      message.error(`${failure.name}：${failure.reason}`)
    }
  } catch (error) {
    message.error(error.message)
  } finally {
    uploading.value = false
    if (fileInputRef.value) fileInputRef.value.value = ''
  }
}

function onFilePicked(event) {
  upload(event.target.files)
}

/** 剪贴板粘贴：截图后直接 Ctrl+V 即可入库 */
function onPaste(event) {
  const target = event.target
  // 正在输入框里打字时不要抢粘贴
  if (target?.tagName === 'INPUT' || target?.tagName === 'TEXTAREA' || target?.isContentEditable) {
    return
  }
  const files = Array.from(event.clipboardData?.items ?? [])
    .filter((item) => item.kind === 'file' && item.type.startsWith('image/'))
    .map((item) => item.getAsFile())
    .filter(Boolean)

  if (!files.length) return
  event.preventDefault()
  upload(files)
}

function onDragEnter() {
  dragDepth.value += 1
}

function onDragLeave() {
  dragDepth.value = Math.max(0, dragDepth.value - 1)
}

function onDrop(event) {
  dragDepth.value = 0
  upload(event.dataTransfer?.files)
}

// ---------------------------------------------------------------- 图片删除

function confirmDeleteImage() {
  const image = currentImage.value
  if (!image) return

  dialog.warning({
    title: '删除这张截图',
    content: `将同时删除它上面的 ${image.annotations?.length ?? 0} 条批注，并重排其余批注的序号。`,
    positiveText: '删除',
    negativeText: '取消',
    onPositiveClick: async () => {
      const index = currentIndex.value
      try {
        await albumApi.deleteImage(image.id)
        // 序号在服务端已压实，重新拉一次保证与后端完全一致
        await load()
        currentIndex.value = Math.min(index, Math.max(0, images.value.length - 1))
        selectedId.value = null
        message.success('截图已删除')
      } catch (error) {
        message.error(error.message)
      }
    },
  })
}

// ---------------------------------------------------------------- 批注

function findAnnotation(id) {
  for (const image of images.value) {
    const found = (image.annotations ?? []).find((item) => item.id === id)
    if (found) return found
  }
  return null
}

async function handleCreate(payload) {
  const image = currentImage.value
  if (!image) return
  try {
    const created = await albumApi.createAnnotation(albumId.value, {
      image_id: image.id,
      ...payload,
    })
    // 按 id 重新定位：等待接口返回期间用户可能已经切换了图片
    const target = images.value.find((item) => item.id === image.id)
    if (!target) return
    if (!Array.isArray(target.annotations)) target.annotations = []
    target.annotations.push(created)
    // 选中新批注，ImageStage 会随即弹出说明编辑框
    selectedId.value = created.id
  } catch (error) {
    message.error(error.message)
  }
}

async function handleUpdateText(id, text) {
  try {
    const updated = await albumApi.updateAnnotation(id, { text })
    const target = findAnnotation(id)
    if (target) Object.assign(target, updated)
    message.success('批注已保存')
  } catch (error) {
    message.error(error.message)
  }
}

function handleRemove(id) {
  dialog.warning({
    title: '删除批注',
    content: '删除后本图集内其余批注的序号会自动重排，确定删除吗？',
    positiveText: '删除',
    negativeText: '取消',
    onPositiveClick: async () => {
      try {
        await albumApi.deleteAnnotation(id)
        // 与后端保持一致：删完把整册序号压实为 1..N
        removeAndRenumber(id)
        message.success('批注已删除')
      } catch (error) {
        message.error(error.message)
      }
    },
  })
}

function removeAndRenumber(removedId) {
  const kept = []
  images.value.forEach((image, imageIndex) => {
    for (const annotation of image.annotations ?? []) {
      if (annotation.id !== removedId) kept.push({ annotation, imageIndex })
    }
  })
  kept.sort((a, b) => a.annotation.seq - b.annotation.seq)

  for (const image of images.value) image.annotations = []
  kept.forEach(({ annotation, imageIndex }, position) => {
    annotation.seq = position + 1
    images.value[imageIndex].annotations.push(annotation)
  })
}

// ---------------------------------------------------------------- 图集本身

async function handleAlbumSubmit(payload) {
  submitting.value = true
  try {
    const updated = await albumApi.updateAlbum(albumId.value, payload)
    // 修改接口只返回图集本身，图片与批注沿用现有数据
    album.value = { ...updated, images: album.value.images }
    editVisible.value = false
    message.success('图集已更新')
  } catch (error) {
    message.error(error.message)
  } finally {
    submitting.value = false
  }
}

function confirmDeleteAlbum() {
  dialog.warning({
    title: '删除图集',
    content: `确定删除「${album.value?.symbol}」及其 ${images.value.length} 张截图和全部批注吗？该操作不可恢复。`,
    positiveText: '删除',
    negativeText: '取消',
    onPositiveClick: async () => {
      try {
        await albumApi.deleteAlbum(albumId.value)
        message.success('图集已删除')
        router.push('/albums')
      } catch (error) {
        message.error(error.message)
      }
    },
  })
}

// ---------------------------------------------------------------- 生命周期

onMounted(() => {
  window.addEventListener('paste', onPaste)
  window.addEventListener('keydown', onKeydown)
})

onBeforeUnmount(() => {
  window.removeEventListener('paste', onPaste)
  window.removeEventListener('keydown', onKeydown)
})
</script>

<template>
  <div
    class="detail"
    @dragover.prevent
    @dragenter.prevent="onDragEnter"
    @dragleave="onDragLeave"
    @drop.prevent="onDrop"
  >
    <!-- 顶部工具条 -->
    <div class="detail__bar">
      <div class="detail__bar-left">
        <n-button quaternary circle title="返回相册列表" @click="router.push('/albums')">
          <template #icon>
            <component :is="IconArrowLeft" />
          </template>
        </n-button>

        <div class="detail__heading">
          <div class="detail__symbol">{{ album?.symbol ?? '加载中…' }}</div>
          <div class="detail__meta">
            {{ formatDateTime(album?.trade_time) }} · {{ images.length }} 张截图 ·
            {{ totalAnnotations }} 条批注
            <span v-if="album?.title"> · {{ album.title }}</span>
          </div>
        </div>
      </div>

      <div class="detail__bar-right">
        <n-radio-group v-model:value="mode" size="small">
          <n-radio-button value="view">
            <span class="toolbar-label">
              <component :is="IconEye" />
              查看
            </span>
          </n-radio-button>
          <n-radio-button value="annotate">
            <span class="toolbar-label">
              <component :is="IconPen" />
              批注
            </span>
          </n-radio-button>
        </n-radio-group>

        <n-radio-group v-if="mode === 'annotate'" v-model:value="tool" size="small">
          <n-radio-button value="point">
            <span class="toolbar-label">
              <component :is="IconPoint" />
              点批注
            </span>
          </n-radio-button>
          <n-radio-button value="rect">
            <span class="toolbar-label">
              <component :is="IconRect" />
              矩形批注
            </span>
          </n-radio-button>
        </n-radio-group>

        <n-divider vertical />

        <n-button size="small" :loading="uploading" :disabled="!album" @click="fileInputRef.click()">
          <template #icon>
            <component :is="IconUpload" />
          </template>
          添加截图
        </n-button>

        <n-button
          size="small"
          quaternary
          :type="panelVisible ? 'primary' : 'default'"
          title="显示 / 隐藏批注清单"
          @click="panelVisible = !panelVisible"
        >
          <template #icon>
            <component :is="IconList" />
          </template>
        </n-button>

        <n-button size="small" quaternary title="编辑图集信息" @click="editVisible = true">
          <template #icon>
            <component :is="IconEdit" />
          </template>
        </n-button>

        <n-button size="small" quaternary title="删除这张截图" :disabled="!currentImage" @click="confirmDeleteImage">
          <template #icon>
            <component :is="IconTrash" />
          </template>
        </n-button>

        <n-button size="small" quaternary type="error" title="删除整个图集" @click="confirmDeleteAlbum">
          <template #icon>
            <component :is="IconClose" />
          </template>
        </n-button>
      </div>
    </div>

    <!-- 主体 -->
    <div class="detail__body">
      <div class="detail__main">
        <ImageStage
          :image="currentImage"
          :annotations="currentAnnotations"
          :mode="mode"
          :tool="tool"
          :selected-id="selectedId"
          :has-prev="currentIndex > 0"
          :has-next="currentIndex < images.length - 1"
          :position-label="images.length ? `${currentIndex + 1} / ${images.length}` : ''"
          :loading="loading"
          @create="handleCreate"
          @select="selectedId = $event"
          @update-text="handleUpdateText"
          @remove="handleRemove"
          @prev="prev"
          @next="next"
        >
          <template #empty>
            <div class="stage-empty">
              <component :is="IconClipboard" />
              <p>这个图集还没有截图</p>
              <p class="stage-empty__hint">
                点右上角「添加截图」选择文件，或截图后直接 Ctrl&nbsp;+&nbsp;V 粘贴，也可以把图片拖进来
              </p>
            </div>
          </template>
        </ImageStage>

        <ThumbnailStrip
          :images="images"
          :current-index="currentIndex"
          :annotation-counts="annotationCounts"
          @select="goTo"
        />

        <input
          ref="fileInputRef"
          class="hidden-input"
          type="file"
          accept="image/*"
          multiple
          @change="onFilePicked"
        />
      </div>

      <!-- 批注清单 -->
      <aside v-show="panelVisible" class="detail__aside">
        <div class="aside__head">
          <span>批注清单</span>
          <n-button quaternary circle size="tiny" title="收起" @click="panelVisible = false">
            <template #icon>
              <component :is="IconClose" />
            </template>
          </n-button>
        </div>
        <p class="aside__hint">序号在同一图集内跨所有图片统一编号</p>

        <n-scrollbar class="aside__scroll">
          <n-empty
            v-if="!annotationList.length"
            size="small"
            description="还没有批注，切到「批注」模式试试"
            style="padding: 32px 0"
          />

          <button
            v-for="item in annotationList"
            :key="item.id"
            type="button"
            class="anno-item"
            :class="{ 'is-active': item.id === selectedId }"
            @click="focusAnnotation(item)"
          >
            <span class="anno-item__seq">{{ item.seq }}</span>
            <span class="anno-item__body">
              <span class="anno-item__text" :class="{ 'is-empty': !item.text }">
                {{ item.text || '（未填写说明）' }}
              </span>
              <span class="anno-item__meta">
                第 {{ item.imageIndex + 1 }} 张 ·
                {{ item.kind === 'point' ? '点批注' : '矩形批注' }}
              </span>
            </span>
          </button>
        </n-scrollbar>
      </aside>
    </div>

    <!-- 拖拽上传提示 -->
    <div v-if="dragging" class="detail__dropmask">
      <component :is="IconUpload" />
      <span>松开即可添加到本图集</span>
    </div>

    <AlbumFormDialog
      v-model:show="editVisible"
      :album="album"
      :submitting="submitting"
      @submit="handleAlbumSubmit"
    />
  </div>
</template>

<style scoped>
.detail {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 12px;
  /* 60px 顶栏 + 上下内边距，让查看器正好铺满一屏 */
  height: calc(100vh - 116px);
  min-height: 520px;
}

.detail__bar {
  display: flex;
  flex: 0 0 auto;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
}

.detail__bar-left {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.detail__bar-right {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.detail__heading {
  min-width: 0;
}

.detail__symbol {
  overflow: hidden;
  font-size: 16px;
  font-weight: 600;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.detail__meta {
  margin-top: 2px;
  color: var(--tl-text-muted);
  font-size: 12px;
  font-variant-numeric: tabular-nums;
}

.toolbar-label {
  display: inline-flex;
  align-items: center;
  gap: 5px;
}

.detail__body {
  display: flex;
  flex: 1 1 auto;
  gap: 14px;
  min-height: 0;
}

.detail__main {
  display: flex;
  flex: 1 1 auto;
  flex-direction: column;
  gap: 12px;
  min-width: 0;
  min-height: 0;
}

/* ---------------------------------------------------------------- 批注清单 */

.detail__aside {
  display: flex;
  flex: 0 0 268px;
  flex-direction: column;
  width: 268px;
  overflow: hidden;
  border: 1px solid var(--tl-surface-border);
  border-radius: 12px;
  background: var(--tl-surface);
}

.aside__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 8px 10px 14px;
  font-size: 13px;
  font-weight: 600;
}

.aside__hint {
  margin: 0 14px 8px;
  color: var(--tl-text-muted);
  font-size: 11px;
  line-height: 1.5;
}

.aside__scroll {
  flex: 1 1 auto;
  min-height: 0;
}

.anno-item {
  display: flex;
  align-items: flex-start;
  gap: 9px;
  width: 100%;
  padding: 9px 14px;
  border: none;
  border-left: 3px solid transparent;
  background: transparent;
  color: inherit;
  font: inherit;
  text-align: left;
  cursor: pointer;
  transition: background-color 0.18s ease;
}

.anno-item:hover {
  background: rgba(128, 128, 128, 0.1);
}

.anno-item.is-active {
  border-left-color: var(--anno-accent);
  background: var(--anno-accent-soft);
}

.anno-item__seq {
  display: flex;
  flex: 0 0 auto;
  align-items: center;
  justify-content: center;
  min-width: 20px;
  height: 20px;
  padding: 0 5px;
  border-radius: 6px;
  background: var(--anno-accent);
  color: #fff;
  font-size: 11px;
  font-weight: 700;
}

.anno-item__body {
  display: flex;
  flex-direction: column;
  gap: 3px;
  min-width: 0;
}

.anno-item__text {
  overflow: hidden;
  font-size: 12px;
  line-height: 1.45;
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}

.anno-item__text.is-empty {
  color: var(--tl-text-muted);
  font-style: italic;
}

.anno-item__meta {
  color: var(--tl-text-muted);
  font-size: 11px;
}

/* ---------------------------------------------------------------- 其它 */

.stage-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 24px;
  text-align: center;
}

.stage-empty p {
  margin: 0;
}

.stage-empty__hint {
  max-width: 360px;
  color: var(--tl-text-muted);
  font-size: 12px;
  line-height: 1.6;
}

.hidden-input {
  display: none;
}

.detail__dropmask {
  position: absolute;
  inset: 0;
  z-index: 20;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  border: 2px dashed var(--brand-primary);
  border-radius: 12px;
  background: rgba(47, 111, 237, 0.12);
  color: var(--brand-primary);
  font-size: 14px;
  font-weight: 600;
  pointer-events: none;
}
</style>
