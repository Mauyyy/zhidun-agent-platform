import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router';

import Dashboard from '@/views/Dashboard/index.vue';
import Account from '@/views/Account/index.vue';

// 安全运营中心：保留并复用原 ChatDemo / AuditDetail 实现，仅在路由层落到新位置
import ChatHall from '@/views/ChatDemo/index.vue';
import EvidenceCenter from '@/views/AuditDetail/index.vue';

// 工具调用监控台 / 综合审计报告（新页面）
const ToolMonitor = () => import('@/views/SecOps/ToolMonitor/index.vue');
const ReportCenter = () => import('@/views/SecOps/ReportCenter/index.vue');

// 防护策略编排
//   - RBAC 复用原 ToolAudit（其本身就是工具策略 CRUD），仅在路由上落到「策略编排」
//   - 注入规则、脱敏模板为新页面
import RbacPolicy from '@/views/ToolAudit/index.vue';
const InjectionRules = () => import('@/views/Policy/InjectionRules/index.vue');
const MaskTemplates = () => import('@/views/Policy/MaskTemplates/index.vue');

// 资产与应用接入（已合并为单页）
const AgentApps = () => import('@/views/Assets/AgentApps/index.vue');

// 系统配置
const SettingsPage = () => import('@/views/Settings/index.vue');

const routes: RouteRecordRaw[] = [
  { path: '/', redirect: '/dashboard' },

  // 📊 态势总览
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: Dashboard,
    meta: { title: '综合安全态势大盘', section: 'dashboard' },
  },

  // 🛡️ 安全运营中心
  {
    path: '/secops/chat',
    name: 'ChatHall',
    component: ChatHall,
    meta: { title: '实时会话审计大厅', section: 'secops' },
  },
  {
    path: '/secops/tools',
    name: 'ToolMonitor',
    component: ToolMonitor,
    meta: { title: '工具调用监控台', section: 'secops' },
  },
  {
    path: '/secops/evidence',
    name: 'EvidenceCenter',
    component: EvidenceCenter,
    meta: { title: '证据链与溯源中心', section: 'secops' },
  },
  {
    path: '/secops/reports',
    name: 'ReportCenter',
    component: ReportCenter,
    meta: { title: '综合审计报告生成', section: 'secops' },
  },

  // ⚙️ 防护策略编排
  {
    path: '/policy/injection',
    name: 'InjectionRules',
    component: InjectionRules,
    meta: { title: '注入检测规则库管理', section: 'policy' },
  },
  {
    path: '/policy/rbac',
    name: 'RbacPolicy',
    component: RbacPolicy,
    meta: { title: 'RBAC 越权防护策略', section: 'policy' },
  },
  {
    path: '/policy/mask',
    name: 'MaskTemplates',
    component: MaskTemplates,
    meta: { title: '数据去标识化（脱敏）模板', section: 'policy' },
  },

  // 📦 资产与应用接入
  {
    path: '/assets',
    name: 'AgentApps',
    component: AgentApps,
    meta: { title: '资产与应用接入', section: 'assets' },
  },
  {
    path: '/assets/agents',
    redirect: '/assets',
  },
  {
    path: '/assets/sensitive',
    redirect: '/assets',
  },

  // 🛠️ 系统配置
  {
    path: '/settings',
    name: 'Settings',
    component: SettingsPage,
    meta: { title: '系统配置', section: 'settings' },
  },
  {
    path: '/settings/alerts',
    redirect: '/settings',
  },
  {
    path: '/settings/operation-logs',
    redirect: '/settings',
  },

  // 个人账户
  {
    path: '/account',
    name: 'Account',
    component: Account,
    meta: { title: '个人账户', section: 'account' },
  },

  // 旧路径兼容
  { path: '/chat', redirect: '/secops/chat' },
  { path: '/tool-audit', redirect: '/policy/rbac' },
  { path: '/event-list', redirect: '/secops/reports' },
  { path: '/audit-detail', redirect: '/secops/evidence' },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

export default router;
