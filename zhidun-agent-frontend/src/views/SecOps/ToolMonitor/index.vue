<template>
  <div class="tool-monitor">
    <!-- 顶部：工具调用 KPI -->
    <a-row :gutter="16" class="kpi-row">
      <a-col :xs="12" :md="6">
        <div class="kpi-card">
          <div class="kpi-label">近 24h 调用</div>
          <div class="kpi-value">{{ kpi.total }}</div>
          <div class="kpi-sub">所有 Agent 合计</div>
        </div>
      </a-col>
      <a-col :xs="12" :md="6">
        <div class="kpi-card warn">
          <div class="kpi-label">越权阻断</div>
          <div class="kpi-value">{{ kpi.blocked }}</div>
          <div class="kpi-sub">RBAC 强制阻断</div>
        </div>
      </a-col>
      <a-col :xs="12" :md="6">
        <div class="kpi-card mid">
          <div class="kpi-label">参数越界</div>
          <div class="kpi-value">{{ kpi.outOfBounds }}</div>
          <div class="kpi-sub">超出约束阈值</div>
        </div>
      </a-col>
      <a-col :xs="12" :md="6">
        <div class="kpi-card ok">
          <div class="kpi-label">合规调用</div>
          <div class="kpi-value">{{ kpi.passed }}</div>
          <div class="kpi-sub">通过 RBAC + 参数校验</div>
        </div>
      </a-col>
    </a-row>

    <!-- 调用明细表 -->
    <a-card class="table-card" :bordered="false" size="small">
      <template #title>
        <span class="card-title"><api-outlined /> 工具调用明细流水</span>
      </template>
      <template #extra>
        <a-input-search
          v-model:value="keyword"
          placeholder="按工具 / Agent / 角色搜索"
          allow-clear
          style="width: 240px"
        />
      </template>

      <a-table
        size="small"
        :loading="loading"
        :data-source="filtered"
        :columns="columns"
        :pagination="pagination"
        row-key="id"
        :row-class-name="(r: ToolInvocationRecord) => (r.rbacBreach ? 'row-breach' : '')"
        @change="onTableChange"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.dataIndex === 'toolName'">
            <span class="mono">{{ record.toolName }}</span>
          </template>
          <template v-else-if="column.dataIndex === 'callerRole'">
            <a-tag>{{ record.callerRole }}</a-tag>
            <span class="vs">→</span>
            <a-tag :color="record.requiredLevel === 'L4' ? 'red' : record.requiredLevel === 'L3' ? 'orange' : 'blue'">
              {{ record.requiredLevel }}
            </a-tag>
          </template>
          <template v-else-if="column.dataIndex === 'passed'">
            <a-tag :color="record.passed ? 'green' : 'red'">
              {{ record.passed ? '通过' : record.rbacBreach ? 'RBAC 越权' : '阻断' }}
            </a-tag>
          </template>
          <template v-else-if="column.dataIndex === 'op'">
            <a-button type="link" size="small" @click="openDetail(record)">
              深度解析 <right-outlined />
            </a-button>
            <a-button v-if="record.eventId" type="link" size="small" @click="openEvidence(record.eventId!)">
              证据链
            </a-button>
          </template>
        </template>
      </a-table>
    </a-card>

    <!-- 深度解析抽屉：JSON 解析 / RBAC 矩阵 / 参数雷达 / 调用链图谱 -->
    <a-drawer
      v-model:open="detailOpen"
      title="工具调用深度解析"
      :width="780"
      placement="right"
    >
      <template v-if="active">
        <a-descriptions size="small" :column="2" bordered class="meta">
          <a-descriptions-item label="调用 ID">{{ active.id }}</a-descriptions-item>
          <a-descriptions-item label="时间">{{ active.time }}</a-descriptions-item>
          <a-descriptions-item label="Agent">{{ active.agent }}</a-descriptions-item>
          <a-descriptions-item label="工具">
            <span class="mono">{{ active.toolName }}</span>
          </a-descriptions-item>
        </a-descriptions>

        <a-tabs default-active-key="json" size="small">
          <a-tab-pane key="json" tab="原始 JSON">
            <div class="code-box">
              <vue-json-pretty :data="active.arguments" :deep="3" showLine theme="dark" />
            </div>
          </a-tab-pane>
          <a-tab-pane key="rbac" tab="RBAC 校验矩阵">
            <a-table
              size="small"
              :pagination="false"
              :data-source="rbacMatrix"
              :columns="[
                { title: '维度', dataIndex: 'dim' },
                { title: '当前 (调用方)', dataIndex: 'caller' },
                { title: '要求 (资源)', dataIndex: 'required' },
                { title: '判定', dataIndex: 'verdict' },
              ]"
            >
              <template #bodyCell="{ column, record }">
                <template v-if="column.dataIndex === 'verdict'">
                  <a-tag :color="record.pass ? 'green' : 'red'">{{ record.pass ? '通过' : '阻断' }}</a-tag>
                </template>
              </template>
            </a-table>
          </a-tab-pane>
          <a-tab-pane key="radar" tab="参数约束雷达">
            <v-chart class="chart" :option="radarOption" autoresize />
            <div class="radar-tip">绿色为安全区间，超出虚线即触发阻断。</div>
          </a-tab-pane>
          <a-tab-pane key="chain" tab="调用链图谱">
            <a-timeline>
              <a-timeline-item
                v-for="(t, i) in active.contextChain || []"
                :key="i"
                :color="t.speaker === 'user' ? 'blue' : 'purple'"
              >
                <div class="chain-row">
                  <a-tag>{{ t.speaker === 'user' ? '用户' : 'Agent' }}</a-tag>
                  <span>{{ t.text }}</span>
                </div>
              </a-timeline-item>
              <a-timeline-item v-if="!active.contextChain?.length" color="gray">
                未提供上下文链路。
              </a-timeline-item>
            </a-timeline>
          </a-tab-pane>
        </a-tabs>
      </template>
    </a-drawer>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import VChart from 'vue-echarts';
