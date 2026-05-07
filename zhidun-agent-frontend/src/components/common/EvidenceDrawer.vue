<template>
  <a-drawer
    v-model:open="open"
    :width="720"
    :title="`证据链 · ${detail?.event_id ?? sessionStore.currentEventId ?? '未选择'}`"
    placement="right"
    @close="onClose"
  >
    <a-spin :spinning="loading">
      <a-empty v-if="!detail && !loading" description="暂无可查看的事件" />
      <template v-if="detail">
        <a-descriptions size="small" :column="2" bordered class="meta">
          <a-descriptions-item label="场景">{{ detail.scenario }}</a-descriptions-item>
          <a-descriptions-item label="处置">
            <a-tag :color="detail.action === 'block' ? 'red' : 'orange'">{{ detail.action }}</a-tag>
          </a-descriptions-item>
          <a-descriptions-item label="时间">{{ detail.timestamp }}</a-descriptions-item>
          <a-descriptions-item label="风险等级">
            <RiskTag :score="detail.risk_score_total ?? 0" />
          </a-descriptions-item>
        </a-descriptions>

        <a-timeline mode="left" class="tl">
          <a-timeline-item color="green">
            <div class="tl-title">原始输入</div>
            <div class="code-box">{{ detail.user_input }}</div>
          </a-timeline-item>

          <a-timeline-item v-if="detail.rule_hits?.length" color="purple">
            <div class="tl-title">规则命中</div>
            <a-list size="small" :data-source="detail.rule_hits" bordered>
              <template #renderItem="{ item }">
                <a-list-item>
                  <a-list-item-meta
                    :title="item.template"
                    :description="`${item.ruleId} · 权重 ${item.weight}`"
                  />
                </a-list-item>
              </template>
            </a-list>
          </a-timeline-item>

          <a-timeline-item color="orange">
            <div class="tl-title">综合评分 R={{ detail.risk_score_total ?? '—' }}</div>
            <a-row :gutter="12">
              <a-col :span="12" v-for="(v, k) in scoreMap" :key="k">
                <div class="score-row">
                  <span class="score-label">{{ k }}</span>
                  <a-progress
                    :percent="Number(v)"
                    size="small"
                    :stroke-color="{
                      '0%': Number(v) > 70 ? '#F43F5E' : Number(v) > 40 ? '#F59E0B' : '#10B981',
                      '100%': Number(v) > 70 ? '#F59E0B' : Number(v) > 40 ? '#FBBF24' : '#34D399',
                    }"
                  />
                </div>
              </a-col>
            </a-row>
          </a-timeline-item>

          <a-timeline-item color="blue">
            <div class="tl-title">Function Calling</div>
            <div class="code-box dark">
              <vue-json-pretty :data="detail.function_call" :deep="3" showLine theme="dark" />
            </div>
          </a-timeline-item>

          <a-timeline-item color="red">
            <div class="tl-title">RBAC 决断</div>
            <a-alert
              :type="detail.rbac_result.passed ? 'success' : 'error'"
              :message="detail.rbac_result.passed ? '校验通过' : '强制阻断'"
              :description="detail.rbac_result.reject_reason || '匹配角色：' + detail.rbac_result.matched_role"
              show-icon
            />
          </a-timeline-item>

          <a-timeline-item v-if="detail.output_diff" color="cyan">
            <div class="tl-title">输出脱敏对比</div>
            <a-row :gutter="12">
              <a-col :span="12">
                <div class="diff orig">原始：{{ detail.output_diff.original }}</div>
              </a-col>
              <a-col :span="12">
                <div class="diff masked">脱敏：{{ detail.output_diff.masked }}</div>
              </a-col>
            </a-row>
          </a-timeline-item>
        </a-timeline>

        <div class="actions">
          <a-button type="primary" :loading="exporting" @click="exportReport">
            <download-outlined /> 导出审计报告
          </a-button>
          <a-button @click="goFullPage">
            <expand-outlined /> 在证据链中心打开
          </a-button>
        </div>
      </template>
    </a-spin>
  </a-drawer>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import { storeToRefs } from 'pinia';
