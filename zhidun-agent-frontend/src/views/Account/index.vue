<template>
  <div class="account-page">
    <!-- 账户概要 -->
    <a-card :bordered="false" class="surface-card hero-card">
      <div class="hero-grid">
        <div class="hero-id">
          <a-avatar :size="56" class="hero-avatar">
            <template #icon><user-outlined /></template>
          </a-avatar>
          <div>
            <div class="hero-title-row">
              <h2 class="hero-title">{{ profile.displayName }}</h2>
              <a-tag color="processing">{{ profile.roleCode }}</a-tag>
            </div>
            <div class="hero-sub">
              <span class="mono">{{ profile.subjectId }}</span>
              <a-divider type="vertical" class="hero-divider" />
              <span>{{ profile.tenantName }}</span>
            </div>
            <p class="hero-lead">{{ profile.scopeLine }}</p>
          </div>
        </div>
        <div class="hero-chips">
          <div class="chip">
            <span class="chip-label">身份源</span>
            <span class="chip-value">{{ profile.idp }}</span>
          </div>
          <div class="chip">
            <span class="chip-label">MFA</span>
            <a-badge :status="profile.mfaOn ? 'success' : 'default'" :text="profile.mfaOn ? '已启用' : '未启用'" />
          </div>
          <div class="chip">
            <span class="chip-label">最近登录</span>
            <span class="chip-value chip-value--sm">{{ profile.lastLogin }}</span>
          </div>
          <div class="chip">
            <span class="chip-label">来源 IP</span>
            <span class="chip-value mono chip-value--sm">{{ profile.lastIp }}</span>
          </div>
        </div>
      </div>
    </a-card>

    <a-row :gutter="[24, 24]" class="body-row" align="stretch">
      <a-col :xs="24" :xl="15" class="body-col-fill">
        <a-card :bordered="false" class="surface-card body-card" title="身份信息与工作联系">
          <template #extra>
            <a-button type="primary" :loading="savingBasic" @click="onSaveBasic">保存</a-button>
          </template>
          <div class="card-stack">
            <p class="section-lead">用于平台内展示、告警接收与审计关联；登录标识由管理员分配，不可自行修改。</p>
            <a-form
              class="pro-form"
              :model="formBasic"
              :label-col="{ flex: '132px' }"
              :wrapper-col="{ flex: '1' }"
              label-align="left"
            >
              <a-form-item label="显示名称" extra="在顶栏、审计记录与导出报告中展示。">
                <a-input v-model:value="formBasic.displayName" allow-clear />
              </a-form-item>
              <a-form-item label="登录主体标识" extra="与网关审计、RBAC 绑定一致。">
                <a-input v-model:value="formBasic.loginId" disabled class="mono-input" />
              </a-form-item>
              <a-form-item label="工作邮箱" extra="高危与策略类告警默认投递地址。">
                <a-input v-model:value="formBasic.email" type="email" allow-clear />
              </a-form-item>
              <a-form-item label="公务电话" extra="可选；用于应急联络与工单回拨。">
                <a-input v-model:value="formBasic.phone" allow-clear />
              </a-form-item>
              <a-form-item label="职责摘要" extra="便于交接与权限复核；不会下发至模型上下文。">
                <a-textarea v-model:value="formBasic.remark" :rows="3" show-count :maxlength="280" />
              </a-form-item>
            </a-form>
            <div class="card-stack-spacer" aria-hidden="true" />
          </div>
        </a-card>
      </a-col>

      <a-col :xs="24" :xl="9" class="body-col-fill">
        <a-card :bordered="false" class="surface-card body-card" title="安全与会话">
          <template #extra>
            <a-button type="primary" :loading="savingSec" @click="onSaveSecurity">保存</a-button>
          </template>
          <div class="card-stack">
            <a-descriptions bordered size="small" :column="1" class="sec-desc">
              <a-descriptions-item label="凭据托管">
                {{ profile.credentialMode }}
              </a-descriptions-item>
              <a-descriptions-item label="多因素认证">
                {{ profile.mfaOn ? 'TOTP 已绑定' : '未配置' }}
              </a-descriptions-item>
              <a-descriptions-item label="会话策略">
                闲置超时后需重新认证
              </a-descriptions-item>
            </a-descriptions>
            <div class="sec-form-block">
              <div class="block-label">闲置超时（分钟）</div>
              <a-input-number
                v-model:value="formSecurity.sessionMinutes"
                :min="15"
                :max="480"
                :step="15"
                class="session-num"
              />
              <p class="block-hint">仅影响本控制台会话；与后端网关 TTL 独立配置时以较严者为准。</p>
            </div>
            <a-divider class="compact-divider" />
            <div class="sec-row">
              <div>
                <div class="block-label">高危操作二次确认</div>
                <p class="block-hint">导出审计包、批量停用策略等操作需再次确认。</p>
              </div>
              <a-switch v-model:checked="formSecurity.strictConfirm" />
            </div>
            <div class="card-stack-spacer" aria-hidden="true" />
          </div>
        </a-card>
      </a-col>
    </a-row>

    <a-card :bordered="false" class="surface-card notify-card" title="通知策略">
      <template #extra>
        <a-button type="default" @click="onSaveNotify">保存通知偏好</a-button>
      </template>
      <p class="section-lead">控制个人订阅范围；平台级强制告警不受此处关闭。</p>
      <a-table
        :columns="notifyColumns"
        :data-source="notifyRows"
        :pagination="false"
        row-key="key"
        size="middle"
        class="notify-table"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'enabled'">
            <a-switch v-model:checked="record.enabled" size="small" />
          </template>
          <template v-if="column.key === 'channel'">
            <a-tag v-for="c in record.channels" :key="c" class="channel-tag">{{ c }}</a-tag>
          </template>
        </template>
      </a-table>
      <a-alert
        type="info"
        show-icon
        class="foot-alert"
        message="审计检索说明"
        description="策略变更、拦截流水与报告导出等记录，请在「拦截审计中心」按事件维度检索；本页配置不向模型侧下发。"
      />
    </a-card>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue';
