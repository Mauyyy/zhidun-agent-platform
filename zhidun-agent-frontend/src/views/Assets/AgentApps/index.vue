<template>
  <div class="assets-unified-page">
    <a-row :gutter="[16, 16]" class="section-row">
      <a-col :span="24">
        <a-card :bordered="false" size="small" class="card">
          <template #title>
            <span class="title"><database-outlined /> 敏感资源盘点</span>
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
              <a-button type="primary" size="small" @click="openCreateAsset"><plus-outlined /> 录入资产</a-button>
            </a-space>
          </template>

          <a-table
            size="small"
            :loading="assetsLoading"
            :data-source="filteredAssets"
            :columns="assetColumns"
            row-key="id"
            :pagination="{ pageSize: 10 }"
            :scroll="{ x: 900 }"
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
                <a-button type="link" size="small" @click="openEditAsset(record)">编辑</a-button>
              </template>
            </template>
          </a-table>
        </a-card>
      </a-col>
    </a-row>

    <a-row :gutter="[16, 16]" class="section-row">
      <a-col :span="24">
        <a-card :bordered="false" size="small" class="card">
          <template #title><span class="title"><robot-outlined /> 接入应用管理</span></template>
          <template #extra>
            <a-button type="primary" size="small" @click="openCreateApp"><plus-outlined /> 接入应用</a-button>
          </template>

          <a-row :gutter="[16, 16]">
            <a-col v-for="row in appRows" :key="row.id" :xs="24" :md="12" :xl="8">
              <div class="app-card" :class="row.status">
                <div class="app-head">
                  <a-avatar size="small" class="logo">{{ row.name.slice(0, 1) }}</a-avatar>
                  <div class="app-meta">
                    <div class="name">{{ row.name }}</div>
                    <div class="scenario">{{ row.scenario }}</div>
                  </div>
                  <a-tag :color="statusColor(row.status)">{{ statusLabel(row.status) }}</a-tag>
                </div>
                <a-descriptions size="small" :column="1" class="desc">
                  <a-descriptions-item label="API Key">
                    <span class="mono">{{ row.apiKey }}</span>
                  </a-descriptions-item>
                  <a-descriptions-item label="实时 RPS">{{ row.rps }} req/s</a-descriptions-item>
                  <a-descriptions-item label="绑定角色">
                    <a-tag v-for="r in row.bindRoles" :key="r" size="small">{{ r }}</a-tag>
                  </a-descriptions-item>
                  <a-descriptions-item label="心跳">{{ row.lastHeartbeat }}</a-descriptions-item>
                </a-descriptions>
                <div class="actions">
                  <a-button size="small" @click="openEditApp(row)">编辑</a-button>
                  <a-button size="small" @click="cycleStatus(row)">
                    {{ row.status === 'online' ? '暂停' : '启动' }}
                  </a-button>
                </div>
              </div>
            </a-col>
          </a-row>
        </a-card>
      </a-col>
    </a-row>

    <a-modal
      v-model:open="appModalOpen"
      :title="appForm.id ? '编辑应用' : '接入应用'"
      :confirm-loading="appSubmitting"
      @ok="submitApp"
    >
      <a-form layout="vertical" :model="appForm">
        <a-form-item label="应用名称" required><a-input v-model:value="appForm.name" /></a-form-item>
        <a-form-item label="业务场景"><a-input v-model:value="appForm.scenario" /></a-form-item>
        <a-form-item label="API Key">
          <a-input v-model:value="appForm.apiKey" />
        </a-form-item>
        <a-form-item label="绑定角色">
          <a-select v-model:value="appForm.bindRoles" mode="tags" :token-separators="[',']" />
        </a-form-item>
      </a-form>
    </a-modal>

    <a-modal
      v-model:open="assetModalOpen"
      :title="assetForm.id ? '编辑资产' : '录入敏感资产'"
      :confirm-loading="assetSubmitting"
      @ok="submitAsset"
    >
      <a-form layout="vertical" :model="assetForm">
        <a-form-item label="资产名称" required><a-input v-model:value="assetForm.name" /></a-form-item>
        <a-row :gutter="12">
          <a-col :span="12">
            <a-form-item label="类型">
              <a-select v-model:value="assetForm.type" :options="typeOpts" />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="敏感等级">
              <a-select v-model:value="assetForm.level" :options="['L1', 'L2', 'L3', 'L4'].map((v) => ({ value: v, label: v }))" />
            </a-form-item>
          </a-col>
        </a-row>
        <a-form-item label="标识符（路径 / 表名 / Glob）">
          <a-input v-model:value="assetForm.identifier" placeholder="如 /admin/config 或 tb_customer_info" />
        </a-form-item>
        <a-form-item label="负责人"><a-input v-model:value="assetForm.owner" /></a-form-item>
        <a-form-item label="说明"><a-textarea v-model:value="assetForm.description" :rows="2" /></a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { DatabaseOutlined, PlusOutlined, RobotOutlined } from '@ant-design/icons-vue';
