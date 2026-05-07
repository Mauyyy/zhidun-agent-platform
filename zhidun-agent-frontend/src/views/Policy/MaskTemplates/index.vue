<template>
  <div class="policy-mask-page">
    <a-row :gutter="16" align="stretch" class="mask-row">
      <a-col :xs="24" :md="16" class="mask-col">
        <a-card :bordered="false" size="small" class="card">
          <template #title><span class="title"><eye-invisible-outlined /> 数据去标识化模板</span></template>
          <template #extra>
            <a-button type="primary" size="small" @click="openCreate"><plus-outlined /> 新增模板</a-button>
          </template>

          <a-table
            size="small"
            :loading="loading"
            :data-source="rows"
            :columns="columns"
            row-key="id"
            :pagination="{ pageSize: 12 }"
          >
            <template #bodyCell="{ column, record }">
              <template v-if="column.dataIndex === 'strategy'">
                <a-tag :color="strategyColor(record.strategy)">{{ strategyLabel(record.strategy) }}</a-tag>
              </template>
              <template v-else-if="column.dataIndex === 'enabled'">
                <a-switch
                  size="small"
                  :checked="record.enabled"
                  @change="(v: boolean) => onToggle(record, v)"
                />
              </template>
              <template v-else-if="column.dataIndex === 'op'">
                <a-button type="link" size="small" @click="openEdit(record)">编辑</a-button>
                <a-popconfirm title="确认删除？" @confirm="onDelete(record.id)">
                  <a-button type="link" size="small" danger>删除</a-button>
                </a-popconfirm>
              </template>
            </template>
          </a-table>
        </a-card>
      </a-col>

      <!-- 右：实时脱敏预览 -->
      <a-col :xs="24" :md="8" class="mask-col">
        <a-card :bordered="false" size="small" class="preview-card">
          <template #title><span class="title">脱敏预览</span></template>
          <a-form layout="vertical">
            <a-form-item label="原始文本">
              <a-textarea v-model:value="sample" :rows="6" />
            </a-form-item>
          </a-form>
          <div class="preview-out">
            <div class="lbl">脱敏后</div>
            <div class="masked">{{ masked }}</div>
            <div class="hits">
              <a-tag v-for="h in hits" :key="h.id" color="orange">{{ h.name }} × {{ h.count }}</a-tag>
              <span v-if="!hits.length" class="muted">未命中任何模板</span>
            </div>
          </div>
        </a-card>
      </a-col>
    </a-row>

    <a-modal
      v-model:open="modalOpen"
      :title="form.id ? '编辑模板' : '新增模板'"
      :confirm-loading="submitting"
      @ok="submit"
    >
      <a-form layout="vertical" :model="form">
        <a-form-item label="名称" required><a-input v-model:value="form.name" /></a-form-item>
        <a-row :gutter="12">
          <a-col :span="12">
            <a-form-item label="字段类型"><a-input v-model:value="form.category" placeholder="如：个人隐私 / 密钥令牌" /></a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="处理策略">
              <a-select v-model:value="form.strategy" :options="strategyOptions" />
            </a-form-item>
          </a-col>
        </a-row>
        <a-form-item label="正则表达式（可空）"><a-textarea v-model:value="form.pattern" :rows="2" /></a-form-item>
        <a-form-item label="替换格式（仅 mask / truncate 生效）"><a-input v-model:value="form.replacement" /></a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue';
import { EyeInvisibleOutlined, PlusOutlined } from '@ant-design/icons-vue';
import { message } from 'ant-design-vue';
import {
  listMaskTemplates,
  previewDesensitization,
  saveMaskTemplate,
  deleteMaskTemplate,
} from '@/api/services';
import type { MaskStrategy, MaskTemplate } from '@/types/api';

const loading = ref(false);
const rows = ref<MaskTemplate[]>([]);
const sample = ref('经理张三的手机号 13812345678，邮箱 admin@zhidun.com，系统密钥 SK-9821ABCDEF。');
const previewMasked = ref(sample.value);
const previewHits = ref<Array<{ id: string; name: string; count: number }>>([]);
let previewTimer: number | null = null;