import { use } from 'echarts/core';
import { CanvasRenderer } from 'echarts/renderers';
import { RadarChart } from 'echarts/charts';
import { TitleComponent, TooltipComponent, LegendComponent } from 'echarts/components';
import VueJsonPretty from 'vue-json-pretty';
import 'vue-json-pretty/lib/styles.css';
import { ApiOutlined, RightOutlined } from '@ant-design/icons-vue';
import { listToolInvocations } from '@/api/services';
import type { ToolInvocationRecord } from '@/types/api';
import { useAuditSessionStore } from '@/stores/auditSession';

use([CanvasRenderer, RadarChart, TitleComponent, TooltipComponent, LegendComponent]);

const sessionStore = useAuditSessionStore();
const loading = ref(false);
const data = ref<ToolInvocationRecord[]>([]);
const keyword = ref('');
const pagination = ref({ current: 1, pageSize: 12, total: 0, showSizeChanger: true });

const detailOpen = ref(false);
const active = ref<ToolInvocationRecord | null>(null);

const columns = [
  { title: '调用 ID', dataIndex: 'id', width: 150 },
  { title: '时间', dataIndex: 'time', width: 160 },
  { title: 'Agent', dataIndex: 'agent', width: 130 },
  { title: '工具', dataIndex: 'toolName', width: 180 },
  { title: '参数摘要', dataIndex: 'argsBrief', ellipsis: true },
  { title: '角色 / 资源等级', dataIndex: 'callerRole', width: 180 },
  { title: '判定', dataIndex: 'passed', width: 100 },
  { title: '操作', dataIndex: 'op', width: 170, fixed: 'right' as const },
];

const filtered = computed(() => {
  const k = keyword.value.trim().toLowerCase();
  if (!k) return data.value;
  return data.value.filter((r) =>
    [r.toolName, r.agent, r.callerRole, r.argsBrief].some((s) => s.toLowerCase().includes(k))
  );
});

const kpi = computed(() => ({
  total: data.value.length,
  blocked: data.value.filter((r) => r.rbacBreach).length,
  outOfBounds: data.value.filter((r) => !r.passed && !r.rbacBreach).length,
  passed: data.value.filter((r) => r.passed).length,
}));

const rbacMatrix = computed(() => {
  if (!active.value) return [];
  const a = active.value;
  const callerOk = !a.rbacBreach;
  return [
    {
      dim: '角色 (Role)',
      caller: a.callerRole,
      required: `允许调用 ${a.toolName}`,
      pass: callerOk,
    },
    {
      dim: '资源敏感度',
      caller: callerOk ? '匹配' : '不足',
      required: a.requiredLevel,
      pass: callerOk,
    },
    {
      dim: '工具白名单',
      caller: callerOk ? '在允许列表' : '不在白名单',
      required: '允许',
      pass: callerOk,
    },
  ];
});

