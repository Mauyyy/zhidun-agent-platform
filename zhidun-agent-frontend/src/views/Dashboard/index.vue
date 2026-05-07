<template>
  <div class="dashboard-container">
    <a-spin :spinning="loading">
      <a-row :gutter="[24, 16]" align="stretch" class="floating-stats-row">
          <a-col :xs="24" :sm="12" :lg="6" class="stat-col">
            <div class="stat-card stat-card--blue">
              <div class="stat-content">
                <div class="stat-title">风险事件总数</div>
                <div class="stat-value">{{ stats ? stats.totalEvents.toLocaleString() : '—' }}</div>
                <div class="stat-trend">
                  较上周
                  <span v-if="stats?.weekChangePercent != null" class="trend-up">+{{ stats.weekChangePercent }}%</span>
                  <span v-else>—</span>
                </div>
              </div>
              <div class="stat-icon-right">
                <img class="stat-icon-img stat-icon-img--lg" :src="iconTotal" alt="total" />
              </div>
            </div>
          </a-col>
          <a-col :xs="24" :sm="12" :lg="6" class="stat-col">
            <div class="stat-card stat-card--red">
              <div class="stat-content">
                <div class="stat-title">高风险事件数</div>
                <div class="stat-value">{{ stats ? stats.highRiskEvents.toLocaleString() : '—' }}</div>
                <div class="stat-trend">重点监控对象</div>
              </div>
              <div class="stat-icon-right">
                <img class="stat-icon-img stat-icon-img--lg" :src="iconRisk" alt="risk" />
              </div>
            </div>
          </a-col>
          <a-col :xs="24" :sm="12" :lg="6" class="stat-col">
            <div class="stat-card stat-card--cyan">
              <div class="stat-content">
                <div class="stat-title">工具调用审计</div>
                <div class="stat-value">{{ stats ? stats.toolAuditCount.toLocaleString() : '—' }}</div>
                <div class="stat-trend">覆盖多种核心组件</div>
              </div>
              <div class="stat-icon-right">
                <img class="stat-icon-img stat-icon-img--lg" :src="iconTool" alt="tool" />
              </div>
            </div>
          </a-col>
          <a-col :xs="24" :sm="12" :lg="6" class="stat-col">
            <div class="stat-card stat-card--green">
              <div class="stat-content">
                <div class="stat-title">泄露拦截次数</div>
                <div class="stat-value">{{ stats ? stats.leakBlockCount.toLocaleString() : '—' }}</div>
                <div class="stat-trend">系统防护状态良好</div>
              </div>
              <div class="stat-icon-right">
                <img class="stat-icon-img stat-icon-img--lg" :src="iconProvent" alt="prevent" />
              </div>
            </div>
          </a-col>
      </a-row>

      <!-- 主趋势图 + 右侧风险类型分布 -->
      <a-row :gutter="24" class="section-row section-row--split" align="stretch">
        <a-col :xs="24" :lg="17" class="dash-col-fill">
          <a-card :bordered="false" class="chart-card">
            <template #title>
              <div class="chart-title">
                <span class="indicator"></span>
                近期风险态势趋势
              </div>
            </template>
            <div class="dash-chart-wrap">
              <v-chart class="chart" :option="trendOption" autoresize />
            </div>
          </a-card>
        </a-col>
        <a-col :xs="24" :lg="7" class="dash-col-fill">
          <a-card :bordered="false" class="chart-card donut-card donut-card--aside">
            <template #title>
              <div class="chart-title">
                <span class="indicator indicator-orange"></span>
                风险类型分布
              </div>
            </template>
            <div class="dash-donut-wrap">
              <v-chart class="donut-chart" :option="donutOption" autoresize />
            </div>
          </a-card>
        </a-col>
      </a-row>

      <!-- 系统运行状态 + 近期事件 -->
      <a-row :gutter="24" class="section-row section-row--split" align="stretch">
        <a-col :xs="24" :lg="9" class="dash-col-fill">
          <a-card :bordered="false" class="status-card">
            <template #title>
              <div class="chart-title">
                <span class="indicator indicator-green"></span>
                系统运行状态
              </div>
            </template>
            <ul class="status-list">
              <li class="status-item">
                <a-badge status="success" text="策略网关同步" />
                <span class="status-meta">已对齐</span>
              </li>
              <li class="status-item">
                <a-badge status="processing" text="模型接入节点" />
                <span class="status-meta">在线</span>
              </li>
              <li class="status-item">
                <a-badge status="default" text="低风险策略域" />
                <span class="status-meta">稳定</span>
              </li>
              <li class="status-item">
                <a-badge status="warning" text="中危观察区" />
                <span class="status-meta">持续扫描</span>
              </li>
              <li class="status-item">
                <a-badge status="error" text="高危拦截区" />
                <span class="status-meta">{{ matrix?.highRiskZones ?? '—' }} 个热点</span>
              </li>
              <li class="status-item">
                <a-badge status="success" text="威胁情报源" />
                <span class="status-meta">已订阅</span>
              </li>
              <li class="status-item">
                <a-badge status="processing" text="脱敏与令牌服务" />
                <span class="status-meta">低延迟</span>
              </li>
              <li class="status-item">
                <a-badge status="default" text="审计存证集群" />
                <span class="status-meta">三副本</span>
              </li>
              <li class="status-item muted">
                <span class="label">监控节点</span>
                <span class="status-meta">{{ matrix?.monitoredNodes?.toLocaleString() ?? '—' }}</span>
              </li>
            </ul>
          </a-card>
        </a-col>
        <a-col :xs="24" :lg="15" class="dash-col-fill">
          <a-card :bordered="false" class="chart-card table-card">
            <template #title>
              <div class="chart-title">
                <span class="indicator"></span>
                近期风险事件
              </div>
            </template>
            <a-table
              :dataSource="recentRows"
              :columns="recentColumns"
              row-key="id"
              size="small"
              :pagination="false"
              :loading="loading"
            >
              <template #bodyCell="{ column, record }">
                <template v-if="column.key === 'level'">
                  <span class="risk-pill" :class="record.level === '高危' ? 'risk-pill--high' : 'risk-pill--mid'">
                    {{ record.level }}
                  </span>
                </template>
                <template v-if="column.key === 'result'">
                  <span class="risk-pill" :class="String(record.result).includes('拦截') ? 'risk-pill--high' : (String(record.result).includes('放行') || String(record.result).includes('通过') ? 'risk-pill--ok' : 'risk-pill--info')">
                    {{ record.result }}
                  </span>
                </template>
                <template v-if="column.key === 'action'">
                  <a-button type="link" size="small" @click="sessionStore.openEvent(record.id)">
                    证据链
                  </a-button>
                </template>
              </template>
            </a-table>
          </a-card>
        </a-col>
      </a-row>
    </a-spin>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue';
