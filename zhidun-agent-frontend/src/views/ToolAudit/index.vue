<template>
  <div class="tool-audit-container">
    <!-- 策略配置大盘：置顶，便于先选行再查看下方审计流 -->
    <a-card :bordered="false" class="main-card main-card--top">
      <template #title>
        <div class="card-title">
          <api-outlined style="color: #6366F1; margin-right: 8px" />
          大模型工具调度与 RBAC 策略大盘
        </div>
      </template>
      <template #extra>
        <a-button type="primary" class="add-btn" @click="openCreate">
          <plus-outlined /> 注册新工具约束
        </a-button>
      </template>

      <a-alert
        message="架构说明：代理网关层管控"
        description="系统在模型生成 Function Calling 后、工具实际执行前，对工具名称、参数范围和资源对象进行审查，任何超出策略边界的请求都将被标记为越权并阻断。"
        type="info"
        show-icon
        style="margin-bottom: 24px"
      />

      <a-table
        :columns="columns"
        :data-source="toolData"
        bordered
        row-key="id"
        :loading="loading"
        :custom-row="customRow"
        :row-class-name="rowClassName"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'rbac'">
            <a-tag v-for="role in record.rbac" :key="role" color="blue">
              {{ role }}
            </a-tag>
          </template>

          <template v-if="column.key === 'level'">
            <a-tag :color="record.level === 'L4' ? 'red' : record.level === 'L3' ? 'orange' : 'green'">
              {{ record.level }} 级敏感度
            </a-tag>
          </template>

          <template v-if="column.key === 'status'">
            <div class="status-cell">
              <span class="dot" :class="record.active ? 'active' : 'inactive'"></span>
              <span>{{ record.active ? '监控中' : '已停用' }}</span>
              <span class="block-count"> (本周拦截: {{ record.blockCount }} 次)</span>
            </div>
          </template>

          <template v-if="column.key === 'action'">
            <a-button type="link" size="small" @click.stop="openEdit(record)">编辑策略</a-button>
            <a-divider type="vertical" />
            <a-button type="link" size="small" danger :disabled="!record.active" @click.stop="onDisable(record)">
              停用
            </a-button>
          </template>
        </template>
      </a-table>
    </a-card>

    <!-- 工具调用审计流：源 JSON → 校验矩阵 → 裁决 -->
    <a-row :gutter="20" class="flow-row" align="stretch">
      <a-col :xs="24" :lg="8" class="flow-col">
        <a-card :bordered="false" class="flow-card flow-card--left">
          <template #title>
            <div class="flow-card-title">
              <code-outlined class="title-icon" />
              模型原始请求（Function Calling）
            </div>
          </template>
          <p class="flow-hint">在上方策略表中选中一行，可联动查看该工具的模拟调用载荷。</p>
          <div class="json-box">
            <vue-json-pretty v-if="flowPayload" :data="flowPayload" :deep="4" show-line theme="light" />
            <a-empty v-else description="暂无选中策略" />
          </div>
        </a-card>
      </a-col>

      <a-col :xs="24" :lg="10" class="flow-col">
        <a-card :bordered="false" class="flow-card flow-card--mid">
          <template #title>
            <div class="flow-card-title">
              <team-outlined class="title-icon" />
              RBAC 与参数校验
            </div>
          </template>
          <div class="flow-mid-stack">
            <div class="sub-block">
              <div class="sub-title">角色—资源矩阵（示意）</div>
              <a-table
                :columns="rbacColumns"
                :data-source="rbacMatrix"
                size="small"
                :pagination="false"
                row-key="key"
                bordered
              />
            </div>
            <div class="sub-block sub-block--grow">
              <div class="sub-title">参数与边界审计</div>
              <a-table
                :columns="paramColumns"
                :data-source="paramAuditRows"
                size="small"
                :pagination="false"
                row-key="key"
                bordered
              >
                <template #bodyCell="{ column, record }">
                  <template v-if="column.key === 'pass'">
                    <a-tag :color="record.pass ? 'success' : 'error'">{{ record.pass ? '通过' : '不通过' }}</a-tag>
                  </template>
                </template>
              </a-table>
            </div>
          </div>
        </a-card>
      </a-col>

      <a-col :xs="24" :lg="6" class="flow-col">
        <a-card :bordered="false" class="flow-card verdict-flow-card flow-card--right">
          <template #title>
            <div class="flow-card-title">
              <audit-outlined class="title-icon" />
              执行裁决
            </div>
          </template>
          <div class="verdict-flow-body">
            <div class="verdict-badge-wrap">
              <a-result
                :status="flowVerdictBlocked ? 'error' : 'success'"
                :title="flowVerdictBlocked ? '拦截' : '放行'"
                :sub-title="flowVerdictSub"
              />
            </div>
            <div class="reason-head">拦截 / 关注原因</div>
            <a-list size="small" bordered :data-source="flowReasons" class="reason-list">
              <template #renderItem="{ item }">
                <a-list-item>{{ item }}</a-list-item>
              </template>
            </a-list>
          </div>
        </a-card>
      </a-col>
    </a-row>

    <a-modal
      v-model:open="modalOpen"
      :title="editingId ? '编辑工具约束' : '注册新工具约束'"
      :confirm-loading="submitting"
      destroy-on-close
      @ok="submitForm"
    >
      <a-form layout="vertical" :model="form">
        <a-form-item label="工具标识 (Function Name)" required>
          <a-input v-model:value="form.name" placeholder="例如 read_system_file" :disabled="!!editingId" />
        </a-form-item>
        <a-form-item label="功能描述" required>
          <a-input v-model:value="form.desc" placeholder="简要说明工具用途" />
        </a-form-item>
        <a-form-item label="参数约束 (正则/范围说明)" required>
          <a-textarea v-model:value="form.constraints" :rows="3" placeholder="路径前缀、禁止字段、返回条数上限等" />
        </a-form-item>
        <a-form-item label="敏感级别" required>
          <a-select v-model:value="form.level" style="width: 100%">
            <a-select-option value="L1">L1</a-select-option>
            <a-select-option value="L2">L2</a-select-option>
            <a-select-option value="L3">L3</a-select-option>
            <a-select-option value="L4">L4</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="RBAC 角色白名单" required>
          <a-select v-model:value="form.rbac" mode="tags" style="width: 100%" placeholder="输入角色标识后回车，如 admin" />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue';
