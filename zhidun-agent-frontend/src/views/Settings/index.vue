<template>
  <div class="settings-unified-page">
    <a-row :gutter="[16, 16]" class="section-row">
      <a-col :span="24">
        <a-card :bordered="false" size="small" class="card">
          <template #title>
            <span class="title"><notification-outlined /> 告警路由与通知设置</span>
          </template>
          <template #extra>
            <a-button type="primary" size="small" @click="openCreateRoute"><plus-outlined /> 新增路由</a-button>
          </template>

          <a-table
            size="small"
            :loading="routeLoading"
            :data-source="routeRows"
            :columns="routeColumns"
            row-key="id"
            :pagination="{ pageSize: 10 }"
            :scroll="{ x: 980 }"
          >
            <template #bodyCell="{ column, record }">
              <template v-if="column.dataIndex === 'channel'">
                <a-tag :color="channelColor(record.channel)">{{ channelLabel(record.channel) }}</a-tag>
              </template>
              <template v-else-if="column.dataIndex === 'triggerLevels'">
                <a-tag v-for="lv in record.triggerLevels" :key="lv" :color="levelColor(lv)">
                  {{ levelLabel(lv) }}
                </a-tag>
              </template>
              <template v-else-if="column.dataIndex === 'enabled'">
                <a-switch
                  size="small"
                  :checked="record.enabled"
                  @change="(v: boolean) => onToggleRoute(record, v)"
                />
              </template>
              <template v-else-if="column.dataIndex === 'op'">
                <a-button type="link" size="small" @click="openEditRoute(record)">编辑</a-button>
                <a-button type="link" size="small" @click="testRoute(record)">测试推送</a-button>
              </template>
            </template>
          </a-table>
        </a-card>
      </a-col>
    </a-row>

    <a-row :gutter="[16, 16]" class="section-row">
      <a-col :span="24">
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
            :loading="logLoading"
            :data-source="filteredLogs"
            :columns="logColumns"
            row-key="id"
            :pagination="logPagination"
            :scroll="{ x: 860 }"
            @change="onLogTableChange"
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
      </a-col>
    </a-row>

    <a-modal
      v-model:open="routeModalOpen"
      :title="routeForm.id ? '编辑路由' : '新增路由'"
      :confirm-loading="routeSubmitting"
      @ok="submitRoute"
    >
      <a-form layout="vertical" :model="routeForm">
        <a-form-item label="路由名称" required><a-input v-model:value="routeForm.name" /></a-form-item>
        <a-row :gutter="12">
          <a-col :span="12">
            <a-form-item label="通道">
              <a-select v-model:value="routeForm.channel" :options="channelOpts" />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="目标（地址 / Webhook URL）">
              <a-input v-model:value="routeForm.target" />
            </a-form-item>
          </a-col>
        </a-row>
        <a-form-item label="触发等级">
          <a-checkbox-group v-model:value="routeForm.triggerLevels">
            <a-checkbox value="low">低风险</a-checkbox>
            <a-checkbox value="mid">中风险</a-checkbox>
            <a-checkbox value="high">高风险</a-checkbox>
          </a-checkbox-group>
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { HistoryOutlined, NotificationOutlined, PlusOutlined } from '@ant-design/icons-vue';
import { message } from 'ant-design-vue';
import { listAlertRoutes, listOperationLogs, saveAlertRoute } from '@/api/services';
import type { AlertChannel, AlertRoute, OperationLog } from '@/types/api';

const routeLoading = ref(false);
const routeRows = ref<AlertRoute[]>([]);
const routeModalOpen = ref(false);
const routeSubmitting = ref(false);
const routeForm = ref<AlertRoute>(emptyRoute());

const routeColumns = [
  { title: '名称', dataIndex: 'name', width: 220 },
  { title: '通道', dataIndex: 'channel', width: 100 },
  { title: '目标', dataIndex: 'target', ellipsis: true },
  { title: '触发等级', dataIndex: 'triggerLevels', width: 220 },
  { title: '最近触发', dataIndex: 'lastTriggeredAt', width: 180 },
  { title: '启用', dataIndex: 'enabled', width: 80 },
  { title: '操作', dataIndex: 'op', width: 180, align: 'right' as const },
];

