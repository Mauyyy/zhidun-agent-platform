<template>
  <a-card :bordered="false" size="small" class="card">
    <template #title>
      <span class="title"><database-outlined /> 敏感资源资产盘点</span>
    </template>
    <template #extra>
      <a-space>
        <a-select v-model:value="filterLevel" placeholder="敏感等级" allow-clear style="width: 120px">
          <a-select-option value="L4">L4</a-select-option>
          <a-select-option value="L3">L3</a-select-option>
          <a-select-option value="L2">L2</a-select-option>
          <a-select-option value="L1">L1</a-select-option>
        </a-select>
        <a-select v-model:value="filterType" placeholder="资源类型" allow-clear style="width: 140px">
          <a-select-option value="api">API</a-select-option>
          <a-select-option value="directory">目录</a-select-option>
          <a-select-option value="db_table">数据库表</a-select-option>
          <a-select-option value="file_pattern">文件 Glob</a-select-option>
        </a-select>
        <a-button type="primary" size="small" @click="openCreate"><plus-outlined /> 录入资产</a-button>
      </a-space>
    </template>

    <a-table
      size="small"
      :loading="loading"
      :data-source="filtered"
      :columns="columns"
      row-key="id"
      :pagination="{ pageSize: 10 }"
    >
      <template #bodyCell="{ column, record }">
        <template v-if="column.dataIndex === 'level'">
          <a-tag :color="record.level === 'L4' ? 'red' : record.level === 'L3' ? 'orange' : 'blue'">
            {{ record.level }}
          </a-tag>
        </template>
        <template v-else-if="column.dataIndex === 'type'">
          <a-tag>{{ typeLabel(record.type) }}</a-tag>
        </template>
        <template v-else-if="column.dataIndex === 'op'">
          <a-button type="link" size="small" @click="openEdit(record)">编辑</a-button>
        </template>
      </template>
    </a-table>
  </a-card>

  <a-modal
    v-model:open="modalOpen"
    :title="form.id ? '编辑资产' : '录入敏感资产'"
    :confirm-loading="submitting"
    @ok="submit"
  >
    <a-form layout="vertical" :model="form">
      <a-form-item label="资产名称" required><a-input v-model:value="form.name" /></a-form-item>
      <a-row :gutter="12">
        <a-col :span="12">
          <a-form-item label="类型">
            <a-select v-model:value="form.type" :options="typeOpts" />
          </a-form-item>
        </a-col>
        <a-col :span="12">
          <a-form-item label="敏感等级">
            <a-select v-model:value="form.level" :options="['L1','L2','L3','L4'].map(v=>({value:v,label:v}))" />
          </a-form-item>
        </a-col>
      </a-row>
      <a-form-item label="标识符（路径 / 表名 / Glob）">
        <a-input v-model:value="form.identifier" placeholder="如 /admin/config 或 tb_customer_info" />
      </a-form-item>
      <a-form-item label="负责人"><a-input v-model:value="form.owner" /></a-form-item>
      <a-form-item label="说明"><a-textarea v-model:value="form.description" :rows="2" /></a-form-item>
    </a-form>
  </a-modal>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { DatabaseOutlined, PlusOutlined } from '@ant-design/icons-vue';
import { message } from 'ant-design-vue';
import { listSensitiveAssets, saveSensitiveAsset } from '@/api/services';
import type { SensitiveAsset } from '@/types/api';

const loading = ref(false);
const rows = ref<SensitiveAsset[]>([]);
const filterLevel = ref<string | undefined>();
const filterType = ref<string | undefined>();

const filtered = computed(() => {
  return rows.value.filter((r) => {
    if (filterLevel.value && r.level !== filterLevel.value) return false;
    if (filterType.value && r.type !== filterType.value) return false;
    return true;
  });
});

const columns = [
  { title: '资产名称', dataIndex: 'name', width: 180 },
  { title: '类型', dataIndex: 'type', width: 110 },
  { title: '标识符', dataIndex: 'identifier', ellipsis: true },
  { title: '敏感等级', dataIndex: 'level', width: 100 },
  { title: '负责人', dataIndex: 'owner', width: 120 },
  { title: '操作', dataIndex: 'op', width: 100, fixed: 'right' as const },
];

const typeOpts = [
  { value: 'api', label: 'API' },
  { value: 'directory', label: '目录' },
  { value: 'db_table', label: '数据库表' },
  { value: 'file_pattern', label: '文件 Glob' },
];
function typeLabel(t: SensitiveAsset['type']) {
  return typeOpts.find((o) => o.value === t)?.label ?? t;
}

const modalOpen = ref(false);
const submitting = ref(false);
const form = ref<SensitiveAsset>(empty());
function empty(): SensitiveAsset {
  return {
    id: '',
    name: '',
    type: 'directory',
    identifier: '',
    level: 'L3',
    owner: '',
    description: '',
  };
}

async function load() {
  loading.value = true;
  try {
    rows.value = await listSensitiveAssets();
  } finally {
    loading.value = false;
  }
}
function openCreate() {
  form.value = empty();
  modalOpen.value = true;
}
function openEdit(r: SensitiveAsset) {
  form.value = { ...r };
  modalOpen.value = true;
}
async function submit() {
  if (!form.value.name) return message.warning('请填写资产名称');
  submitting.value = true;
  try {
    const saved = await saveSensitiveAsset(form.value);
    const i = rows.value.findIndex((r) => r.id === saved.id);
    if (i >= 0) rows.value[i] = saved;
    else rows.value = [...rows.value, saved];
    modalOpen.value = false;
    message.success('已保存');
  } finally {
    submitting.value = false;
  }
}

onMounted(load);
</script>

<style scoped>
.card {
  background: rgba(255, 255, 255, 0.94);
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
</style>