const radarOption = computed(() => ({
  tooltip: {
    backgroundColor: 'rgba(255, 255, 255, 0.96)',
    borderColor: 'rgba(99, 102, 241, 0.32)',
    textStyle: { color: '#0F172A' },
  },
  radar: {
    indicator: [
      { name: '路径合法性', max: 100 },
      { name: '参数大小', max: 100 },
      { name: '调用频次', max: 100 },
      { name: '资源等级匹配', max: 100 },
      { name: '上下文一致性', max: 100 },
    ],
    splitArea: { areaStyle: { color: ['rgba(238, 242, 255, 0.4)', 'rgba(255, 255, 255, 0.4)'] } },
    axisLine: { lineStyle: { color: 'rgba(148, 163, 184, 0.32)' } },
    splitLine: { lineStyle: { color: 'rgba(148, 163, 184, 0.32)' } },
    name: { textStyle: { color: '#475569', fontSize: 11 } },
  },
  series: [
    {
      type: 'radar',
      data: [
        {
          value: active.value?.passed ? [86, 78, 70, 88, 80] : [22, 60, 92, 18, 30],
          name: active.value?.passed ? '安全调用' : '本次调用',
          itemStyle: {
            color: active.value?.passed ? '#10B981' : '#F43F5E',
          },
          lineStyle: {
            color: active.value?.passed ? '#10B981' : '#F43F5E',
            width: 2,
          },
          areaStyle: {
            color: active.value?.passed ? 'rgba(16, 185, 129, 0.32)' : 'rgba(244, 63, 94, 0.32)',
          },
        },
        {
          value: [80, 80, 80, 80, 80],
          name: '安全阈值',
          itemStyle: { color: '#6366F1' },
          lineStyle: { type: 'dashed', color: '#818CF8', width: 1.5 },
          areaStyle: { color: 'rgba(99, 102, 241, 0.08)' },
        },
      ],
    },
  ],
}));

async function load() {
  loading.value = true;
  try {
    const res = await listToolInvocations(pagination.value.current, pagination.value.pageSize);
    data.value = res.items;
    pagination.value.total = res.total;
  } finally {
    loading.value = false;
  }
}

function onTableChange(p: { current?: number; pageSize?: number }) {
  pagination.value.current = p.current ?? 1;
  pagination.value.pageSize = p.pageSize ?? 12;
  load();
}

function openDetail(row: ToolInvocationRecord) {
  active.value = row;
  detailOpen.value = true;
}

function openEvidence(eventId: string) {
  sessionStore.openEvent(eventId);
}

onMounted(load);
</script>

<style scoped>
.tool-monitor {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.kpi-row {
  margin: 0 !important;
}
.kpi-card {
  background: linear-gradient(165deg, rgba(255, 255, 255, 0.96), rgba(238, 242, 255, 0.85));
  border: 1px solid rgba(99, 102, 241, 0.18);
  border-radius: 12px;
  padding: 14px 18px;
  box-shadow: 0 4px 12px -4px rgba(99, 102, 241, 0.18);
  transition: transform 0.22s ease, box-shadow 0.22s ease;
}
.kpi-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 18px -6px rgba(99, 102, 241, 0.32);
}
.kpi-card.warn {
  border-color: rgba(244, 63, 94, 0.28);
  background: linear-gradient(165deg, rgba(255, 245, 247, 0.96), rgba(255, 228, 230, 0.88));
}
.kpi-card.warn:hover { box-shadow: 0 8px 18px -6px rgba(244, 63, 94, 0.32); }
.kpi-card.mid {
  border-color: rgba(245, 158, 11, 0.32);
  background: linear-gradient(165deg, rgba(255, 252, 245, 0.96), rgba(254, 243, 199, 0.88));
}
.kpi-card.mid:hover { box-shadow: 0 8px 18px -6px rgba(245, 158, 11, 0.32); }
.kpi-card.ok {
  border-color: rgba(16, 185, 129, 0.28);
  background: linear-gradient(165deg, rgba(245, 253, 248, 0.96), rgba(209, 250, 229, 0.88));
}
.kpi-card.ok:hover { box-shadow: 0 8px 18px -6px rgba(16, 185, 129, 0.32); }
.kpi-label {
  font-size: 12px;
  color: #475569;
  font-weight: 500;
}
.kpi-value {
  font-size: 26px;
  font-weight: 700;
  color: #0F172A;
  margin: 4px 0;
  font-variant-numeric: tabular-nums;
}
.kpi-sub {
  font-size: 11.5px;
  color: #64748B;
}
.table-card {
  background: rgba(255, 255, 255, 0.92);
}
.card-title {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-weight: 600;
  color: #0F172A;
}
.card-title :deep(.anticon) {
  color: #6366F1;
}
.mono {
  font-family: 'SFMono-Regular', Consolas, Menlo, monospace;
  font-size: 12.5px;
}
.vs {
  margin: 0 4px;
  color: #94A3B8;
}
:deep(.row-breach) {
  background: rgba(255, 228, 230, 0.45) !important;
}
:deep(.row-breach:hover) > td {
  background: rgba(254, 205, 211, 0.55) !important;
}
.code-box {
  background: linear-gradient(165deg, #0F172A 0%, #1E1B4B 100%);
  border-radius: 8px;
  padding: 12px;
  color: #E0E7FF;
  max-height: 320px;
  overflow: auto;
  border: 1px solid rgba(99, 102, 241, 0.28);
}
.meta {
  margin-bottom: 12px;
}
.chart {
  height: 320px;
}
.radar-tip {
  font-size: 12px;
  color: #64748B;
  text-align: center;
  margin-top: 8px;
}
.chain-row {
  display: flex;
  align-items: center;
  gap: 8px;
}
</style>
