<template>
  <div class="audit-container">
    <a-spin :spinning="loading">
      <template v-if="detail">
        <a-page-header
          class="custom-audit-header"
          title="安全事件审计详情与证据链追踪"
          :sub-title="`事件编号：${detail.event_id}`"
          @back="goBack"
        >
          <template #tags>
            <a-tag
              :color="detail.risk_level === 'high' ? 'red' : 'orange'"
              :class="['risk-tag', detail.risk_level === 'high' ? 'risk-tag-pulse' : '']"
            >
              {{ detail.action === 'block' ? '高危阻断' : detail.risk_level }}
            </a-tag>
            <a-tag color="blue" class="risk-tag">{{ detail.scenario }}</a-tag>
            <a-tag color="gold" class="risk-tag">三阶段防护触发</a-tag>
          </template>

          <template #extra>
            <a-button @click="handleExport" :loading="isExporting" type="primary" class="export-btn">
              <download-outlined /> {{ isExporting ? '生成加密报告中...' : '导出合规审计报告 (PDF)' }}
            </a-button>
          </template>

          <div class="header-desc">
            <safety-outlined class="desc-icon" />
            <span><strong>审计结论：</strong>{{ detail.audit_conclusion }}</span>
          </div>
        </a-page-header>

        <a-card :bordered="false" class="verdict-focus-card">
          <a-row :gutter="[16, 16]" align="middle">
            <a-col :xs="24" :md="8">
              <div class="verdict-chip" :class="detail.rbac_result.passed ? 'is-allow' : 'is-block'">
                {{ detail.rbac_result.passed ? 'ALLOW · 放行' : 'BLOCK · 拦截' }}
              </div>
              <div class="verdict-sub">最终执行裁决</div>
            </a-col>
            <a-col :xs="24" :md="16">
              <a-row :gutter="12" class="kpi-row">
                <a-col :span="8">
                  <div class="kpi-box">
                    <div class="kpi-label">综合风险 R</div>
                    <div class="kpi-value">{{ detail.risk_score_total ?? '—' }}</div>
                  </div>
                </a-col>
                <a-col :span="8">
                  <div class="kpi-box">
                    <div class="kpi-label">规则命中</div>
                    <div class="kpi-value">{{ detail.rule_hits?.length ?? 0 }}</div>
                  </div>
                </a-col>
                <a-col :span="8">
                  <div class="kpi-box">
                    <div class="kpi-label">RBAC 校验</div>
                    <div class="kpi-value">{{ detail.rbac_result.passed ? 'PASS' : 'DENY' }}</div>
                  </div>
                </a-col>
              </a-row>
            </a-col>
          </a-row>
        </a-card>

        <a-card title="全链路审计追踪 (执行前置拦截)" :bordered="false" class="main-timeline-card">
          <a-timeline mode="left">
            <a-timeline-item color="green">
              <template #dot><message-outlined style="font-size: 16px" /></template>
              <div class="timeline-title">1. 原始交互意图识别</div>
              <div class="code-box user-input">
                {{ detail.user_input }}
              </div>
            </a-timeline-item>

            <a-timeline-item v-if="detail.rule_hits?.length" color="purple">
              <template #dot><safety-outlined style="font-size: 16px" /></template>
              <div class="timeline-title">规则模板命中（可解释性）</div>
              <a-list size="small" bordered :data-source="detail.rule_hits" class="hit-list">
                <template #renderItem="{ item }">
                  <a-list-item>
                    <a-list-item-meta :title="item.template" :description="`规则 ID: ${item.ruleId} · 权重 ${item.weight}`" />
                  </a-list-item>
                </template>
              </a-list>
            </a-timeline-item>

            <a-timeline-item color="orange">
              <template #dot><dashboard-outlined style="font-size: 16px" /></template>
              <div class="timeline-title">2. 综合风险评估诊断 (R={{ detail.risk_score_total ?? '—' }})</div>
              <div class="score-grid-container">
                <a-row :gutter="24">
                  <a-col :span="12" v-for="(val, key) in scoreMap" :key="key">
                    <div class="score-item">
                      <div class="score-label">{{ key }}</div>
                      <a-progress
                        :percent="Number(val)"
                        size="small"
                        :stroke-color="{
                          '0%': Number(val) > 70 ? '#F43F5E' : Number(val) > 40 ? '#F59E0B' : '#10B981',
                          '100%': Number(val) > 70 ? '#F59E0B' : Number(val) > 40 ? '#FBBF24' : '#34D399',
                        }"
                        status="active"
                      />
                    </div>
                  </a-col>
                </a-row>
              </div>
            </a-timeline-item>

            <a-timeline-item color="blue">
              <template #dot><api-outlined style="font-size: 16px" /></template>
              <div class="timeline-title">3. 模型底层 Function Calling 意图截获</div>
              <p class="step-desc">系统在工具实际执行前，通过代理网关层解析出模型调用的高敏插件及参数。</p>
              <div class="code-box json-box code-shell">
                <div class="code-shell-head">
                  <span class="dot red"></span>
                  <span class="dot yellow"></span>
                  <span class="dot green"></span>
                  <span class="code-shell-title">Function Calling Payload</span>
                </div>
                <vue-json-pretty :data="detail.function_call" :deep="3" showLine theme="dark" />
              </div>
            </a-timeline-item>

            <a-timeline-item color="red">
              <template #dot><stop-outlined style="font-size: 16px" /></template>
              <div class="timeline-title">4. RBAC 策略校验与执行决断</div>
              <a-alert
                :message="detail.rbac_result.passed ? '放行 Action: Allow' : '拦截 Action: Block (强制阻断)'"
                :description="detail.rbac_result.reject_reason || '校验通过'"
                :type="detail.rbac_result.passed ? 'success' : 'error'"
                show-icon
                class="block-alert-item"
              />
              <div class="rbac-details">
                <a-descriptions bordered size="small" :column="2" class="rbac-table">
                  <a-descriptions-item label="匹配用户角色">{{ detail.rbac_result.matched_role }}</a-descriptions-item>
                  <a-descriptions-item label="访问资源等级">按策略引擎标注</a-descriptions-item>
                </a-descriptions>
              </div>
            </a-timeline-item>

            <a-timeline-item v-if="detail.output_diff" color="cyan">
              <template #dot><diff-outlined style="font-size: 16px" /></template>
              <div class="timeline-title">5. 输出安全防护层 (动态脱敏结果对比)</div>
              <div class="diff-view-wrapper">
                <a-row :gutter="16">
                  <a-col :xs="24" :md="11">
                    <div class="diff-panel original-panel">
                      <div class="panel-tag">原始模型输出</div>
                      <div class="text-inner">{{ detail.output_diff.original }}</div>
                    </div>
                  </a-col>
                  <a-col :xs="0" :md="2" class="diff-arrow">
                    <swap-right-outlined />
                  </a-col>
                  <a-col :xs="24" :md="11">
                    <div class="diff-panel masked-panel">
                      <div class="panel-tag">安全脱敏输出</div>
                      <div class="text-inner">{{ detail.output_diff.masked }}</div>
                    </div>
                  </a-col>
                </a-row>
              </div>
            </a-timeline-item>
          </a-timeline>
        </a-card>
      </template>
      <a-empty v-else-if="!loading" description="未找到事件或加载失败" />
    </a-spin>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, computed, onBeforeUnmount } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { storeToRefs } from 'pinia';
