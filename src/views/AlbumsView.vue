<script setup>
/**
 * 相册页：展示当前所有图集（按交易时间倒序），并支持新建 / 编辑 / 删除图集。
 */
import AlbumFormDialog from '@/components/album/AlbumFormDialog.vue'
import { IconAlbum, IconEdit, IconImage, IconPlus, IconRefresh, IconTrash } from '@/components/icons'
import { useAlbumStore } from '@/stores'
import { formatDateTime } from '@/utils/datetime'

defineOptions({ name: 'AlbumsView' })

const router = useRouter()
const albumStore = useAlbumStore()
const message = useMessage()
const dialog = useDialog()

const formVisible = ref(false)
const editingAlbum = ref(null)
const submitting = ref(false)

async function load(force = false) {
  try {
    await (force ? albumStore.refresh() : albumStore.load())
  } catch (error) {
    message.error(error.message)
  }
}

onMounted(() => load())

function openCreate() {
  editingAlbum.value = null
  formVisible.value = true
}

function openEdit(album) {
  editingAlbum.value = album
  formVisible.value = true
}

async function handleSubmit(payload) {
  submitting.value = true
  try {
    if (editingAlbum.value) {
      await albumStore.update(editingAlbum.value.id, payload)
      message.success('图集已更新')
    } else {
      await albumStore.create(payload)
      message.success('图集已创建，进入后即可添加截图')
    }
    formVisible.value = false
  } catch (error) {
    message.error(error.message)
  } finally {
    submitting.value = false
  }
}

function confirmDelete(album) {
  dialog.warning({
    title: '删除图集',
    content: `确定删除「${album.symbol}」及其 ${album.image_count} 张截图和全部批注吗？该操作不可恢复。`,
    positiveText: '删除',
    negativeText: '取消',
    onPositiveClick: async () => {
      try {
        await albumStore.remove(album.id)
        message.success('图集已删除')
      } catch (error) {
        message.error(error.message)
      }
    },
  })
}

function openAlbum(album) {
  router.push(`/albums/${album.id}`)
}
</script>

<template>
  <div class="page">
    <div class="albums__head">
      <div>
        <h1 class="page__title">交易相册</h1>
        <p class="page__desc">
          共 {{ albumStore.total }} 个图集 · 按交易时间倒序排列 · 每个图集内可上传多张截图并添加点/矩形批注
        </p>
      </div>

      <div class="albums__actions">
        <n-button :loading="albumStore.loading" @click="load(true)">
          <template #icon>
            <component :is="IconRefresh" />
          </template>
          刷新
        </n-button>
        <n-button type="primary" @click="openCreate">
          <template #icon>
            <component :is="IconPlus" />
          </template>
          新建图集
        </n-button>
      </div>
    </div>

    <n-spin :show="albumStore.loading && !albumStore.loaded">
      <!-- 空状态 -->
      <n-empty
        v-if="albumStore.isEmpty"
        class="albums__empty"
        description="还没有任何图集"
      >
        <template #extra>
          <n-button type="primary" @click="openCreate">新建第一个图集</n-button>
        </template>
      </n-empty>

      <n-grid
        v-else
        :x-gap="16"
        :y-gap="16"
        cols="1 s:2 m:3 l:4"
        responsive="screen"
      >
        <n-grid-item v-for="album in albumStore.albums" :key="album.id">
          <div class="album-card" @click="openAlbum(album)">
            <div class="album-card__cover">
              <img
                v-if="album.cover_thumb_url"
                class="album-card__cover-img"
                :src="album.cover_thumb_url"
                :alt="album.symbol"
              />
              <div v-else class="album-card__cover-empty">
                <component :is="album.image_count ? IconImage : IconAlbum" />
                <span>暂无截图</span>
              </div>

              <span class="album-card__count">{{ album.image_count }} 张</span>
            </div>

            <div class="album-card__body">
              <div class="album-card__symbol" :title="album.symbol">{{ album.symbol }}</div>
              <div class="album-card__time">{{ formatDateTime(album.trade_time) }}</div>
              <div v-if="album.title" class="album-card__title" :title="album.title">
                {{ album.title }}
              </div>
            </div>

            <div class="album-card__foot">
              <n-button
                size="tiny"
                quaternary
                title="编辑图集信息"
                @click.stop="openEdit(album)"
              >
                <template #icon>
                  <component :is="IconEdit" />
                </template>
                编辑
              </n-button>
              <n-button
                size="tiny"
                quaternary
                type="error"
                title="删除图集"
                @click.stop="confirmDelete(album)"
              >
                <template #icon>
                  <component :is="IconTrash" />
                </template>
                删除
              </n-button>
            </div>
          </div>
        </n-grid-item>
      </n-grid>
    </n-spin>

    <AlbumFormDialog
      v-model:show="formVisible"
      :album="editingAlbum"
      :submitting="submitting"
      @submit="handleSubmit"
    />
  </div>
</template>

<style scoped>
.albums__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 18px;
}

.albums__actions {
  display: flex;
  flex: 0 0 auto;
  gap: 10px;
}

.albums__empty {
  padding: 70px 0;
}

.album-card {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
  border: 1px solid var(--tl-surface-border);
  border-radius: 12px;
  background: var(--tl-surface);
  cursor: pointer;
  transition:
    transform 0.2s ease,
    box-shadow 0.2s ease,
    border-color 0.2s ease;
}

.album-card:hover {
  transform: translateY(-3px);
  border-color: var(--brand-primary);
  box-shadow: 0 10px 24px rgba(0, 0, 0, 0.14);
}

.album-card__cover {
  position: relative;
  height: 132px;
  background: var(--tl-board);
}

.album-card__cover-img {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: cover;
  /* 截图多为浅底，铺白更接近原貌 */
  background: #fff;
}

.album-card__cover-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 6px;
  height: 100%;
  color: var(--tl-text-muted);
  font-size: 12px;
}

.album-card__count {
  position: absolute;
  right: 8px;
  bottom: 8px;
  padding: 2px 8px;
  border-radius: 999px;
  background: rgba(0, 0, 0, 0.6);
  color: #fff;
  font-size: 11px;
  font-weight: 600;
}

.album-card__body {
  flex: 1 1 auto;
  padding: 12px 14px 6px;
}

.album-card__symbol {
  overflow: hidden;
  font-size: 15px;
  font-weight: 600;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.album-card__time {
  margin-top: 4px;
  color: var(--tl-text-muted);
  font-size: 12px;
  font-variant-numeric: tabular-nums;
}

.album-card__title {
  margin-top: 6px;
  overflow: hidden;
  color: var(--tl-text-dim);
  font-size: 12px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.album-card__foot {
  display: flex;
  justify-content: flex-end;
  gap: 4px;
  padding: 6px 8px 8px;
  border-top: 1px solid var(--tl-surface-border);
}
</style>