const columns = [
  { title: '名称', dataIndex: 'name', width: 140 },
  { title: '字段类型', dataIndex: 'category', width: 120 },
  { title: '正则模板', dataIndex: 'pattern', ellipsis: true },
  { title: '策略', dataIndex: 'strategy', width: 110 },
  { title: '7d 命中', dataIndex: 'hits7d', width: 100 },
  { title: '启用', dataIndex: 'enabled', width: 80 },
  { title: '操作', dataIndex: 'op', width: 130, fixed: 'right' as const },
];

const strategyOptions: Array<{ value: MaskStrategy; label: string }> = [
  { value: 'mask', label: '掩码（保留首尾）' },
  { value: 'truncate', label: '截断' },
  { value: 'hash', label: '哈希' },
  { value: 'reject', label: '拒绝输出' },
];

function strategyLabel(s: MaskStrategy) {
  return strategyOptions.find((o) => o.value === s)?.label ?? s;
}
function strategyColor(s: MaskStrategy) {
  if (s === 'reject') return 'red';
  if (s === 'truncate') return 'orange';
  if (s === 'hash') return 'purple';
  return 'green';
}

const modalOpen = ref(false);
const submitting = ref(false);
const form = ref<MaskTemplate>(empty());
function empty(): MaskTemplate {
  return {
    id: '',
    name: '',
    pattern: '',
    category: '',
    strategy: 'mask',
    replacement: '',
    enabled: true,
    hits7d: 0,
  };
}

async function load() {
  loading.value = true;
  try {
    rows.value = await listMaskTemplates();
  } finally {
    loading.value = false;
  }
}
function openCreate() {
  form.value = empty();
  modalOpen.value = true;
}
function openEdit(r: MaskTemplate) {
  form.value = { ...r };
  modalOpen.value = true;
}
async function submit() {
  if (!form.value.name) return message.warning('请填写名称');
  submitting.value = true;
  try {
    const saved = await saveMaskTemplate(form.value);
    const i = rows.value.findIndex((r) => r.id === saved.id);
    if (i >= 0) rows.value[i] = saved;
    else rows.value = [...rows.value, saved];
    modalOpen.value = false;
    message.success('已保存');
  } finally {
    submitting.value = false;
  }
}
async function onToggle(r: MaskTemplate, v: boolean) {
  await saveMaskTemplate({ ...r, enabled: v });
  r.enabled = v;
}
async function onDelete(id: string) {
  await deleteMaskTemplate(id);
  rows.value = rows.value.filter((r) => r.id !== id);
}

const masked = computed(() => previewMasked.value);
const hits = computed(() => previewHits.value);

async function runPreview() {
  try {
    const result = await previewDesensitization(sample.value);
    previewMasked.value = result.masked || result.after || sample.value;
    const counters = new Map<string, number>();
    for (const item of result.redactions ?? []) {
      counters.set(item.type, (counters.get(item.type) ?? 0) + 1);
    }
    previewHits.value = Array.from(counters.entries()).map(([name, count]) => ({
      id: name,
      name,
      count,
    }));
  } catch {
    previewMasked.value = sample.value;
    previewHits.value = [];
  }
}

watch(sample, () => {
  if (previewTimer != null) window.clearTimeout(previewTimer);
  previewTimer = window.setTimeout(runPreview, 250);
});

onMounted(async () => {
  await load();
  await runPreview();
});
</script>

<style scoped>
.policy-mask-page {
  width: 100%;
  min-width: 0;
}

.mask-row {
  margin: 0 !important;
  min-width: 0;
}

.mask-col {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.card,
.preview-card {
  background: rgba(255, 255, 255, 0.94);
  height: 100%;
  min-width: 0;
}

.card :deep(.ant-card-body),
.preview-card :deep(.ant-card-body) {
  min-width: 0;
}
.title {
  font-weight: 600;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: #0F172A;
}
.title :deep(.anticon) {
  color: #6366F1;
}
.preview-out {
  margin-top: 8px;
  padding: 12px;
  background: #D1FAE5;
  border: 1px solid rgba(16, 185, 129, 0.32);
  border-radius: 10px;
}
.lbl {
  font-size: 11px;
  color: #475569;
  margin-bottom: 6px;
  font-weight: 500;
}
.masked {
  font-family: monospace;
  font-size: 12.5px;
  color: #047857;
  margin-bottom: 8px;
  white-space: pre-wrap;
  word-break: break-all;
}
.hits {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
}
.muted {
  color: #94A3B8;
  font-size: 12px;
}

@media (max-width: 767px) {
  .mask-col + .mask-col {
    margin-top: 16px;
  }
}
</style>