import {
  MessageOutlined,
  DashboardOutlined,
  ApiOutlined,
  StopOutlined,
  DownloadOutlined,
  SafetyOutlined,
  DiffOutlined,
  SwapRightOutlined,
} from '@ant-design/icons-vue';
import { message } from 'ant-design-vue';
import VueJsonPretty from 'vue-json-pretty';
import 'vue-json-pretty/lib/styles.css';
import { requestAuditReport } from '@/api/services';
import type { AuditEventDetail } from '@/types/api';
import { useSecurityRealtimeStore } from '@/stores/securityRealtime';

const router = useRouter();
const route = useRoute();
const loading = ref(true);
const detail = ref<AuditEventDetail | null>(null);
const isExporting = ref(false);
const realtimeStore = useSecurityRealtimeStore();
const { detailMap } = storeToRefs(realtimeStore);

const scoreMap = computed(() => {
  const d = detail.value;
  if (!d) return {};
  return {
    '规则命中分 (S_rule)': d.risk_scores.rule_score,
    '语义判别分 (S_cls)': d.risk_scores.semantic_score,
    '上下文异常度 (S_ctx)': d.risk_scores.context_score,
    '资源敏感度 (S_res)': d.risk_scores.resource_score,
  };
});

async function load(id: string) {
  loading.value = true;
  try {
    const dataFromStore = await realtimeStore.loadDetail(id);
    detail.value = dataFromStore ?? detailMap.value[id] ?? null;
    realtimeStore.setActiveDetail(id);
  } catch {
    detail.value = null;
    message.error('加载事件详情失败');
  } finally {
    loading.value = false;
  }
}

