<template>
  <a-card :bordered="false" size="small" class="card">
    <template #title>
      <span class="title"><notification-outlined /> 告警路由与通知设置</span>
    </template>
    <template #extra>
      <a-button type="primary" size="small" @click="openCreate"><plus-outlined /> 新增路由</a-button>
    </template>

    <a-table
      size="small"
      :loading="loading"
      :data-source="rows"
      :columns="columns"
      row-key="id"
      :pagination="{ pageSize: 10 }"
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
            @change="(v: boolean) => onToggle(record, v)"
          />
        </template>
        <template v-else-if="column.dataIndex === 'op'">
          <a-button type="link" size="small" @click="openEdit(record)">编辑</a-button>
          <a-button type="link" size="small" @click="testRoute(record)">测试推送</a-button>
        </template>
      </template>
    </a-table>
  </a-card>

  <a-modal
    v-model:open="modalOpen"
    :title="form.id ? '编辑路由' : '新增路由'"
    :confirm-loading="submitting"
    @ok="submit"
  >
    <a-form layout="vertical" :model="form">
      <a-form-item label="路由名称" required><a-input v-model:value="form.name" /></a-form-item>
      <a-row :gutter="12">
        <a-col :span="12">
          <a-form-item label="通道">
            <a-select v-model:value="form.channel" :options="channelOpts" />
          </a-form-item>
        </a-col>
        <a-col :span="12">
          <a-form-item label="目标（地址 / Webhook URL）">
            <a-input v-model:value="form.target" />
          </a-form-item>
        </a-col>
      </a-row>
      <a-form-item label="触发等级">
        <a-checkbox-group v-model:value="form.triggerLevels">
          <a-checkbox value="low">低风险</a-checkbox>
          <a-checkbox value="mid">中风险</a-checkbox>
          <a-checkbox value="high">高风险</a-checkbox>
        </a-checkbox-group>
      </a-form-item>
    </a-form>
  </a-modal>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { NotificationOutlined, PlusOutlined } from '@ant-design/icons-vue';
import { message } from 'ant-design-vue';
import { listAlertRoutes, saveAlertRoute } from '@/api/services';
import type { AlertChannel, AlertRoute } from '@/types/api';

const loading = ref(false);
const rows = ref<AlertRoute[]>([]);

const columns = [
  { title: '名称', dataIndex: 'name', width: 220 },
  { title: '通道', dataIndex: 'channel', width: 100 },
  { title: '目标', dataIndex: 'target', ellipsis: true },
  { title: '触发等级', dataIndex: 'triggerLevels', width: 220 },
  { title: '最近触发', dataIndex: 'lastTriggeredAt', width: 180 },
  { title: '启用', dataIndex: 'enabled', width: 80 },
  { title: '操作', dataIndex: 'op', width: 180, fixed: 'right' as const },
];

const channelOpts: Array<{ value: AlertChannel; label: string }> = [
  { value: 'feishu', label: '飞书' },
  { value: 'dingtalk', label: '钉钉' },
  { value: 'email', label: '邮件' },
  { value: 'sms', label: '短信' },
  { value: 'webhook', label: 'Webhook' },
];

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

const modalOpen = ref(false);
const submitting = ref(false);
const form = ref<AlertRoute>(empty());
function empty(): AlertRoute {
  return {
    id: '',
    name: '',
    channel: 'feishu',
    target: '',
    triggerLevels: ['high'],
    enabled: true,
  };
}

async function load() {
  loading.value = true;
  try {
    rows.value = await listAlertRoutes();
  } finally {
    loading.value = false;
  }
}
function openCreate() {
  form.value = empty();
  modalOpen.value = true;
}
function openEdit(r: AlertRoute) {
  form.value = { ...r };
  modalOpen.value = true;
}
async function submit() {
  if (!form.value.name) return message.warning('请填写名称');
  if (!form.value.target) return message.warning('请填写目标地址');
  submitting.value = true;
  try {
    const saved = await saveAlertRoute(form.value);
    const i = rows.value.findIndex((r) => r.id === saved.id);
    if (i >= 0) rows.value[i] = saved;
    else rows.value = [...rows.value, saved];
    modalOpen.value = false;
    message.success('已保存');
  } finally {
    submitting.value = false;
  }
}
async function onToggle(r: AlertRoute, v: boolean) {
  await saveAlertRoute({ ...r, enabled: v });
  r.enabled = v;
}
async function testRoute(r: AlertRoute) {
  await new Promise((res) => setTimeout(res, 400));
  message.success(`已向 ${r.target} 发送测试告警`);
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