import iconTotal from '@/assets/icon/total.png';
import iconRisk from '@/assets/icon/risk.png';
import iconTool from '@/assets/icon/tool.png';
import iconProvent from '@/assets/icon/provent.png';
import { use } from 'echarts/core';
import { CanvasRenderer } from 'echarts/renderers';
import { LineChart, PieChart } from 'echarts/charts';
import { TitleComponent, TooltipComponent, GridComponent, LegendComponent } from 'echarts/components';
import VChart from 'vue-echarts';
import { storeToRefs } from 'pinia';
import { useSecurityRealtimeStore } from '@/stores/securityRealtime';
import { useAuditSessionStore } from '@/stores/auditSession';
import type { DashboardOverview } from '@/types/api';

use([
  CanvasRenderer,
  LineChart,
  PieChart,
  TitleComponent,
  TooltipComponent,
  GridComponent,
  LegendComponent,
]);

const realtimeStore = useSecurityRealtimeStore();
const sessionStore = useAuditSessionStore();
const { coreLoading, overview, matrix, events } = storeToRefs(realtimeStore);
const loading = computed(() => coreLoading.value);
const stats = computed(() => overview.value?.stats ?? null);
const recentRows = computed(() => events.value.slice(0, 14));
const trendOption = computed(() => buildTrendOption(overview.value));
const donutOption = computed(() => buildDonutOption(overview.value));