watch(
  () => route.query.id,
  (id) => {
    const eventId = typeof id === 'string' && id ? id : 'EVT-2026-0883';
    void load(eventId);
  },
  { immediate: true }
);

watch(
  () => route.query.id,
  (id) => {
    const eventId = typeof id === 'string' && id ? id : 'EVT-2026-0883';
    const live = detailMap.value[eventId];
    if (live) detail.value = live;
  }
);

const goBack = () => {
  router.back();
};

const handleExport = async () => {
  if (!detail.value) return;
  isExporting.value = true;
  try {
    const job = await requestAuditReport(detail.value.event_id);
    if (job.downloadUrl) {
      const url = job.downloadUrl.startsWith('http') ? job.downloadUrl : `${window.location.origin}${job.downloadUrl}`;
      window.open(url, '_blank');
    }
    message.success('报告已就绪');
  } catch {
    message.error('导出失败');
  } finally {
    isExporting.value = false;
  }
};

onBeforeUnmount(() => {
  realtimeStore.setActiveDetail(null);
});
</script>

<style scoped>
.audit-container {
  --zd-blue: #6366F1;
  --zd-blue-deep: #0F172A;
  --zd-border: rgba(148, 163, 184, 0.22);
  --zd-shadow: 0 0 0 1px rgba(255, 255, 255, 0.85) inset, 0 4px 12px -4px rgba(15, 23, 42, 0.08),
    0 16px 32px -12px rgba(99, 102, 241, 0.18);
  --zd-mono: ui-monospace, 'Roboto Mono', 'SFMono-Regular', Menlo, Consolas, monospace;
  padding: 4px 0 8px;
}
.custom-audit-header {
  position: relative;
  border-radius: 18px;
  border: 1px solid var(--zd-border) !important;
  margin-bottom: 24px;
  overflow: hidden;
  background: linear-gradient(165deg, rgba(255, 255, 255, 0.88) 0%, rgba(248, 250, 255, 0.74) 100%) !important;
  box-shadow: var(--zd-shadow) !important;
}
.header-desc {
  margin-top: 16px;
  padding: 12px 16px;
  background: linear-gradient(90deg, rgba(238, 242, 255, 0.85) 0%, rgba(207, 250, 254, 0.6) 100%);
  border-radius: 12px;
  border-left: 4px solid #6366F1;
  color: #334155;
  display: flex;
  align-items: center;
}
.desc-icon {
  margin-right: 8px;
  font-size: 18px;
}
.risk-tag {
  border-radius: 6px;
  font-weight: 500;
}
.risk-tag-pulse {
  animation: alertPulse 2s ease-in-out infinite;
}
.export-btn {
  background: linear-gradient(135deg, #6366F1 0%, #8B5CF6 100%) !important;
  border-color: transparent !important;
  border-radius: 10px;
  font-weight: 600;
  box-shadow: 0 8px 16px -4px rgba(99, 102, 241, 0.4);
}
.verdict-focus-card {
  border-radius: 18px;
  overflow: hidden;
  border: 1px solid var(--zd-border) !important;
  background: linear-gradient(160deg, rgba(255, 255, 255, 0.9) 0%, rgba(248, 250, 255, 0.78) 100%) !important;
  box-shadow: var(--zd-shadow) !important;
  margin-bottom: 18px;
}
.verdict-chip {
  display: inline-flex;
  align-items: center;
  padding: 8px 14px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
}
.verdict-chip.is-block {
  color: #fff;
  background: linear-gradient(135deg, #F43F5E 0%, #E11D48 100%);
  box-shadow: 0 8px 16px -4px rgba(244, 63, 94, 0.45);
}
.verdict-chip.is-allow {
  color: #fff;
  background: linear-gradient(135deg, #10B981 0%, #047857 100%);
  box-shadow: 0 8px 16px -4px rgba(16, 185, 129, 0.4);
}
.verdict-sub {
  margin-top: 8px;
  font-size: 12px;
  color: #6b7280;
}
.kpi-row {
  width: 100%;
}
.kpi-box {
  border-radius: 12px;
  border: 1px solid rgba(200, 204, 232, 0.55);
  background: rgba(255, 255, 255, 0.65);
  padding: 10px 12px;
}
.kpi-label {
  font-size: 11px;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.06em;
}
.kpi-value {
  margin-top: 6px;
  font-size: 20px;
  font-weight: 800;
  color: var(--zd-blue-deep);
  font-family: var(--zd-mono);
  font-variant-numeric: tabular-nums;
}

.main-timeline-card {
  border-radius: 18px;
  overflow: hidden;
  border: 1px solid var(--zd-border) !important;
  background: linear-gradient(165deg, rgba(255, 255, 255, 0.88) 0%, rgba(248, 250, 255, 0.74) 100%) !important;
  box-shadow: var(--zd-shadow) !important;
}
.main-timeline-card :deep(.ant-timeline-item-tail) {
  border-inline-start: 2px solid rgba(200, 204, 232, 0.85);
}
.timeline-title {
  font-size: 16px;
  font-weight: 700;
  margin-bottom: 12px;
  color: #0F172A;
  letter-spacing: -0.01em;
}
.step-desc {
  color: #6b7280;
  font-size: 13px;
  margin-bottom: 12px;
}

.code-box {
  padding: 16px;
  border-radius: 10px;
  font-family: var(--zd-mono);
  font-size: 13px;
  margin-top: 10px;
}
.user-input {
  background: linear-gradient(180deg, #ECFDF5 0%, #D1FAE5 100%);
  border: 1px solid rgba(16, 185, 129, 0.32);
  color: #047857;
}
.json-box {
  background: linear-gradient(165deg, #0F172A 0%, #1E1B4B 100%);
  border: 1px solid rgba(99, 102, 241, 0.28);
  color: #E0E7FF;
  padding-top: 10px;
}
.code-shell-head {
  display: flex;
  align-items: center;
  gap: 7px;
  margin-bottom: 10px;
  padding-bottom: 8px;
  border-bottom: 1px solid rgba(148, 163, 184, 0.25);
}
.code-shell-head .dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}
.code-shell-head .dot.red {
  background: #ef4444;
}
.code-shell-head .dot.yellow {
  background: #f59e0b;
}
.code-shell-head .dot.green {
  background: #22c55e;
}
.code-shell-title {
  margin-left: 6px;
  font-size: 11px;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}
.hit-list :deep(.ant-list-item) {
  background: rgba(248, 250, 255, 0.85);
}

.score-grid-container {
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.75) 0%, rgba(244, 247, 255, 0.92) 100%);
  padding: 18px;
  border-radius: 14px;
  margin-top: 12px;
  border: 1px solid rgba(200, 204, 232, 0.55);
}
.score-item {
  margin-bottom: 12px;
}
.score-label {
  font-size: 12px;
  color: #6b7280;
  margin-bottom: 5px;
}
.score-item :deep(.ant-progress-inner) {
  border-radius: 999px;
}

.block-alert-item {
  margin-top: 16px;
  border-radius: 10px;
}
.rbac-details {
  margin-top: 12px;
}
.rbac-table :deep(.ant-descriptions-view) {
  border-radius: 8px;
  overflow: hidden;
}
.rbac-table :deep(.ant-descriptions-item-label) {
  width: 160px;
  background: rgba(248, 250, 255, 0.95) !important;
  font-size: 12px;
}
.rbac-table :deep(.ant-descriptions-item-content) {
  font-size: 13px;
}

.diff-view-wrapper {
  margin-top: 16px;
}
.diff-panel {
  padding: 16px;
  border-radius: 10px;
  min-height: 120px;
  position: relative;
}
.panel-tag {
  font-size: 10px;
  text-transform: uppercase;
  margin-bottom: 12px;
  color: #64748b;
  font-weight: 700;
  letter-spacing: 0.06em;
}
.original-panel {
  background: linear-gradient(180deg, #FFF1F2 0%, #FFE4E6 100%);
  border: 1px solid rgba(244, 63, 94, 0.32);
}
.masked-panel {
  background: linear-gradient(180deg, #ECFDF5 0%, #D1FAE5 100%);
  border: 1px solid rgba(16, 185, 129, 0.32);
}
.text-inner {
  font-family: var(--zd-mono);
  font-size: 13px;
  line-height: 1.8;
  white-space: pre-wrap;
  word-break: break-all;
  color: #0F172A;
}
.diff-arrow {
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  color: #9ca3af;
}
@media (max-width: 768px) {
  .kpi-value {
    font-size: 18px;
  }
  .diff-arrow {
    display: none;
  }
}
@keyframes alertPulse {
  0%,
  100% {
    box-shadow: 0 0 0 0 rgba(245, 34, 45, 0.28);
  }
  50% {
    box-shadow: 0 0 0 6px rgba(245, 34, 45, 0);
  }
}
</style>
