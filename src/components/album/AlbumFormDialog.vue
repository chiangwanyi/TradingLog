<script setup>
/**
 * 新建 / 编辑图集的表单弹窗。
 *
 * 图集信息：交易时间（精确到分钟）+ 标的，另有可选标题与备注。
 * 交易时间在提交时转成不带时区的本地 ISO 字符串，与后端约定一致。
 */
import { toLocalIso, toPickerValue } from '@/utils/datetime'

const props = defineProps({
  show: { type: Boolean, default: false },
  /** 传入则为编辑模式，为 null 则是新建 */
  album: { type: Object, default: null },
  submitting: { type: Boolean, default: false },
})

const emit = defineEmits(['update:show', 'submit'])

const formRef = ref(null)

const form = reactive({
  symbol: '',
  tradeTime: Date.now(),
  title: '',
  note: '',
})

const isEdit = computed(() => Boolean(props.album))
const title = computed(() => (isEdit.value ? '编辑图集' : '新建图集'))

const rules = {
  symbol: {
    required: true,
    trigger: ['input', 'blur'],
    message: '请填写标的',
  },
  tradeTime: {
    type: 'number',
    required: true,
    trigger: ['change', 'blur'],
    message: '请选择交易时间',
  },
}

/** 每次打开重置表单：编辑态回填已有数据，新建态默认当前时间 */
watch(
  () => props.show,
  (visible) => {
    if (!visible) return
    form.symbol = props.album?.symbol ?? ''
    form.tradeTime = toPickerValue(props.album?.trade_time)
    form.title = props.album?.title ?? ''
    form.note = props.album?.note ?? ''
    formRef.value?.restoreValidation()
  },
)

async function handleSubmit() {
  try {
    await formRef.value?.validate()
  } catch {
    return // 校验未通过，Naive UI 已在表单上给出提示
  }

  emit('submit', {
    symbol: form.symbol.trim(),
    trade_time: toLocalIso(new Date(form.tradeTime)),
    title: form.title.trim(),
    note: form.note.trim(),
  })
}

function handleClose() {
  emit('update:show', false)
}
</script>

<template>
  <n-modal
    :show="show"
    preset="card"
    :title="title"
    class="album-form"
    :style="{ width: '460px' }"
    :mask-closable="!submitting"
    @update:show="emit('update:show', $event)"
  >
    <n-form ref="formRef" :model="form" :rules="rules" label-placement="top" require-mark-placement="right-hanging">
      <n-form-item label="标的" path="symbol">
        <n-input
          v-model:value="form.symbol"
          placeholder="如：000001 平安银行 / 沪深300 / BTCUSDT"
          maxlength="64"
          show-count
          :disabled="submitting"
        />
      </n-form-item>

      <n-form-item label="交易时间" path="tradeTime">
        <n-date-picker
          v-model:value="form.tradeTime"
          type="datetime"
          format="yyyy-MM-dd HH:mm"
          :actions="['now', 'confirm']"
          :is-date-disabled="() => false"
          placeholder="选择交易发生的日期与时间"
          style="width: 100%"
          :disabled="submitting"
        />
      </n-form-item>

      <n-form-item label="标题（可选）">
        <n-input
          v-model:value="form.title"
          placeholder="如：早盘突破回踩"
          maxlength="128"
          show-count
          :disabled="submitting"
        />
      </n-form-item>

      <n-form-item label="备注（可选）">
        <n-input
          v-model:value="form.note"
          type="textarea"
          placeholder="补充当时的市场背景、操作思路等"
          maxlength="2000"
          show-count
          :autosize="{ minRows: 3, maxRows: 6 }"
          :disabled="submitting"
        />
      </n-form-item>
    </n-form>

    <template #footer>
      <div class="album-form__foot">
        <n-button :disabled="submitting" @click="handleClose">取消</n-button>
        <n-button type="primary" :loading="submitting" @click="handleSubmit">
          {{ isEdit ? '保存' : '创建' }}
        </n-button>
      </div>
    </template>
  </n-modal>
</template>

<style scoped>
.album-form__foot {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}
</style>