const recentColumns = [
  { title: '时间', dataIndex: 'time', key: 'time', width: 170 },
  { title: '风险类型', dataIndex: 'type', key: 'type' },
  { title: '等级', dataIndex: 'level', key: 'level', width: 88 },
  { title: '处置结果', dataIndex: 'result', key: 'result', width: 110 },
  { title: '操作', key: 'action', width: 72 },
];

function buildDonutOption(data: DashboardOverview | null) {
  const distribution = data?.riskTypeDistribution ?? data?.risk_type_distribution ?? [];
  const colors: Record<string, string> = {
    prompt_injection: '#0284C7',
    rule_override: '#6366F1',
    privilege_escalation: '#E11D48',
    sensitive_data_exfiltration: '#F59E0B',
    normal: '#10B981',
    unknown: '#94A3B8',
  };
  const seriesData = distribution
    .filter((item) => item.count > 0)
    .map((item) => ({
      value: item.count,
      name: item.label,
      itemStyle: { color: colors[item.type] ?? colors.unknown },
    }));
  const pieData = seriesData.length
    ? seriesData
    : [{ value: 1, name: '暂无事件', itemStyle: { color: '#CBD5E1' } }];

  return {
    tooltip: {
      trigger: 'item',
      backgroundColor: 'rgba(255, 255, 255, 0.98)',
      borderColor: 'rgba(14, 165, 233, 0.32)',
      borderWidth: 1,
      textStyle: { color: '#0F172A' },
      extraCssText: 'box-shadow: 0 4px 16px rgba(45, 90, 150, 0.12); border-radius: 8px;',
      formatter: '{b}<br/>{c} ({d}%)',
    },
    legend: {
      bottom: 0,
      left: 'center',
      itemWidth: 10,
      itemHeight: 10,
      itemGap: 14,
      icon: 'circle',
      textStyle: { color: '#475569', fontSize: 12 },
    },
    series: [
      {
        name: '风险类型',
        type: 'pie',
        radius: ['55%', '70%'],
        center: ['50%', '44%'],
        avoidLabelOverlap: true,
        itemStyle: { borderRadius: 6, borderColor: '#FFFFFF', borderWidth: 3 },
        label: {
          show: true,
          position: 'outside',
          formatter: '{b}\n{d}%',
          fontSize: 11,
          fontWeight: 500,
          color: '#475569',
          lineHeight: 16,
        },
        labelLine: {
          show: true,
          length: 10,
          length2: 14,
          smooth: true,
          lineStyle: { color: '#CBD5E1', width: 1 },
        },
        emphasis: {
          scale: true,
          scaleSize: 6,
          label: { fontWeight: 700, color: '#0F172A' },
          itemStyle: { shadowBlur: 18, shadowColor: 'rgba(59, 130, 246, 0.35)' },
        },
        data: pieData,
      },
    ],
  };
}