import { message } from 'ant-design-vue';
import { listAgentApps, listSensitiveAssets, saveAgentApp, saveSensitiveAsset } from '@/api/services';
import type { AgentApp, SensitiveAsset } from '@/types/api';

const appRows = ref<AgentApp[]>([]);
const appModalOpen = ref(false);
const appSubmitting = ref(false);
const appForm = ref<AgentApp>(emptyApp());

const assetsLoading = ref(false);
const assetRows = ref<SensitiveAsset[]>([]);
const filterLevel = ref<string | undefined>();
const filterType = ref<string | undefined>();
const assetModalOpen = ref(false);
const assetSubmitting = ref(false);
const assetForm = ref<SensitiveAsset>(emptyAsset());

const filteredAssets = computed(() => {
  return assetRows.value.filter((r) => {
    if (filterLevel.value && r.level !== filterLevel.value) return false;
    if (filterType.value && r.type !== filterType.value) return false;
    return true;
  });
});

const assetColumns = [
  { title: '资产名称', dataIndex: 'name', width: 180 },
  { title: '类型', dataIndex: 'type', width: 110 },
  { title: '标识符', dataIndex: 'identifier', ellipsis: true },
  { title: '敏感等级', dataIndex: 'level', width: 100 },
  { title: '负责人', dataIndex: 'owner', width: 120 },
  { title: '操作', dataIndex: 'op', width: 100, align: 'right' as const },
];

const typeOpts = [
  { value: 'api', label: 'API' },
  { value: 'directory', label: '目录' },
  { value: 'db_table', label: '数据库表' },
  { value: 'file_pattern', label: '文件 Glob' },
];

function emptyApp(): AgentApp {
  return {
    id: '',
    name: '',
    scenario: '',
    apiKey: '',
    rps: 0,
    status: 'online',
    bindRoles: [],
    lastHeartbeat: new Date().toISOString().replace('T', ' ').slice(0, 19),
  };
}