const channelOpts: Array<{ value: AlertChannel; label: string }> = [
  { value: 'feishu', label: '飞书' },
  { value: 'dingtalk', label: '钉钉' },
  { value: 'email', label: '邮件' },
  { value: 'sms', label: '短信' },
  { value: 'webhook', label: 'Webhook' },
];

const logLoading = ref(false);
const logRows = ref<OperationLog[]>([]);
const keyword = ref('');
const logPagination = ref({ current: 1, pageSize: 20, total: 0, showSizeChanger: true });

const logColumns = [
  { title: '时间', dataIndex: 'time', width: 180 },
  { title: '操作员', dataIndex: 'actor', width: 130 },
  { title: '动作', dataIndex: 'action', width: 200 },
  { title: '目标', dataIndex: 'target' },
  { title: 'IP', dataIndex: 'ip', width: 140 },
  { title: '结果', dataIndex: 'outcome', width: 100 },
];

const filteredLogs = computed(() => {
  const k = keyword.value.trim().toLowerCase();
  if (!k) return logRows.value;
  return logRows.value.filter((r) => [r.actor, r.action, r.target].some((s) => s.toLowerCase().includes(k)));
});

function emptyRoute(): AlertRoute {
  return {
    id: '',
    name: '',
    channel: 'feishu',
    target: '',
    triggerLevels: ['high'],
    enabled: true,
  };
}

function channelLabel(c: AlertChannel) {
  return channelOpts.find((o) => o.value === c)?.label ?? c;
}
function channelColor(c: AlertChannel) {
  if (c === 'webhook') return 'purple';
  if (c === 'feishu') return 'cyan';
  if (c === 'dingtalk') return 'blue';
  if (c === 'sms') return 'orange';
  return 'default';
}
function levelLabel(lv: string) {
  return lv === 'high' ? '高' : lv === 'mid' ? '中' : '低';
}
function levelColor(lv: string) {
  return lv === 'high' ? 'red' : lv === 'mid' ? 'orange' : 'green';
}

async function loadRoutes() {
  routeLoading.value = true;
  try {
    routeRows.value = await listAlertRoutes();
  } finally {
    routeLoading.value = false;
  }
}
async function loadLogs() {
  logLoading.value = true;
  try {
    const res = await listOperationLogs(logPagination.value.current, logPagination.value.pageSize);
    logRows.value = res.items;
    logPagination.value.total = res.total;
  } finally {
    logLoading.value = false;
  }
}

function openCreateRoute() {
  routeForm.value = emptyRoute();
  routeModalOpen.value = true;
}
function openEditRoute(r: AlertRoute) {
  routeForm.value = { ...r };
  routeModalOpen.value = true;
}

async function submitRoute() {
  if (!routeForm.value.name) return message.warning('请填写名称');
  if (!routeForm.value.target) return message.warning('请填写目标地址');
  routeSubmitting.value = true;
  try {
    const saved = await saveAlertRoute(routeForm.value);
    const i = routeRows.value.findIndex((r) => r.id === saved.id);
    if (i >= 0) routeRows.value[i] = saved;
    else routeRows.value = [...routeRows.value, saved];
    routeModalOpen.value = false;
    message.success('已保存');
  } finally {
    routeSubmitting.value = false;
  }
}
async function onToggleRoute(r: AlertRoute, v: boolean) {
  await saveAlertRoute({ ...r, enabled: v });
  r.enabled = v;
}
async function testRoute(r: AlertRoute) {
  await new Promise((res) => setTimeout(res, 400));
  message.success(`已向 ${r.target} 发送测试告警`);
}

function onLogTableChange(p: { current?: number; pageSize?: number }) {
  logPagination.value.current = p.current ?? 1;
  logPagination.value.pageSize = p.pageSize ?? 20;
  loadLogs();
}

onMounted(async () => {
  await Promise.all([loadRoutes(), loadLogs()]);
});
</script>

<style scoped>
.settings-unified-page {
  width: 100%;
  min-width: 0;
}
.section-row {
  margin: 0 !important;
}
.section-row + .section-row {
  margin-top: 22px !important;
}
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
