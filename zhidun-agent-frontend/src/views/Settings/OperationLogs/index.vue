<template>
  <a-card :bordered="false" size="small" class="card">
    <template #title>
      <span class="title"><history-outlined /> 平台操作日志</span>
    </template>
    <template #extra>
      <a-input-search
        v-model:value="keyword"
        placeholder="按操作员 / 动作 / 目标搜索"
        allow-clear
        style="width: 280px"
      />
    </template>

    <a-table
      size="small"
      :loading="loading"
      :data-source="filtered"
      :columns="columns"
      row-key="id"
      :pagination="pagination"
      @change="onTableChange"
    >
      <template #bodyCell="{ column, record }">
        <template v-if="column.dataIndex === 'outcome'">
          <a-tag :color="record.outcome === 'success' ? 'green' : 'red'">
            {{ record.outcome === 'success' ? '成功' : '失败' }}
          </a-tag>
        </template>
      </template>
    </a-table>
  </a-card>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { HistoryOutlined } from '@ant-design/icons-vue';
import { listOperationLogs } from '@/api/services';
import type { OperationLog } from '@/types/api';

const loading = ref(false);
const rows = ref<OperationLog[]>([]);
const keyword = ref('');
const pagination = ref({ current: 1, pageSize: 20, total: 0, showSizeChanger: true });

const columns = [
  { title: '时间', dataIndex: 'time', width: 180 },
  { title: '操作员', dataIndex: 'actor', width: 130 },
  { title: '动作', dataIndex: 'action', width: 200 },
  { title: '目标', dataIndex: 'target' },
  { title: 'IP', dataIndex: 'ip', width: 140 },
  { title: '结果', dataIndex: 'outcome', width: 100 },
];

const filtered = computed(() => {
  const k = keyword.value.trim().toLowerCase();
  if (!k) return rows.value;
  return rows.value.filter((r) =>
    [r.actor, r.action, r.target].some((s) => s.toLowerCase().includes(k))
  );
});

async function load() {
  loading.value = true;
  try {
    const res = await listOperationLogs(pagination.value.current, pagination.value.pageSize);
    rows.value = res.items;
    pagination.value.total = res.total;
  } finally {
    loading.value = false;
  }
}

function onTableChange(p: { current?: number; pageSize?: number }) {
  pagination.value.current = p.current ?? 1;
  pagination.value.pageSize = p.pageSize ?? 20;
  load();
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
