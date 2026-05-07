<template>
  <div class="policy-injection-page">
    <div class="injection-stack">
      <!-- 第一行：规则分类 + 策略沙箱 -->
      <a-row :gutter="16" class="page-row page-row--top" align="stretch">
        <a-col :xs="24" :md="24" :lg="10" :xl="9" class="col-fill col-top">
          <a-card :bordered="false" size="small" class="tree-card">
            <template #title><span class="card-title"><filter-outlined /> 规则分类</span></template>
            <a-tree
              v-model:selected-keys="selectedKeys"
              :tree-data="treeData"
              :default-expand-all="true"
              block-node
            />
            <a-divider />
            <a-row :gutter="8">
              <a-col :span="12"><div class="mini">总规则数<br /><b>{{ rules.length }}</b></div></a-col>
              <a-col :span="12"><div class="mini">7 日命中<br /><b>{{ totalHits }}</b></div></a-col>
            </a-row>

            <RiskThresholdPanel />
          </a-card>
        </a-col>

        <a-col :xs="24" :md="24" :lg="14" :xl="15" class="col-fill col-top">
          <div class="sandbox-stretch">
            <PolicySandbox />
          </div>
        </a-col>
      </a-row>

      <!-- 第二行：规则库表格全宽 -->
      <a-row :gutter="16" class="page-row page-row--table">
        <a-col :span="24" class="col-table">
          <a-card :bordered="false" size="small" class="table-card">
            <template #title><span class="card-title">注入检测规则库</span></template>
            <template #extra>
              <a-button type="primary" size="small" @click="openCreate"><plus-outlined /> 新增规则</a-button>
            </template>

            <a-table
              size="small"
              class="rules-table"
              :loading="loading"
              :data-source="filtered"
              :columns="columns"
              :pagination="{ pageSize: 12 }"
              :scroll="{ x: 980 }"
              row-key="id"
            >
              <template #bodyCell="{ column, record }">
                <template v-if="column.dataIndex === 'type'">
                  <a-tag>{{ typeLabel(record.type) }}</a-tag>
                </template>
                <template v-else-if="column.dataIndex === 'weight'">
                  <a-progress
                    :percent="Math.round(record.weight * 100)"
                    size="small"
                    :stroke-color="{
                      '0%': record.weight > 0.85 ? '#F43F5E' : record.weight > 0.6 ? '#F59E0B' : '#10B981',
                      '100%': record.weight > 0.85 ? '#F59E0B' : record.weight > 0.6 ? '#FBBF24' : '#34D399',
                    }"
                  />
                </template>
                <template v-else-if="column.dataIndex === 'enabled'">
                  <a-switch
                    size="small"
                    :checked="record.enabled"
                    @change="(v: boolean) => toggleEnabled(record, v)"
                  />
                </template>
                <template v-else-if="column.dataIndex === 'op'">
                  <a-space size="small" :wrap="false" class="op-cell">
                    <a-button type="link" size="small" @click="openEdit(record)">编辑</a-button>
                    <a-popconfirm title="确认删除？" @confirm="onDelete(record.id)">
                      <a-button type="link" size="small" danger>删除</a-button>
                    </a-popconfirm>
                  </a-space>
                </template>
              </template>
            </a-table>
          </a-card>
        </a-col>
      </a-row>
    </div>

    <!-- 编辑/新增弹窗 -->
    <a-modal
      v-model:open="modalOpen"
      :title="form.id ? '编辑规则' : '新增规则'"
      :confirm-loading="submitting"
      @ok="submit"
    >
      <a-form layout="vertical" :model="form">
        <a-form-item label="名称" required>
          <a-input v-model:value="form.name" />
        </a-form-item>
        <a-row :gutter="12">
          <a-col :span="12">
            <a-form-item label="类型" required>
              <a-select v-model:value="form.type" :options="typeOptions" />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="风险类别">
              <a-select v-model:value="form.category" :options="categoryOptions" />
            </a-form-item>
          </a-col>
        </a-row>
        <a-form-item :label="form.type === 'semantic' ? '匹配模板（语义识别可留空）' : '匹配模板（正则 / 关键词）'">
          <a-textarea v-model:value="form.pattern" :rows="2" />
        </a-form-item>
        <a-form-item label="风险权重">
          <a-slider v-model:value="weightPercent" :min="0" :max="100" />
          <span class="hint">当前权重：{{ weightPercent }}% — 用于 R 综合评分中的 S_rule 子项</span>
        </a-form-item>
        <a-form-item label="说明">
          <a-textarea v-model:value="form.description" :rows="2" />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue';
import { FilterOutlined, PlusOutlined } from '@ant-design/icons-vue';
import { message } from 'ant-design-vue';
import {
  listInjectionRules,
  saveInjectionRule,
  deleteInjectionRule,
} from '@/api/services';
import type { InjectionRule, RuleType } from '@/types/api';
import PolicySandbox from '@/components/common/PolicySandbox.vue';
import RiskThresholdPanel from '@/components/common/RiskThresholdPanel.vue';

const loading = ref(false);
const rules = ref<InjectionRule[]>([]);
const selectedKeys = ref<string[]>(['all']);

const treeData = computed(() => [
  {
    title: `全部规则 (${rules.value.length})`,
    key: 'all',
    children: [
      { title: `提示注入 (${countOf('提示注入')})`, key: '提示注入' },
      { title: `越权诱导 (${countOf('越权诱导')})`, key: '越权诱导' },
      { title: `系统提示泄露 (${countOf('系统提示泄露')})`, key: '系统提示泄露' },
      { title: `敏感诱导 (${countOf('敏感诱导')})`, key: '敏感诱导' },
    ],
  },
]);