import { UserOutlined } from '@ant-design/icons-vue';
import { message } from 'ant-design-vue';

const savingBasic = ref(false);
const savingSec = ref(false);

const profile = reactive({
  displayName: '系统管理员',
  subjectId: 'UMID-SEC-8F2A91',
  roleCode: '安全运营 · 管理员',
  tenantName: '租户：华东区生产治理域',
  scopeLine: '责任范围：策略发布、高危事件确认、合规报告导出与跨系统工单协同。',
  idp: '企业 SSO（OIDC）',
  mfaOn: true,
  lastLogin: '2026-04-22 09:18:06',
  lastIp: '10.0.12.88',
  credentialMode: '密码与 TOTP 由 IdP 托管；控制台不落库口令。',
});

const formBasic = reactive({
  displayName: profile.displayName,
  loginId: 'sec-admin@zhidun',
  email: 'sec-admin@corp.example.com',
  phone: '+86 138 **** 1024',
  remark: '对接安全运营中心 SOC 与等保测评材料输出；非业务系统最终用户。',
});

const formSecurity = reactive({
  sessionMinutes: 45,
  strictConfirm: true,
});

const notifyColumns = [
  { title: '策略项', dataIndex: 'title', key: 'title', width: '26%' },
  { title: '说明', dataIndex: 'desc', key: 'desc' },
  { title: '渠道', key: 'channel', width: '22%' },
  { title: '订阅', key: 'enabled', width: 100, align: 'center' as const },
];

const notifyRows = ref([
  {
    key: 'n1',
    title: '高危 / 阻断类事件',
    desc: '策略命中「强制阻断」或风险评分超过发布阈值时即时推送。',
    channels: ['邮件', '站内'],
    enabled: true,
  },
  {
    key: 'n2',
    title: '策略与工具白名单变更',
    desc: 'RBAC 绑定、工具注册与停用、参数边界模板变更后汇总通知。',
    channels: ['邮件'],
    enabled: true,
  },
  {
    key: 'n3',
    title: '低危观察与降噪',
    desc: '仅写入审计流水，不弹窗；适合大规模扫描期降低干扰。',
    channels: ['站内'],
    enabled: false,
  },
]);

async function onSaveBasic() {
  savingBasic.value = true;
  await delay();
  profile.displayName = formBasic.displayName.trim() || profile.displayName;
  savingBasic.value = false;
  message.success('身份信息已更新');
}

async function onSaveSecurity() {
  savingSec.value = true;
  await delay();
  savingSec.value = false;
  message.success('会话与安全偏好已更新');
}

function onSaveNotify() {
  message.success('通知策略已保存');
}

function delay(ms = 400) {
  return new Promise((r) => setTimeout(r, ms));
}
</script>

<style scoped>
.account-page {
  padding: 4px 0 12px;
  max-width: 1120px;
  margin: 0 auto;
}