function emptyAsset(): SensitiveAsset {
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

function statusLabel(s: AgentApp['status']) {
  return s === 'online' ? '在线' : s === 'paused' ? '已暂停' : '离线';
}

function statusColor(s: AgentApp['status']) {
  return s === 'online' ? 'green' : s === 'paused' ? 'orange' : 'default';
}

function typeLabel(t: SensitiveAsset['type']) {
  return typeOpts.find((o) => o.value === t)?.label ?? t;
}

async function load() {
  const [apps, assets] = await Promise.all([listAgentApps(), listSensitiveAssets()]);
  appRows.value = apps;
  assetRows.value = assets;
}

function openCreateApp() {
  appForm.value = emptyApp();
  appModalOpen.value = true;
}

function openEditApp(r: AgentApp) {
  appForm.value = { ...r };
  appModalOpen.value = true;
}

async function submitApp() {
  if (!appForm.value.name) return message.warning('请填写应用名称');
  appSubmitting.value = true;
  try {
    const saved = await saveAgentApp(appForm.value);
    const i = appRows.value.findIndex((r) => r.id === saved.id);
    if (i >= 0) appRows.value[i] = saved;
    else appRows.value = [...appRows.value, saved];
    appModalOpen.value = false;
    message.success('应用已保存');
  } finally {
    appSubmitting.value = false;
  }
}

async function cycleStatus(r: AgentApp) {
  const next: AgentApp['status'] = r.status === 'online' ? 'paused' : 'online';
  const saved = await saveAgentApp({ ...r, status: next });
  Object.assign(r, saved);
}

function openCreateAsset() {
  assetForm.value = emptyAsset();
  assetModalOpen.value = true;
}

function openEditAsset(r: SensitiveAsset) {
  assetForm.value = { ...r };
  assetModalOpen.value = true;
}

async function submitAsset() {
  if (!assetForm.value.name) return message.warning('请填写资产名称');
  assetSubmitting.value = true;
  try {
    const saved = await saveSensitiveAsset(assetForm.value);
    const i = assetRows.value.findIndex((r) => r.id === saved.id);
    if (i >= 0) assetRows.value[i] = saved;
    else assetRows.value = [...assetRows.value, saved];
    assetModalOpen.value = false;
    message.success('资产已保存');
  } finally {
    assetSubmitting.value = false;
  }
}

onMounted(async () => {
  assetsLoading.value = true;
  try {
    await load();
  } finally {
    assetsLoading.value = false;
  }
});
</script>

<style scoped>
.assets-unified-page {
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

.app-card {
  background: linear-gradient(165deg, rgba(255, 255, 255, 0.96), rgba(238, 242, 255, 0.85));
  border: 1px solid rgba(99, 102, 241, 0.22);
  border-radius: 14px;
  padding: 14px 16px;
  box-shadow: 0 4px 12px -4px rgba(99, 102, 241, 0.18);
  transition: transform 0.22s ease, box-shadow 0.22s ease, border-color 0.22s ease;
}

.app-card:hover {
  transform: translateY(-2px);
  border-color: rgba(99, 102, 241, 0.4);
  box-shadow: 0 10px 22px -8px rgba(99, 102, 241, 0.32);
}

.app-card.paused {
  border-color: rgba(245, 158, 11, 0.32);
  background: linear-gradient(165deg, rgba(255, 252, 245, 0.96), rgba(254, 243, 199, 0.78));
}

.app-card.paused:hover {
  box-shadow: 0 10px 22px -8px rgba(245, 158, 11, 0.32);
}

.app-card.offline {
  filter: grayscale(0.45) opacity(0.85);
}

.app-head {
  display: flex;
  align-items: center;
  gap: 10px;
}

.logo {
  background: linear-gradient(135deg, #6366F1, #8B5CF6) !important;
  color: #fff !important;
  font-weight: 600;
  box-shadow: 0 4px 10px rgba(99, 102, 241, 0.4);
}

/* 直接命中 ant-avatar 本体，避免 scoped 下被组件内部样式覆盖 */
:deep(.logo.ant-avatar) {
  width: 32px !important;
  min-width: 32px !important;
  max-width: 32px !important;
  height: 32px !important;
  min-height: 32px !important;
  max-height: 32px !important;
  line-height: 32px !important;
  border-radius: 999px !important;
  aspect-ratio: 1 / 1;
  display: inline-flex !important;
  align-items: center;
  justify-content: center;
  flex: 0 0 32px;
}

:deep(.logo.ant-avatar .ant-avatar-string) {
  line-height: 1 !important;
}

.app-card.paused .logo {
  background: linear-gradient(135deg, #F59E0B, #F97316) !important;
  box-shadow: 0 4px 10px rgba(245, 158, 11, 0.4);
}

.app-meta {
  flex: 1;
  min-width: 0;
}

.name {
  font-weight: 600;
  font-size: 14px;
  color: #0F172A;
}

.scenario {
  font-size: 11.5px;
  color: #64748B;
}

.mono {
  font-family: monospace;
  font-size: 12px;
  color: #4338CA;
}

.desc {
  margin-top: 6px;
}

.actions {
  margin-top: 8px;
  display: flex;
  gap: 8px;
}
</style>