import { ApiOutlined, PlusOutlined, CodeOutlined, TeamOutlined, AuditOutlined } from '@ant-design/icons-vue';
import { message } from 'ant-design-vue';
import VueJsonPretty from 'vue-json-pretty';
import 'vue-json-pretty/lib/styles.css';
import { listToolPolicies, createToolPolicy, updateToolPolicy } from '@/api/services';
import type { ToolPolicy, SensitivityLevel } from '@/types/api';

const columns = [
  { title: '工具标识 (Function Name)', dataIndex: 'name', key: 'name', width: 200 },
  { title: '功能描述', dataIndex: 'desc', key: 'desc' },
  { title: '参数约束 (正则/范围)', dataIndex: 'constraints', key: 'constraints', width: 250 },
  { title: '敏感级别', dataIndex: 'level', key: 'level', width: 120 },
  { title: 'RBAC 角色白名单', dataIndex: 'rbac', key: 'rbac', width: 200 },
  { title: '运行状态与审计统计', dataIndex: 'status', key: 'status', width: 220 },
  { title: '操作', key: 'action', width: 150 },
];

const rbacColumns = [
  { title: '角色', dataIndex: 'role', key: 'role', width: 100 },
  { title: '资源域', dataIndex: 'res', key: 'res' },
  { title: '默认策略', dataIndex: 'allow', key: 'allow', width: 88 },
];

const rbacMatrix = [
  { key: '1', role: 'admin', res: 'L4 数据 / 系统配置', allow: '受限放行' },
  { key: '2', role: 'manager', res: 'L3 业务文档', allow: '条件放行' },
  { key: '3', role: 'guest', res: '公开 FAQ', allow: '允许' },
];

const paramColumns = [
  { title: '检查项', dataIndex: 'name', key: 'name', width: 120 },
  { title: '策略/期望', dataIndex: 'expect', key: 'expect' },
  { title: '本次请求', dataIndex: 'actual', key: 'actual' },
  { title: '结果', dataIndex: 'pass', key: 'pass', width: 88 },
];

const loading = ref(false);
const toolData = ref<ToolPolicy[]>([]);
const selectedId = ref<string | null>(null);
const modalOpen = ref(false);
const submitting = ref(false);
const editingId = ref<string | null>(null);

const form = ref({
  name: '',
  desc: '',
  constraints: '',
  level: 'L3' as SensitivityLevel,
  rbac: [] as string[],
});

const selectedPolicy = computed(() => toolData.value.find((r) => r.id === selectedId.value) ?? null);

