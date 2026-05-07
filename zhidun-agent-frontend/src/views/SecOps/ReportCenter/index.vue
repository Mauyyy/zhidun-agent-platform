<template>
  <div class="report-center">
    <a-card :bordered="false" size="small" class="head-card">
      <a-row :gutter="16" align="middle">
        <a-col :flex="1">
          <span class="title"><file-protect-outlined /> 综合审计报告生成</span>
          <p class="sub">支持按事件、按时间窗、按风险类别批量导出，可一键发送到合规邮箱。</p>
        </a-col>
        <a-col>
          <a-space>
            <a-range-picker v-model:value="range" />
            <a-select
              v-model:value="filterLevel"
              :options="levelOpts"
              placeholder="风险等级"
              allow-clear
              style="width: 140px"
            />
            <a-button type="primary" :loading="batching" @click="batchExport">
              <download-outlined /> 批量导出 ({{ selectedRowKeys.length || filtered.length }})
            </a-button>
          </a-space>
        </a-col>
      </a-row>
    </a-card>

    <a-card :bordered="false" size="small" class="table-card">
      <a-table
        size="small"
        :loading="loading"
        :data-source="filtered"
        :columns="columns"
        :row-selection="{ selectedRowKeys, onChange: (keys: string[]) => (selectedRowKeys = keys) }"
        :pagination="{ pageSize: 10, showSizeChanger: true }"
        row-key="id"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.dataIndex === 'level'">
            <a-tag :color="record.level === '高危' ? 'red' : record.level === '中危' ? 'orange' : 'green'">
              {{ record.level }}
            </a-tag>
          </template>
          <template v-else-if="column.dataIndex === 'op'">
            <a-button type="link" size="small" @click="openEvidence(record.id)">查看证据链</a-button>
            <a-button type="link" size="small" :loading="exportingId === record.id" @click="exportOne(record.id)">
              生成 PDF
            </a-button>
          </template>
        </template>
      </a-table>
    </a-card>

    <a-card v-if="jobs.length" :bordered="false" size="small" class="job-card" title="导出任务">
      <a-list size="small" :data-source="jobs" item-layout="horizontal">
        <template #renderItem="{ item }">
          <a-list-item>
            <a-list-item-meta>
              <template #title>
                <span class="mono">{{ item.jobId }}</span>
                <a-tag :color="item.status === 'done' ? 'green' : item.status === 'failed' ? 'red' : 'blue'">
                  {{ item.status }}
                </a-tag>
              </template>
              <template #description>事件 {{ item.eventId }}</template>
            </a-list-item-meta>
            <template #actions>
              <a v-if="item.downloadUrl" :href="item.downloadUrl" target="_blank">下载</a>
            </template>
          </a-list-item>
        </template>
      </a-list>
    </a-card>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { DownloadOutlined, FileProtectOutlined } from '@ant-design/icons-vue';
import { message } from 'ant-design-vue';
import dayjs, { type Dayjs } from 'dayjs';
import { listSecurityEvents, requestAuditReport } from '@/api/services';
import type { SecurityEventListItem, ReportJobResponse } from '@/types/api';
import { useAuditSessionStore } from '@/stores/auditSession';

const sessionStore = useAuditSessionStore();
const loading = ref(false);
const data = ref<SecurityEventListItem[]>([]);
const range = ref<[Dayjs, Dayjs] | null>(null);
const filterLevel = ref<string | undefined>(undefined);
const selectedRowKeys = ref<string[]>([]);
const batching = ref(false);
const exportingId = ref<string | null>(null);

interface ExportJob extends ReportJobResponse {
  eventId: string;
}
const jobs = ref<ExportJob[]>([]);

const levelOpts = [
  { value: '高危', label: '高危' },
  { value: '中危', label: '中危' },
  { value: '低危', label: '低危' },
];

const columns = [
  { title: '事件 ID', dataIndex: 'id', width: 160 },
  { title: '时间', dataIndex: 'time', width: 180 },
  { title: '类型', dataIndex: 'type', width: 160 },
  { title: '等级', dataIndex: 'level', width: 100 },
  { title: '处置结果', dataIndex: 'result' },
  { title: '操作', dataIndex: 'op', width: 200, fixed: 'right' as const },
];

const filtered = computed(() => {
  let list = data.value;
  if (filterLevel.value) list = list.filter((r) => r.level === filterLevel.value);
  if (range.value) {
    const [s, e] = range.value;
    list = list.filter((r) => {
      const t = dayjs(r.time);
      return !t.isBefore(s) && !t.isAfter(e);
    });
  }
  return list;
});

async function load() {
  loading.value = true;
  try {
    const res = await listSecurityEvents({ page: 1, pageSize: 50 });
    data.value = res.items;
  } finally {
    loading.value = false;
  }
}

async function exportOne(id: string) {
  exportingId.value = id;
  try {
    const job = await requestAuditReport(id);
    jobs.value = [{ ...job, eventId: id }, ...jobs.value];
    if (job.downloadUrl) {
      message.success(`报告 ${id} 已就绪`);
    }
  } catch {
    message.error(`${id} 报告导出失败`);
  } finally {
    exportingId.value = null;
  }
}

async function batchExport() {
  const ids = selectedRowKeys.value.length ? selectedRowKeys.value : filtered.value.map((r) => r.id);
  if (!ids.length) {
    message.info('暂无可导出的事件');
    return;
  }
  batching.value = true;
  try {
    for (const id of ids) await exportOne(id);
    message.success(`已批量提交 ${ids.length} 份报告`);
  } finally {
    batching.value = false;
  }
}

function openEvidence(id: string) {
  sessionStore.openEvent(id);
}

onMounted(load);
</script>

<style scoped>
.report-center {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.head-card,
.table-card,
.job-card {
  background: rgba(255, 255, 255, 0.92);
}
.head-card {
  background: linear-gradient(135deg, rgba(238, 242, 255, 0.85) 0%, rgba(255, 255, 255, 0.92) 50%, rgba(207, 250, 254, 0.6) 100%) !important;
  border: 1px solid rgba(99, 102, 241, 0.18) !important;
}
.title {
  font-size: 16px;
  font-weight: 700;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  color: #0F172A;
}
.title :deep(.anticon) {
  color: #6366F1;
  font-size: 18px;
}
.sub {
  margin: 4px 0 0;
  font-size: 12.5px;
  color: #64748B;
}
.mono {
  font-family: 'SFMono-Regular', Consolas, Menlo, monospace;
  margin-right: 8px;
  color: #4338CA;
  font-weight: 500;
}
</style>