function countOf(cat: InjectionRule['category']) {
  return rules.value.filter((r) => r.category === cat).length;
}

const filtered = computed(() => {
  const k = selectedKeys.value[0];
  if (!k || k === 'all') return rules.value;
  return rules.value.filter((r) => r.category === k);
});

const totalHits = computed(() => rules.value.reduce((s, r) => s + r.hits7d, 0));

const columns = [
  { title: '名称', dataIndex: 'name', width: 150, ellipsis: true },
  { title: '类型', dataIndex: 'type', width: 88 },
  { title: '类别', dataIndex: 'category', width: 108, ellipsis: true },
  { title: '匹配模板', dataIndex: 'pattern', width: 200, ellipsis: true },
  { title: '权重', dataIndex: 'weight', width: 120 },
  { title: '7d 命中', dataIndex: 'hits7d', width: 76 },
  { title: '启用', dataIndex: 'enabled', width: 72 },
  /** 不使用 fixed: right：在 flex 三栏布局下未设 scroll 时固定列会脱离表格叠到右侧卡片上 */
  { title: '操作', dataIndex: 'op', width: 136, align: 'right' as const },
];

const typeOptions = [
  { value: 'regex', label: '正则' },
  { value: 'keyword', label: '关键词' },
  { value: 'semantic', label: '语义识别' },
];

const categoryOptions: Array<{ value: InjectionRule['category']; label: string }> = [
  { value: '提示注入', label: '提示注入' },
  { value: '越权诱导', label: '越权诱导' },
  { value: '系统提示泄露', label: '系统提示泄露' },
  { value: '敏感诱导', label: '敏感诱导' },
];

const modalOpen = ref(false);
const submitting = ref(false);
const form = ref<InjectionRule>(emptyForm());
const weightPercent = ref(70);

watch(weightPercent, (v) => {
  form.value.weight = Number((v / 100).toFixed(2));
});

function emptyForm(): InjectionRule {
  return {
    id: '',
    name: '',
    type: 'keyword' as RuleType,
    pattern: '',
    category: '提示注入',
    weight: 0.7,
    enabled: true,
    hits7d: 0,
  };
}

function typeLabel(t: RuleType) {
  return t === 'regex' ? '正则' : t === 'keyword' ? '关键词' : '语义识别';
}

async function load() {
  loading.value = true;
  try {
    rules.value = await listInjectionRules();
  } finally {
    loading.value = false;
  }
}

function openCreate() {
  form.value = emptyForm();
  weightPercent.value = 70;
  modalOpen.value = true;
}
function openEdit(r: InjectionRule) {
  form.value = { ...r };
  weightPercent.value = Math.round(r.weight * 100);
  modalOpen.value = true;
}
async function submit() {
  if (!form.value.name) {
    message.warning('请填写规则名称');
    return;
  }
  submitting.value = true;
  try {
    const saved = await saveInjectionRule(form.value);
    const i = rules.value.findIndex((r) => r.id === saved.id);
    if (i >= 0) rules.value[i] = saved;
    else rules.value = [...rules.value, saved];
    modalOpen.value = false;
    message.success('已保存');
  } finally {
    submitting.value = false;
  }
}
async function toggleEnabled(r: InjectionRule, v: boolean) {
  await saveInjectionRule({ ...r, enabled: v });
  r.enabled = v;
}
async function onDelete(id: string) {
  await deleteInjectionRule(id);
  rules.value = rules.value.filter((r) => r.id !== id);
  message.success('已删除');
}

onMounted(load);
</script>

<style scoped>
.policy-injection-page {
  width: 100%;
  max-width: 100%;
  min-width: 0;
  overflow-x: hidden;
}

.injection-stack {
  display: flex;
  flex-direction: column;
  gap: 16px;
  width: 100%;
  min-width: 0;
}

.page-row {
  margin: 0 !important;
  min-width: 0;
  width: 100%;
}

.col-fill {
  display: flex;
  flex-direction: column;
  min-height: 0;
  min-width: 0;
}

.col-top {
  /* 首行两列等高：沙箱与分类区视觉对齐 */
  align-self: stretch;
}

.sandbox-stretch {
  flex: 1;
  min-height: 0;
  min-width: 0;
  display: flex;
  flex-direction: column;
  height: 100%;
}

.sandbox-stretch :deep(.sandbox-card) {
  flex: 1;
  min-height: 260px;
}

.col-table {
  min-width: 0;
  width: 100%;
}

.tree-card {
  background: rgba(255, 255, 255, 0.94);
  height: 100%;
  flex: 1;
  min-height: 0;
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.tree-card :deep(.ant-card-body) {
  flex: 1;
  min-height: 0;
  min-width: 0;
  overflow-x: auto;
  overflow-y: auto;
}

.table-card {
  background: rgba(255, 255, 255, 0.94);
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.table-card :deep(.ant-card-body) {
  min-width: 0;
  overflow-x: auto;
}

.table-card :deep(.rules-table) {
  max-width: 100%;
}

.table-card :deep(.ant-table-wrapper) {
  max-width: 100%;
}

.op-cell {
  white-space: nowrap;
  justify-content: flex-end;
}
.card-title {
  font-weight: 600;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: #0F172A;
}
.card-title :deep(.anticon) {
  color: #6366F1;
}
.mini {
  font-size: 12px;
  color: #64748B;
  text-align: center;
  padding: 6px 0;
  border-radius: 8px;
  background: rgba(238, 242, 255, 0.55);
  border: 1px solid rgba(99, 102, 241, 0.14);
}
.mini b {
  font-size: 18px;
  color: #4338CA;
  font-variant-numeric: tabular-nums;
}
.hint {
  font-size: 12px;
  color: #64748B;
  margin-top: 4px;
}
</style>