const flowPayload = computed(() => {
  const row = selectedPolicy.value;
  if (!row) return null;
  const high = row.level === 'L4';
  return {
    tool: row.name,
    arguments: high
      ? { query: 'SELECT password, phone FROM customers LIMIT 100', reason: '演示：触及 L4 数据域' }
      : { path: '/public/docs/overview.md', preview: true },
    meta: {
      caller_role: row.rbac[0] ?? 'unknown',
      policy_level: row.level,
      simulated: true,
    },
  };
});

const paramAuditRows = computed(() => {
  const row = selectedPolicy.value;
  if (!row)
    return [
      { key: 'p0', name: '—', expect: '—', actual: '—', pass: true },
    ];
  const boundaryFail = row.level === 'L4';
  return [
    {
      key: 'p1',
      name: '工具注册',
      expect: '已在策略表激活',
      actual: row.active ? `已注册 · ${row.name}` : '策略已停用',
      pass: row.active,
    },
    {
      key: 'p2',
      name: '敏感级别',
      expect: '与 RBAC 绑定一致',
      actual: `${row.level} · ${row.desc}`,
      pass: true,
    },
    {
      key: 'p3',
      name: '参数边界',
      expect: row.constraints,
      actual: boundaryFail ? '模拟请求超出高敏资源边界' : '参数落在允许范围内',
      pass: !boundaryFail,
    },
  ];
});

const flowVerdictBlocked = computed(() => {
  const row = selectedPolicy.value;
  if (!row) return false;
  if (!row.active) return true;
  return row.level === 'L4';
});

const flowVerdictSub = computed(() => {
  const row = selectedPolicy.value;
  if (!row) return '请选择一条工具策略';
  if (!row.active) return '策略处于停用状态，网关将拒绝此类调用。';
  if (row.level === 'L4') return '演示载荷命中 L4 资源，执行前强制阻断。';
  return '模拟载荷通过 RBAC 与参数边界校验，可进入受控执行。';
});

const flowReasons = computed(() => {
  const row = selectedPolicy.value;
  if (!row) return ['在表格中选择一行策略以查看原因列表。'];
  if (!row.active) return ['策略未启用，所有指向该工具的调用将被直接拒绝。'];
  if (row.level === 'L4') {
    return [
      '调用参数涉及 L4 级敏感资源（演示）。',
      '当前模拟角色与数据域不匹配或缺少二次审批。',
      `策略约束：${row.constraints}`,
    ];
  }
  return ['未发现越权与参数越界（演示数据）。', `工具「${row.name}」处于监控中，本周拦截 ${row.blockCount} 次异常调用。`];
});

function customRow(record: ToolPolicy) {
  return {
    onClick: () => {
      selectedId.value = record.id;
    },
    style: { cursor: 'pointer' },
  };
}

function rowClassName(record: ToolPolicy) {
  return record.id === selectedId.value ? 'row-selected' : '';
}

async function refresh() {
  loading.value = true;
  try {
    toolData.value = await listToolPolicies();
  } catch {
    message.error('加载策略列表失败');
  } finally {
    loading.value = false;
  }
}

watch(
  toolData,
  (rows) => {
    if (!rows.length) {
      selectedId.value = null;
      return;
    }
    if (!rows.some((r) => r.id === selectedId.value)) {
      selectedId.value = rows[0].id;
    }
  },
  { immediate: true }
);

onMounted(() => {
  refresh();
});

function openCreate() {
  editingId.value = null;
  form.value = {
    name: '',
    desc: '',
    constraints: '',
    level: 'L3',
    rbac: [],
  };
  modalOpen.value = true;
}

function openEdit(row: ToolPolicy) {
  editingId.value = row.id;
  form.value = {
    name: row.name,
    desc: row.desc,
    constraints: row.constraints,
    level: row.level,
    rbac: [...row.rbac],
  };
  modalOpen.value = true;
}

async function submitForm() {
  const f = form.value;
  if (!f.name?.trim() || !f.desc?.trim() || !f.constraints?.trim() || !f.rbac.length) {
    message.warning('请填写完整信息');
    return;
  }
  submitting.value = true;
  try {
    if (editingId.value) {
      await updateToolPolicy(editingId.value, {
        desc: f.desc,
        constraints: f.constraints,
        level: f.level,
        rbac: f.rbac,
      });
      message.success('策略已更新');
    } else {
      await createToolPolicy({
        name: f.name.trim(),
        desc: f.desc.trim(),
        constraints: f.constraints.trim(),
        level: f.level,
        rbac: f.rbac,
      });
      message.success('已注册新工具约束');
    }
    modalOpen.value = false;
    await refresh();
  } catch {
    message.error('保存失败');
  } finally {
    submitting.value = false;
  }
}