function buildTrendOption(data: DashboardOverview | null) {
  const dates = data?.trend.dates ?? [];
  const inj = data?.trend.injection ?? [];
  const tool = data?.trend.toolAbuse ?? [];
  const leak = data?.trend.dataLeak ?? [];
  return {
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(255, 255, 255, 0.98)',
      borderColor: 'rgba(14, 165, 233, 0.32)',
      borderWidth: 1,
      textStyle: { color: '#0F172A' },
      extraCssText: 'box-shadow: 0 4px 16px rgba(45, 90, 150, 0.12); border-radius: 8px;',
    },
    legend: {
      data: ['提示注入', '工具越权', '敏感数据泄露'],
      top: 4,
      right: 8,
      icon: 'circle',
      itemWidth: 9,
      itemHeight: 9,
      textStyle: { color: '#475569', fontSize: 12 },
    },
    grid: { left: '2%', right: '3%', bottom: '4%', top: '14%', containLabel: true },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: dates.length ? dates : ['—'],
      axisLine: { lineStyle: { color: 'rgba(203, 213, 225, 0.8)' } },
      axisTick: { show: false },
      axisLabel: { color: '#94A3B8', fontSize: 11 },
    },
    yAxis: {
      type: 'value',
      splitLine: { lineStyle: { type: 'dashed', color: 'rgba(226, 232, 240, 0.9)' } },
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { color: '#94A3B8', fontSize: 11 },
    },
    series: [
      {
        name: '提示注入',
        type: 'line',
        smooth: 0.45,
        lineStyle: { width: 2.5, color: '#0284C7' },
        symbol: 'circle',
        symbolSize: 6,
        data: inj.length ? inj : [0],
        itemStyle: { color: '#0284C7', borderColor: '#fff', borderWidth: 2 },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(14, 165, 233, 0.24)' },
              { offset: 1, color: 'rgba(14, 165, 233, 0)' },
            ],
          },
        },
      },
      {
        name: '工具越权',
        type: 'line',
        smooth: 0.45,
        lineStyle: { width: 2.5, color: '#E11D48' },
        symbol: 'circle',
        symbolSize: 6,
        data: tool.length ? tool : [0],
        itemStyle: { color: '#E11D48', borderColor: '#fff', borderWidth: 2 },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(245, 34, 45, 0.26)' },
              { offset: 1, color: 'rgba(245, 34, 45, 0)' },
            ],
          },
        },
      },
      {
        name: '敏感数据泄露',
        type: 'line',
        smooth: 0.45,
        lineStyle: { width: 2.5, color: '#10B981' },
        symbol: 'circle',
        symbolSize: 6,
        data: leak.length ? leak : [0],
        itemStyle: { color: '#10B981', borderColor: '#fff', borderWidth: 2 },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(16, 185, 129, 0.22)' },
              { offset: 1, color: 'rgba(16, 185, 129, 0)' },
            ],
          },
        },
      },
    ],
  };
}

onMounted(async () => {
  if (!realtimeStore.started) {
    await realtimeStore.start();
  } else if (!overview.value) {
    await realtimeStore.forceRefreshAll();
  }
});
</script>

<style scoped>
.dashboard-container {
  padding: 0;
  --dash-primary: #0369a1;
  --dash-primary-soft: rgba(14, 165, 233, 0.14);
  --dash-accent: #14b8a6;
  --dash-ink: #0f172a;
  --dash-muted: #64748b;
  --dash-border: rgba(203, 213, 225, 0.72);
  --dash-card: rgba(255, 255, 255, 0.96);
  --dash-shadow: 0 14px 34px rgba(15, 23, 42, 0.08);
}

/* 悬浮在 Hero 底边与波浪叠层；App 内 .shell-content.is-hero-page z-index:2 高于 .header-glass(1) */
.floating-stats-row {
  position: relative;
  z-index: 1;
  margin-top: -76px !important;
  margin-bottom: 22px !important;
  width: 100%;
}
@media (max-width: 1200px) {
  .floating-stats-row {
    margin-top: -48px !important;
  }
}
@media (max-width: 576px) {
  .floating-stats-row {
    margin-top: -40px !important;
  }
  .stat-card {
    min-height: 112px;
    padding: 16px;
  }
  .stat-value {
    font-size: 28px;
  }
  .stat-icon-img--lg {
    width: 82px;
    height: 82px;
  }
}

.section-row {
  margin-top: 20px;
}

.stat-col {
  display: flex;
  flex-direction: column;
  margin-bottom: 12px;
}
@media (min-width: 576px) {
  .stat-col {
    margin-bottom: 0;
  }
}
.stat-col .stat-card {
  flex: 1;
  /* 需要至少容纳 138px icon + 上下 padding，避免 overflow hidden 裁切 */
  min-height: 136px;
}

/* 轻量科技风 KPI 卡片：白底 + 蓝色弥散阴影 + Icon 在左 */
.stat-card {
  position: relative;
  z-index: 0;
  min-height: 118px;
  border-radius: 14px;
  /* 仅收紧上下间距，左右恢复 */
  padding: 18px 18px 16px;
  overflow: hidden;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.98) 0%, rgba(248, 251, 254, 0.96) 100%);
  border: 1px solid var(--dash-border);
  /* 弥散深色柔和阴影：3D 悬浮，高于波浪层次 */
  box-shadow: var(--dash-shadow);
  transition: transform 0.28s ease, box-shadow 0.28s ease, border-color 0.28s ease;
  cursor: default;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