import { useRouter } from 'vue-router';
import VueJsonPretty from 'vue-json-pretty';
import 'vue-json-pretty/lib/styles.css';
import { DownloadOutlined, ExpandOutlined } from '@ant-design/icons-vue';
import { message } from 'ant-design-vue';
import { useAuditSessionStore } from '@/stores/auditSession';
import { getAuditEventDetail, requestAuditReport } from '@/api/services';
import type { AuditEventDetail } from '@/types/api';
import RiskTag from '@/components/common/RiskTag.vue';

const sessionStore = useAuditSessionStore();
const { drawerOpen, currentEventId } = storeToRefs(sessionStore);
const router = useRouter();

const open = computed<boolean>({
  get: () => drawerOpen.value,
  set: (v) => {
    if (!v) sessionStore.closeDrawer();
  },
});

const detail = ref<AuditEventDetail | null>(null);
const loading = ref(false);
const exporting = ref(false);

const scoreMap = computed(() => {
  const d = detail.value;
  if (!d) return {} as Record<string, number>;
  return {
    'S_rule': d.risk_scores.rule_score,
    'S_cls': d.risk_scores.semantic_score,
    'S_ctx': d.risk_scores.context_score,
    'S_res': d.risk_scores.resource_score,
  };
});

async function load(id: string | null) {
  if (!id) {
    detail.value = null;
    return;
  }
  loading.value = true;
  try {
    detail.value = await getAuditEventDetail(id);
  } catch {
    detail.value = null;
    message.error('事件加载失败');
  } finally {
    loading.value = false;
  }
}

watch([drawerOpen, currentEventId], ([opened, id]) => {
  if (opened && id) load(id);
});

function onClose() {
  sessionStore.closeDrawer();
}

function goFullPage() {
  if (!detail.value) return;
  sessionStore.closeDrawer();
  router.push({ path: '/secops/evidence', query: { id: detail.value.event_id } });
}

async function exportReport() {
  if (!detail.value) return;
  exporting.value = true;
  try {
    const job = await requestAuditReport(detail.value.event_id);
    if (job.downloadUrl) {
      const url = job.downloadUrl.startsWith('http')
        ? job.downloadUrl
        : `${window.location.origin}${job.downloadUrl}`;
      window.open(url, '_blank');
    }
    message.success('报告已就绪');
  } catch {
    message.error('导出失败');
  } finally {
    exporting.value = false;
  }
}
</script>

<style scoped>
.meta {
  margin-bottom: 16px;
}
.tl {
  padding-top: 4px;
}
.tl-title {
  font-weight: 600;
  margin-bottom: 6px;
  font-size: 13px;
}
.code-box {
  padding: 10px 12px;
  border-radius: 8px;
  font-family: 'SFMono-Regular', Consolas, Menlo, monospace;
  font-size: 12.5px;
  background: rgba(238, 242, 255, 0.85);
  border: 1px solid rgba(99, 102, 241, 0.18);
  color: #4338CA;
  margin-top: 4px;
  white-space: pre-wrap;
  word-break: break-all;
}
.code-box.dark {
  background: linear-gradient(165deg, #0F172A 0%, #1E1B4B 100%);
  border-color: rgba(99, 102, 241, 0.28);
  color: #E0E7FF;
}
.score-row {
  margin-bottom: 8px;
}
.score-label {
  font-size: 11px;
  color: #64748B;
  display: block;
  margin-bottom: 2px;
}
.diff {
  padding: 10px 12px;
  border-radius: 8px;
  font-family: monospace;
  font-size: 12.5px;
  line-height: 1.6;
}
.diff.orig {
  background: #FFE4E6;
  border: 1px solid rgba(244, 63, 94, 0.28);
  color: #BE123C;
}
.diff.masked {
  background: #D1FAE5;
  border: 1px solid rgba(16, 185, 129, 0.28);
  color: #047857;
}
.actions {
  display: flex;
  gap: 8px;
  margin-top: 16px;
}
</style>