async function onDisable(row: ToolPolicy) {
  submitting.value = true;
  try {
    await updateToolPolicy(row.id, { active: false });
    message.success('已停用');
    await refresh();
  } catch {
    message.error('操作失败');
  } finally {
    submitting.value = false;
  }
}
</script>

<style scoped>
.tool-audit-container {
  padding: 8px 0;
}

.main-card--top {
  margin-bottom: 24px;
}

.flow-row {
  margin-bottom: 0;
}

.flow-col {
  display: flex;
  flex-direction: column;
  min-height: 0;
  margin-bottom: 16px;
}
@media (min-width: 992px) {
  .flow-col {
    margin-bottom: 0;
    align-self: stretch;
  }
}

.flow-card {
  position: relative;
  border-radius: 14px;
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: linear-gradient(165deg, rgba(255, 255, 255, 0.88) 0%, rgba(248, 250, 255, 0.74) 100%) !important;
  border: 1px solid rgba(200, 204, 232, 0.55) !important;
  box-shadow: 0 0 0 1px rgba(255, 255, 255, 0.75) inset, 0 8px 28px rgba(124, 139, 219, 0.12) !important;
}
.flow-card :deep(.ant-card-body) {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.flow-card--left :deep(.ant-card-body) {
  gap: 0;
}
.flow-card--mid :deep(.ant-card-body),
.flow-card--right :deep(.ant-card-body) {
  gap: 0;
}
.flow-card-title {
  display: flex;
  align-items: center;
  font-size: 15px;
  font-weight: 600;
}
.title-icon {
  color: #6366F1;
  margin-right: 8px;
  font-size: 16px;
}
.flow-hint {
  font-size: 12px;
  color: #94a3b8;
  margin: 0 0 12px;
  flex-shrink: 0;
}
.json-box {
  flex: 1;
  min-height: 200px;
  background: linear-gradient(165deg, #0F172A 0%, #1E1B4B 100%);
  border-radius: 12px;
  border: 1px solid rgba(99, 102, 241, 0.28);
  padding: 12px 14px;
  overflow: auto;
  box-shadow: inset 0 1px 0 rgba(99, 102, 241, 0.12);
}
.json-box :deep(.vjs-tree) {
  color: #E0E7FF;
}
.json-box :deep(.vjs-key) {
  color: #A5B4FC;
}
.json-box :deep(.vjs-value-string) {
  color: #6EE7B7;
}
.json-box :deep(.vjs-value-number),
.json-box :deep(.vjs-value-boolean) {
  color: #67E8F9;
}
.json-box :deep(.vjs-tree-node .vjs-indent-unit.has-line) {
  border-left-color: rgba(99, 102, 241, 0.32);
}

.flow-mid-stack {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  gap: 16px;
  overflow: hidden;
}

.sub-block {
  flex-shrink: 0;
}
.sub-block--grow {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.sub-block--grow :deep(.ant-table-wrapper) {
  flex: 1;
  min-height: 0;
  overflow: auto;
}
.sub-title {
  font-size: 13px;
  font-weight: 600;
  color: #475569;
  margin-bottom: 8px;
}

.verdict-flow-card :deep(.ant-result) {
  padding: 12px 8px 0;
}
.verdict-flow-card :deep(.ant-result-title) {
  font-size: 22px;
  font-weight: 700;
}
.verdict-flow-body {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.verdict-badge-wrap {
  flex-shrink: 0;
}
.reason-head {
  font-size: 13px;
  font-weight: 600;
  margin: 4px 0 0;
  color: #6b7280;
  flex-shrink: 0;
}
.reason-list {
  flex: 1;
  min-height: 80px;
  overflow-y: auto;
  margin-top: 4px;
}

.main-card {
  position: relative;
  border-radius: 14px;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.92) !important;
  border: 1px solid rgba(148, 163, 184, 0.22) !important;
  box-shadow: 0 0 0 1px rgba(255, 255, 255, 0.85) inset, 0 8px 24px -8px rgba(15, 23, 42, 0.08) !important;
}
.card-title {
  font-size: 18px;
  font-weight: 600;
  color: #0F172A;
}
.status-cell {
  display: flex;
  align-items: center;
}
.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  margin-right: 8px;
}
.dot.active {
  background-color: #10B981;
  box-shadow: 0 0 6px rgba(16, 185, 129, 0.7);
}
.dot.inactive {
  background-color: #94A3B8;
}
.block-count {
  margin-left: 8px;
  color: #E11D48;
  font-size: 12px;
  font-weight: 600;
}
.add-btn {
  border-radius: 8px;
}

:deep(.row-selected) > td {
  background: rgba(238, 242, 255, 0.95) !important;
}
</style>