/* 每张卡片不同主色：用“左侧强调条 + 极浅底色晕染”区分 */
.stat-card::after {
  content: '';
  position: absolute;
  inset: 0;
  pointer-events: none;
  z-index: 0;
}

.stat-card--blue::after {
  background: radial-gradient(120% 95% at 92% 10%, rgba(14, 165, 233, 0.18) 0%, transparent 62%);
}

.stat-card--red::after {
  background: radial-gradient(120% 95% at 92% 10%, rgba(244, 63, 94, 0.15) 0%, transparent 62%);
}
.stat-card--cyan::after {
  background: radial-gradient(120% 95% at 92% 10%, rgba(20, 184, 166, 0.16) 0%, transparent 62%);
}

.stat-card--green::after {
  background: radial-gradient(120% 95% at 92% 10%, rgba(16, 185, 129, 0.16) 0%, transparent 62%);
}
.stat-card:hover {
  transform: translateY(-2px);
  border-color: rgba(14, 165, 233, 0.42);
  box-shadow: 0 18px 44px rgba(15, 23, 42, 0.11);
}

.stat-content {
  position: relative;
  z-index: 2;
  flex: 1;
  min-width: 0;
}
.stat-title {
  font-size: 13px;
  color: var(--dash-muted);
  font-weight: 700;
  margin-bottom: 10px;
  letter-spacing: 0;
}
.stat-value {
  font-size: 32px;
  font-weight: 800;
  color: var(--dash-ink);
  font-variant-numeric: tabular-nums;
  font-family: ui-sans-serif, system-ui, -apple-system, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
  letter-spacing: -0.02em;
  line-height: 1.15;
}
.stat-trend {
  font-size: 12px;
  color: var(--dash-muted);
  margin-top: 8px;
}
.trend-up {
  color: #F5222D;
  font-weight: 600;
}

.stat-icon-img {
  width: 30px;
  height: 30px;
  object-fit: contain;
  user-select: none;
  -webkit-user-drag: none;
}

.stat-icon-right {
  flex: 0 0 auto;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding-left: 6px;
}

.stat-icon-img--lg {
  /* 按“当前大小的 3 倍”放大 */
  width: 104px;
  height: 104px;
  opacity: 0.86;
  filter: saturate(0.95);
}

/* 图表 / 列表 卡片样式：白底 + 蓝色弥散阴影 */
.chart-card {
  position: relative;
  border-radius: 14px;
  overflow: hidden;
  background: var(--dash-card) !important;
  box-shadow: 0 10px 28px rgba(15, 23, 42, 0.06);
  border: 1px solid var(--dash-border) !important;
}
.chart-card :deep(.ant-card-head) {
  border-bottom-color: rgba(226, 232, 240, 0.78);
  padding-top: 4px;
  min-height: 52px;
}
.chart-card :deep(.ant-card-body) {
  padding: 20px 24px 24px;
}
.chart-title {
  display: flex;
  align-items: center;
  font-size: 15px;
  font-weight: 700;
  color: var(--dash-ink);
  letter-spacing: 0;
}
.indicator {
  display: inline-block;
  width: 8px;
  height: 8px;
  background: var(--dash-primary);
  border-radius: 4px;
  margin-right: 10px;
  box-shadow: 0 0 0 4px rgba(14, 165, 233, 0.13);
}
.chart {
  width: 100%;
}