.surface-card {
  position: relative;
  border-radius: 14px;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.92) !important;
  border: 1px solid rgba(148, 163, 184, 0.22) !important;
  box-shadow: 0 0 0 1px rgba(255, 255, 255, 0.85) inset, 0 8px 24px -8px rgba(99, 102, 241, 0.18) !important;
  margin-bottom: 24px;
}
.surface-card :deep(.ant-card-head) {
  border-bottom-color: rgba(148, 163, 184, 0.18);
  padding-top: 4px;
  min-height: 52px;
}
.surface-card :deep(.ant-card-head-title) {
  font-size: 16px;
  font-weight: 600;
  color: #0F172A;
  letter-spacing: -0.02em;
}

.hero-card :deep(.ant-card-body) {
  padding: 20px 24px 22px;
}

.hero-grid {
  display: flex;
  flex-wrap: wrap;
  align-items: stretch;
  justify-content: space-between;
  gap: 24px;
}

.hero-id {
  display: flex;
  gap: 18px;
  min-width: 0;
  flex: 1 1 320px;
}

.hero-avatar {
  flex-shrink: 0;
  background: linear-gradient(135deg, #6366F1 0%, #8B5CF6 100%) !important;
  box-shadow: 0 8px 16px -4px rgba(99, 102, 241, 0.42);
}

.hero-title-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
  margin-bottom: 6px;
}

.hero-title {
  margin: 0;
  font-size: 22px;
  font-weight: 700;
  color: #0F172A;
  letter-spacing: -0.03em;
  line-height: 1.25;
}

.hero-sub {
  font-size: 13px;
  color: #64748b;
  line-height: 1.5;
}

.hero-divider {
  border-color: rgba(51, 65, 85, 0.75);
}

.hero-lead {
  margin: 10px 0 0;
  font-size: 13px;
  color: #94a3b8;
  line-height: 1.65;
  max-width: 52rem;
}

.mono {
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-size: 12px;
  color: #cbd5e1;
}

.hero-chips {
  display: grid;
  grid-template-columns: repeat(2, minmax(140px, 1fr));
  gap: 12px 20px;
  flex: 0 1 280px;
  align-self: stretch;
  padding: 12px 16px;
  background: linear-gradient(160deg, rgba(255, 255, 255, 0.78) 0%, rgba(241, 245, 249, 0.9) 100%);
  border: 1px solid rgba(148, 163, 184, 0.2);
  border-radius: 12px;
  align-content: center;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.9);
}

.chip-label {
  display: block;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: #94a3b8;
  margin-bottom: 4px;
}

.chip-value {
  font-size: 13px;
  color: #0F172A;
  font-weight: 500;
}
.chip-value--sm {
  font-size: 12px;
  font-weight: 400;
  color: #475569;
}

.body-row.ant-row {
  align-items: stretch;
  margin-bottom: 24px;
}

.body-col-fill {
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.body-col-fill .body-card {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  margin-bottom: 0;
}

.body-col-fill .body-card :deep(.ant-card-body) {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.card-stack {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.card-stack-spacer {
  flex: 1;
  min-height: 0;
}

.section-lead {
  margin: 0 0 20px;
  font-size: 13px;
  color: #64748b;
  line-height: 1.6;
  max-width: 48rem;
}

.pro-form :deep(.ant-form-item) {
  margin-bottom: 18px;
}
.pro-form :deep(.ant-form-item-extra) {
  font-size: 12px;
  color: #94a3b8;
  margin-top: 4px;
}

.mono-input :deep(input) {
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-size: 13px;
}

.sec-desc {
  margin-bottom: 20px;
}
.sec-desc :deep(.ant-descriptions-item-label) {
  width: 112px;
  font-weight: 500;
  color: #6b7280;
  background: rgba(248, 250, 255, 0.95) !important;
}

.sec-form-block {
  margin-bottom: 4px;
}
.block-label {
  font-size: 13px;
  font-weight: 600;
  color: #cbd5e1;
  margin-bottom: 8px;
}
.block-hint {
  margin: 8px 0 0;
  font-size: 12px;
  color: #94a3b8;
  line-height: 1.55;
  max-width: 100%;
}
.session-num {
  width: 100%;
  max-width: 200px;
}

.compact-divider {
  margin: 16px 0;
}

.sec-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}
.sec-row :deep(.ant-switch) {
  flex-shrink: 0;
  margin-top: 4px;
}

.notify-card :deep(.ant-card-body) {
  padding-top: 12px;
}

.notify-table :deep(.ant-table-thead > tr > th) {
  background: rgba(255, 255, 255, 0.92) !important;
  font-weight: 600;
  color: #5c6370;
  font-size: 13px;
}
.channel-tag {
  margin: 0 4px 4px 0;
  border-radius: 4px;
}

.foot-alert {
  margin-top: 20px;
  border-radius: 8px;
}
.foot-alert :deep(.ant-alert-description) {
  font-size: 13px;
  line-height: 1.6;
}
</style>