/* 并排模块等高：列 flex + 卡片撑满 */
.dash-col-fill {
  display: flex;
  flex-direction: column;
  min-height: 0;
  margin-bottom: 16px;
}
@media (min-width: 992px) {
  .dash-col-fill {
    margin-bottom: 0;
    align-self: stretch;
  }
}
.dash-col-fill > .chart-card,
.dash-col-fill > .status-card {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}
.dash-col-fill :deep(.ant-card-body) {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}
.dash-chart-wrap {
  flex: 1;
  min-height: 340px;
  position: relative;
}
.dash-chart-wrap .chart {
  height: 100%;
  min-height: 340px;
}
.dash-donut-wrap {
  flex: 1;
  min-height: 260px;
  position: relative;
}
.dash-donut-wrap .donut-chart {
  height: 100%;
  min-height: 260px;
}
.table-card :deep(.ant-table-wrapper) {
  flex: 1;
  min-height: 0;
}
.table-card :deep(.ant-spin-nested-loading),
.table-card :deep(.ant-spin-container) {
  height: 100%;
  display: flex;
  flex-direction: column;
}
.table-card :deep(.ant-table) {
  flex: 1;
}

.status-card {
  border-radius: 14px;
  height: 100%;
  background: var(--dash-card) !important;
  border: 1px solid var(--dash-border) !important;
  box-shadow: 0 10px 28px rgba(15, 23, 42, 0.06) !important;
  position: relative;
  overflow: hidden;
}
.status-card :deep(.ant-card-body) {
  padding: 16px 24px 20px;
}
.status-card :deep(.ant-card-head) {
  border-bottom-color: rgba(226, 232, 240, 0.9);
}
.status-list {
  list-style: none;
  padding: 0;
  margin: 0;
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  min-height: 0;
}
.status-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 10px 0;
  border-bottom: 1px solid rgba(226, 232, 240, 0.74);
}
.status-item:last-child {
  border-bottom: none;
}
.status-item.muted {
  padding-top: 16px;
  color: #64748B;
  font-size: 13px;
}
.status-item .label {
  font-weight: 500;
}
.status-meta {
  font-size: 13px;
  color: var(--dash-muted);
  white-space: nowrap;
}

.indicator-green {
  background: #10b981;
  box-shadow: 0 0 0 4px rgba(16, 185, 129, 0.13);
}
.indicator-orange {
  background: #f59e0b;
  box-shadow: 0 0 0 4px rgba(245, 158, 11, 0.13);
}
.indicator-purple {
  background: linear-gradient(180deg, #818CF8 0%, #6366F1 100%);
  box-shadow: 0 1px 4px rgba(99, 102, 241, 0.4);
}
.topology-wrap {
  height: 360px;
}

.donut-card {
  min-height: 0;
}
/* 环形图引导线曾伸出卡片被裁切；现改为扇区内标签，此处放宽避免 hover 装饰被裁 */
.donut-card.chart-card,
.donut-card.chart-card :deep(.ant-card-body) {
  overflow: visible;
}
/* 与趋势图并排时列宽较窄，略压缩环形图高度避免拥挤 */
@media (min-width: 992px) {
  .donut-card--aside .dash-donut-wrap,
  .donut-card--aside .dash-donut-wrap .donut-chart {
    min-height: 240px;
  }
}
.donut-chart {
  width: 100%;
}
.table-card :deep(.ant-card-body) {
  padding-top: 8px;
}

/* 表格行间隔仅显示极浅实线 */
.table-card :deep(.ant-table-thead > tr > th) {
  background: #f8fbfe;
  color: #334155;
  font-weight: 700;
  border-bottom: 1px solid rgba(226, 232, 240, 0.9);
}
.table-card :deep(.ant-table-tbody > tr > td) {
  border-bottom: 1px solid rgba(226, 232, 240, 0.72);
}
.table-card :deep(.ant-table-tbody > tr:last-child > td) {
  border-bottom: none;
}
.table-card :deep(.ant-table-tbody > tr:hover > td) {
  background: #eff8ff !important;
}

/* 胶囊状风险标签 —— 无边框 */
.risk-pill {
  display: inline-flex;
  align-items: center;
  padding: 2px 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 700;
  line-height: 20px;
  border: none;
  letter-spacing: 0.01em;
}
.risk-pill--high {
  background: #FFF1F0;
  color: #F5222D;
}
.risk-pill--mid {
  background: #FFF7E6;
  color: #FA8C16;
}
.risk-pill--ok {
  background: #F6FFED;
  color: #52C41A;
}
.risk-pill--info {
  background: #E6F4FF;
  color: #1677FF;
}
</style>
