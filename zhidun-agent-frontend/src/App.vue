<template>
  <a-config-provider :theme="antdTheme" component-size="middle">
  <a-app>
  <a-layout class="app-root">
    <!-- 全局网络流动装饰层：横向波浪 + 漂浮粒子 -->
    <div class="app-bg-decor" aria-hidden="true">
      <svg class="bg-waves" viewBox="0 0 1600 420" preserveAspectRatio="none">
        <defs>
          <linearGradient id="zdWaveA" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0%" stop-color="#818cf8" stop-opacity="0" />
            <stop offset="35%" stop-color="#818cf8" stop-opacity="0.55" />
            <stop offset="100%" stop-color="#67e8f9" stop-opacity="0" />
          </linearGradient>
          <linearGradient id="zdWaveB" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0%" stop-color="#67e8f9" stop-opacity="0" />
            <stop offset="50%" stop-color="#6366f1" stop-opacity="0.45" />
            <stop offset="100%" stop-color="#8b5cf6" stop-opacity="0" />
          </linearGradient>
          <linearGradient id="zdWaveC" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0%" stop-color="#a5b4fc" stop-opacity="0" />
            <stop offset="45%" stop-color="#8b5cf6" stop-opacity="0.32" />
            <stop offset="100%" stop-color="#06b6d4" stop-opacity="0" />
          </linearGradient>
        </defs>
        <path class="wave wave-a" d="M0,160 C220,110 420,220 640,170 C860,120 1060,230 1280,180 C1420,150 1520,190 1600,170 L1600,0 L0,0 Z" fill="url(#zdWaveA)" />
        <path class="wave wave-b" d="M0,200 C240,150 460,250 680,210 C900,170 1120,270 1320,220 C1460,190 1540,210 1600,200 L1600,0 L0,0 Z" fill="url(#zdWaveB)" />
        <path class="wave wave-c" d="M0,120 C220,80 420,190 640,140 C860,90 1080,200 1300,150 C1440,120 1540,150 1600,135 L1600,0 L0,0 Z" fill="url(#zdWaveC)" />
        <g class="wave-lines" stroke-linecap="round" fill="none">
          <path d="M0,96 C300,50 620,150 920,100 C1180,60 1400,120 1600,90" stroke="#818cf8" stroke-opacity="0.45" stroke-width="1.1" stroke-dasharray="6 14" />
          <path d="M0,140 C280,110 600,200 920,150 C1200,110 1420,170 1600,140" stroke="#06b6d4" stroke-opacity="0.32" stroke-width="1" stroke-dasharray="4 12" />
          <path d="M0,60 C320,30 620,110 940,70 C1200,40 1420,90 1600,60" stroke="#8b5cf6" stroke-opacity="0.32" stroke-width="1" stroke-dasharray="2 16" />
        </g>
      </svg>
      <div class="bg-particles">
        <span class="pt pt-1" /><span class="pt pt-2" /><span class="pt pt-3" />
        <span class="pt pt-4" /><span class="pt pt-5" /><span class="pt pt-6" />
        <span class="pt pt-7" /><span class="pt pt-8" />
      </div>
    </div>

    <a-layout-sider v-model:collapsed="collapsed" collapsible width="232" class="app-shell-sider">
      <div class="sider-decor" aria-hidden="true" />
      <div class="sider-top">
        <div class="logo">
          <div class="logo-mark">
            <span class="logo-ring" />
            <safety-certificate-filled class="logo-icon" />
          </div>
          <transition name="sider-fade">
            <span v-if="!collapsed" class="logo-text">智盾 Agent</span>
          </transition>
        </div>
      </div>
      <div class="sider-menu-scroll">
      <a-menu
        v-model:selectedKeys="selectedKeys"
        v-model:openKeys="openKeys"
        theme="light"
        mode="inline"
        class="app-shell-menu app-shell-menu--frost"
      >
        <a-menu-item key="dashboard">
          <router-link to="/dashboard">
            <dashboard-outlined />
            <span>态势总览</span>
          </router-link>
        </a-menu-item>

        <a-sub-menu key="secops">
          <template #icon><security-scan-outlined /></template>
          <template #title>安全运营中心</template>
          <a-menu-item key="secops-chat">
            <router-link to="/secops/chat"><message-outlined /><span>实时会话审计大厅</span></router-link>
          </a-menu-item>
          <a-menu-item key="secops-tools">
            <router-link to="/secops/tools"><api-outlined /><span>工具调用监控台</span></router-link>
          </a-menu-item>
          <a-menu-item key="secops-evidence">
            <router-link to="/secops/evidence"><file-search-outlined /><span>证据链与溯源中心</span></router-link>
          </a-menu-item>
          <a-menu-item key="secops-reports">
            <router-link to="/secops/reports"><file-protect-outlined /><span>综合审计报告</span></router-link>
          </a-menu-item>
        </a-sub-menu>

        <a-sub-menu key="policy">
          <template #icon><setting-outlined /></template>
          <template #title>防护策略编排</template>
          <a-menu-item key="policy-injection">
            <router-link to="/policy/injection"><filter-outlined /><span>注入检测规则库</span></router-link>
          </a-menu-item>
          <a-menu-item key="policy-rbac">
            <router-link to="/policy/rbac"><lock-outlined /><span>RBAC 越权防护</span></router-link>
          </a-menu-item>
          <a-menu-item key="policy-mask">
            <router-link to="/policy/mask"><eye-invisible-outlined /><span>数据脱敏模板</span></router-link>
          </a-menu-item>
        </a-sub-menu>

        <a-menu-item key="assets">
          <router-link to="/assets"><appstore-outlined /><span>资产与应用接入</span></router-link>
        </a-menu-item>

        <a-menu-item key="settings">
          <router-link to="/settings"><tool-outlined /><span>系统配置</span></router-link>
        </a-menu-item>

        <a-menu-item key="account">
          <router-link to="/account">
            <idcard-outlined />
            <span>个人账户</span>
          </router-link>
        </a-menu-item>
      </a-menu>
      </div>
      <div v-if="!collapsed" class="sider-footer">
        <div class="sider-footer-label">防护链路</div>
        <div class="sider-footer-dots">
          <span class="dot on" /><span class="dot on" /><span class="dot pulse" />
        </div>
        <span class="sider-footer-text">输入 · 执行 · 输出 审计就绪</span>
      </div>
    </a-layout-sider>

    <a-layout class="app-main-layout" :class="{ 'is-hero-page': isDashboard }">
      <a-layout-header
        class="header-glass"
        :class="{ 'is-hero': isDashboard }"
        :style="headerBgStyle"
      >
        <!-- 顶部窄行：业务系统名称 + 时间 + 操作图标 + 用户头像 -->
        <div class="header-topbar">
          <div class="brand-block">
            <span class="brand-dot" />
            <span class="brand-name">智盾 Agent</span>
          </div>
          <div class="topbar-right">
            <span v-if="isDashboard" class="now-time">{{ currentTimeText }}</span>
            <span class="env-pill">演示环境</span>
            <span class="env-pill env-pill--mode" :class="realtimeModeClass">{{ realtimeStatus }}</span>
            <a-tooltip :title="isFullscreen ? '退出全屏' : '沉浸式演示模式'">
              <span class="action-icon-wrap" @click="toggleFullScreen">
                <fullscreen-exit-outlined v-if="isFullscreen" />
                <fullscreen-outlined v-else />
              </span>
            </a-tooltip>
            <a-badge dot>
              <span class="action-icon-wrap"><bell-outlined /></span>
            </a-badge>
            <router-link to="/account" class="user-profile-link">
              <div class="user-profile">
                <a-avatar :size="34" class="user-avatar">
                  <template #icon><user-outlined /></template>
                </a-avatar>
                <div class="user-meta">
                  <span class="username">系统管理员</span>
                  <span class="user-role">安全运营 · 管理员</span>
                </div>
              </div>
            </router-link>
          </div>
        </div>

        <!-- 中央页面标题 -->
        <div class="header-content">
          <div class="header-left">
            <h1 class="page-heading">{{ currentRouteName }}</h1>
            <p v-if="currentPageSub" class="page-sub">{{ currentPageSub }}</p>
          </div>
        </div>

        <!-- Hero 装饰：全球网络连接 + 底部波浪 -->
        <template v-if="isDashboard">
          <svg class="hero-globe" viewBox="0 0 480 320" aria-hidden="true">
            <defs>
              <radialGradient id="zdGlobeFill" cx="50%" cy="50%" r="55%">
                <stop offset="0%" stop-color="#3B82F6" stop-opacity="0.36" />
                <stop offset="60%" stop-color="#1D4ED8" stop-opacity="0.16" />
                <stop offset="100%" stop-color="#0B1E40" stop-opacity="0" />
              </radialGradient>
              <linearGradient id="zdGlobeArc" x1="0" y1="0" x2="1" y2="1">
                <stop offset="0%" stop-color="#60A5FA" stop-opacity="0.9" />
                <stop offset="100%" stop-color="#22D3EE" stop-opacity="0.4" />
              </linearGradient>
            </defs>
            <circle cx="240" cy="170" r="140" fill="url(#zdGlobeFill)" />
            <g fill="none" stroke="url(#zdGlobeArc)" stroke-width="1.1">
              <ellipse cx="240" cy="170" rx="140" ry="140" stroke-opacity="0.45" />
              <ellipse cx="240" cy="170" rx="140" ry="60" stroke-opacity="0.55" />
              <ellipse cx="240" cy="170" rx="140" ry="100" stroke-opacity="0.35" />
              <ellipse cx="240" cy="170" rx="60" ry="140" stroke-opacity="0.4" />
              <ellipse cx="240" cy="170" rx="100" ry="140" stroke-opacity="0.3" />
              <line x1="240" y1="30" x2="240" y2="310" stroke-opacity="0.35" />
              <line x1="100" y1="170" x2="380" y2="170" stroke-opacity="0.35" />
            </g>
            <g fill="#A0B9E0">
              <circle cx="180" cy="118" r="2.4" opacity="0.85" />
              <circle cx="320" cy="142" r="2" opacity="0.7" />
              <circle cx="276" cy="206" r="2.6" opacity="0.95" />
              <circle cx="208" cy="226" r="2" opacity="0.6" />
              <circle cx="156" cy="190" r="1.8" opacity="0.75" />
              <circle cx="354" cy="200" r="2.2" opacity="0.85" />
              <circle cx="248" cy="92" r="2.2" opacity="0.8" />
              <circle cx="298" cy="108" r="1.8" opacity="0.6" />
            </g>
            <g stroke="#67E8F9" stroke-width="1" stroke-opacity="0.55" fill="none">
              <path d="M180 118 Q230 80 276 206" />
              <path d="M320 142 Q260 170 208 226" />
              <path d="M156 190 Q220 160 354 200" />
            </g>
          </svg>

          <svg class="hero-wave" viewBox="0 0 1600 80" preserveAspectRatio="none" aria-hidden="true">
            <path d="M0,80 L0,38 C200,72 420,4 720,32 C980,56 1240,12 1600,40 L1600,80 Z" fill="#DCE6F3" />
            <path d="M0,80 L0,52 C260,82 480,18 760,46 C1020,70 1280,28 1600,54 L1600,80 Z" fill="#DCE6F3" opacity="0.6" />
          </svg>
        </template>
      </a-layout-header>

      <a-layout-content class="shell-content" :class="{ 'is-hero-page': isDashboard }">
        <div class="content-inner">
          <router-view v-slot="{ Component }">
            <div class="page-outlet">
              <Suspense>
                <template #default>
                  <transition name="page-fade" mode="out-in">
                    <div class="route-view-shell" :key="routeViewKey">
                      <component :is="Component" />
                    </div>
                  </transition>
                </template>
                <template #fallback>
                  <div class="page-loading">
                    <a-spin />
                  </div>
                </template>
              </Suspense>
            </div>
          </router-view>
        </div>
      </a-layout-content>
    </a-layout>
  </a-layout>

  <!-- 全局证据链抽屉：任一页面 setOpenEvent(eventId) 即可弹出 -->
  <EvidenceDrawer />
  </a-app>
  </a-config-provider>
</template>

<script setup lang="ts">
import { ref, watch, computed, onMounted, onBeforeUnmount } from 'vue';
import { useRoute } from 'vue-router';
import { storeToRefs } from 'pinia';
import {
  DashboardOutlined,
  MessageOutlined,
  SecurityScanOutlined,
  ApiOutlined,
  SafetyCertificateFilled,
  BellOutlined,
  UserOutlined,
  IdcardOutlined,
  FullscreenOutlined,
  FullscreenExitOutlined,
  FileSearchOutlined,
  FileProtectOutlined,
  SettingOutlined,
  FilterOutlined,
  LockOutlined,
  EyeInvisibleOutlined,
  AppstoreOutlined,
  ToolOutlined,
} from '@ant-design/icons-vue';
import { useSecurityRealtimeStore } from '@/stores/securityRealtime';
import { theme } from 'ant-design-vue';
import EvidenceDrawer from '@/components/common/EvidenceDrawer.vue';
import TopBackgroundUrl from '@/assets/Top-background.jpg';

/**
 * 轻量科技风 (Light Tech / Soft UI)
 * 全局浅蓝灰底 + 纯白卡片 + 蓝色弥散阴影 + 16px 大圆角
 * 主色：#3B82F6 (Blue)，状态色：Success / Warning / Error
 */
const antdTheme = {
  algorithm: theme.defaultAlgorithm,
  token: {
    colorPrimary: '#0369A1',
    colorInfo: '#0EA5E9',
    colorSuccess: '#52C41A',
    colorWarning: '#FA8C16',
    colorError: '#F5222D',
    colorLink: '#0369A1',

    colorBgBase: '#EEF5FB',
    colorBgLayout: '#EEF5FB',
    colorBgContainer: '#FFFFFF',
    colorBgElevated: '#FFFFFF',
    colorBgSpotlight: '#F0F7FF',

    colorBorder: 'rgba(220, 230, 245, 1)',
    colorBorderSecondary: 'rgba(226, 232, 240, 0.95)',

    colorText: '#1F2937',
    colorTextHeading: '#0F172A',
    colorTextSecondary: '#475569',
    colorTextTertiary: '#6B7280',

    borderRadius: 8,
    borderRadiusLG: 16,
    borderRadiusSM: 6,

    boxShadow: '0 8px 24px rgba(15, 23, 42, 0.06)',
    boxShadowSecondary: '0 14px 34px rgba(15, 23, 42, 0.09)',
    boxShadowTertiary: '0 8px 24px rgba(15, 23, 42, 0.06)',

    fontFamily: '-apple-system, BlinkMacSystemFont, "Inter", "Segoe UI", Roboto, "Helvetica Neue", "PingFang SC", "Microsoft YaHei", sans-serif',
    fontSize: 13,
  },
  components: {
    Button: {
      borderRadius: 8,
      controlHeight: 36,
      controlHeightLG: 42,
      controlHeightSM: 28,
      fontWeight: 500,
    },
    Card: {
      colorBorderSecondary: 'rgba(220, 230, 245, 0.9)',
      headerBg: 'transparent',
      boxShadowTertiary: '0 4px 20px rgba(45, 90, 150, 0.08)',
      borderRadiusLG: 16,
      paddingLG: 24,
    },
    Tag: {
      lineWidth: 0,
      borderRadiusSM: 999,
      defaultBg: '#F5F5F7',
      defaultColor: '#595959',
    },
    Menu: {
      itemBorderRadius: 8,
      itemHeight: 40,
      collapsedIconSize: 16,
      itemColor: '#475569',
      itemSelectedBg: '#E6F4FF',
      itemSelectedColor: '#0369A1',
      itemHoverBg: '#F0F7FF',
      itemHoverColor: '#0369A1',
    },
    Drawer: {
      colorBgElevated: '#FFFFFF',
      paddingLG: 24,
    },
    Modal: {
      borderRadiusLG: 16,
    },
    Table: {
      borderRadius: 12,
      headerBg: '#FAFBFC',
      headerColor: '#475569',
      rowHoverBg: '#F5F9FF',
    },
    Input: {
      borderRadius: 8,
      controlHeight: 36,
      activeBorderColor: '#0369A1',
      hoverBorderColor: '#0EA5E9',
    },
    Select: {
      borderRadius: 8,
      controlHeight: 36,
    },
    Progress: {
      defaultColor: '#0369A1',
    },
    Switch: {
      colorPrimary: '#0369A1',
    },
    Timeline: {
      tailColor: 'rgba(59, 130, 246, 0.18)',
    },
  },
};

const collapsed = ref(false);
const selectedKeys = ref<string[]>(['dashboard']);
const openKeys = ref<string[]>(['secops']);
const isFullscreen = ref(false);
const route = useRoute();
const securityRealtime = useSecurityRealtimeStore();
const { statusText, runtimeMode } = storeToRefs(securityRealtime);

/** 路径 → 菜单 key + 显示标题 */
const routeMeta: Record<string, { key: string; parent?: string; title: string; subtitle?: string }> = {
  '/dashboard': { key: 'dashboard', title: '综合安全态势大盘', subtitle: '一屏看态势' },
  '/secops/chat': { key: 'secops-chat', parent: 'secops', title: '实时会话审计大厅' },
  '/secops/tools': { key: 'secops-tools', parent: 'secops', title: '工具调用监控台' },
  '/secops/evidence': { key: 'secops-evidence', parent: 'secops', title: '证据链与溯源中心' },
  '/secops/reports': { key: 'secops-reports', parent: 'secops', title: '综合审计报告生成' },
  '/policy/injection': { key: 'policy-injection', parent: 'policy', title: '注入检测规则库管理' },
  '/policy/rbac': { key: 'policy-rbac', parent: 'policy', title: 'RBAC 越权防护策略' },
  '/policy/mask': { key: 'policy-mask', parent: 'policy', title: '数据去标识化（脱敏）模板' },
  '/assets': { key: 'assets', title: '资产与应用接入' },
  '/assets/agents': { key: 'assets', title: '资产与应用接入' },
  '/assets/sensitive': { key: 'assets', title: '资产与应用接入' },
  '/settings': { key: 'settings', title: '系统配置' },
  '/settings/alerts': { key: 'settings', title: '系统配置' },
  '/settings/operation-logs': { key: 'settings', title: '系统配置' },
  '/account': { key: 'account', title: '个人账户' },
};

const currentRouteName = computed(() => {
  return routeMeta[route.path]?.title ?? '智盾 Agent 控制台';
});

const currentPageSub = computed(() => routeMeta[route.path]?.subtitle);

const isDashboard = computed(() => route.path === '/dashboard');

const currentTimeText = ref('');
let timeTimer: ReturnType<typeof setInterval> | null = null;
function refreshTime() {
  const d = new Date();
  const pad = (n: number) => String(n).padStart(2, '0');
  currentTimeText.value =
    `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ` +
    `${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`;
}

const toggleFullScreen = () => {
  if (!document.fullscreenElement) {
    document.documentElement.requestFullscreen();
    isFullscreen.value = true;
  } else {
    document.exitFullscreen();
    isFullscreen.value = false;
  }
};

const realtimeStatus = computed(() => statusText.value);
const realtimeModeClass = computed(() => {
  if (runtimeMode.value === 'push') return 'is-push';
  if (runtimeMode.value === 'poll') return 'is-poll';
  return 'is-idle';
});

const headerBgStyle = computed(() => ({
  // 通过 CSS 变量注入真实资源 URL，避免 CSS url('@/...') 别名解析不生效
  '--zd-header-bg': `url("${TopBackgroundUrl}")`,
}) as Record<string, string>);

/**
 * 关键点：为 router-view 内的动态组件提供稳定 key。
 * 否则在 transition(out-in) + 异步路由组件的组合下，可能出现组件复用/挂载未触发导致的内容区空白。
 */
const routeViewKey = computed(() => route.fullPath);

watch(
  () => route.path,
  (path) => {
    const meta = routeMeta[path];
    if (!meta) return;
    selectedKeys.value = [meta.key];
    if (meta.parent && !openKeys.value.includes(meta.parent)) {
      openKeys.value = [...openKeys.value, meta.parent];
    }
  },
  { immediate: true }
);

onMounted(() => {
  void securityRealtime.start();
  refreshTime();
  timeTimer = setInterval(refreshTime, 1000);
});

onBeforeUnmount(() => {
  securityRealtime.stop();
  if (timeTimer) clearInterval(timeTimer);
});
</script>

<style>
.app-root {
  min-height: 100vh;
  position: relative;
  /* 页面底色：略深的灰蓝，增强白卡对比 */
  background: #DCE6F3;
}

/* ============ 全局网络流动装饰层（轻量科技风：弱化）============ */
.app-bg-decor {
  position: fixed;
  inset: 0;
  pointer-events: none;
  z-index: 0;
  overflow: hidden;
  display: none;
}

.bg-waves {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: clamp(340px, 44vh, 480px);
  opacity: 0.9;
  mix-blend-mode: screen;
  filter: saturate(1.15);
}

.bg-waves .wave {
  transform-origin: 50% 50%;
}

.bg-waves .wave-a {
  animation: zdWaveShift 14s ease-in-out infinite alternate;
}
.bg-waves .wave-b {
  animation: zdWaveShift 18s ease-in-out -4s infinite alternate;
}
.bg-waves .wave-c {
  animation: zdWaveShift 22s ease-in-out -8s infinite alternate;
}

.bg-waves .wave-lines path {
  stroke-dashoffset: 0;
  animation: zdDashFlow 9s linear infinite;
}
.bg-waves .wave-lines path:nth-child(2) {
  animation-duration: 13s;
  animation-direction: reverse;
}
.bg-waves .wave-lines path:nth-child(3) {
  animation-duration: 16s;
}

@keyframes zdWaveShift {
  0% {
    transform: translate3d(0, 0, 0);
  }
  100% {
    transform: translate3d(-24px, 6px, 0);
  }
}

@keyframes zdDashFlow {
  0% {
    stroke-dashoffset: 0;
  }
  100% {
    stroke-dashoffset: -240;
  }
}

.bg-particles .pt {
  position: absolute;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(129, 140, 248, 0.9) 0%, rgba(103, 232, 249, 0.45) 55%, transparent 75%);
  filter: blur(0.4px);
  opacity: 0.55;
  animation: zdFloat 14s ease-in-out infinite;
}

.bg-particles .pt-1 { top: 14%; left: 12%; animation-delay: 0s; }
.bg-particles .pt-2 { top: 22%; left: 32%; animation-delay: -3s; width: 4px; height: 4px; }
.bg-particles .pt-3 { top: 8%;  left: 58%; animation-delay: -6s; width: 8px; height: 8px; }
.bg-particles .pt-4 { top: 18%; left: 74%; animation-delay: -2s; }
.bg-particles .pt-5 { top: 28%; left: 88%; animation-delay: -9s; width: 5px; height: 5px; }
.bg-particles .pt-6 { top: 34%; left: 16%; animation-delay: -5s; width: 4px; height: 4px; }
.bg-particles .pt-7 { top: 40%; left: 46%; animation-delay: -11s; width: 5px; height: 5px; }
.bg-particles .pt-8 { top: 26%; left: 24%; animation-delay: -7s; width: 3px; height: 3px; }

@keyframes zdFloat {
  0%, 100% {
    transform: translate3d(0, 0, 0);
    opacity: 0.35;
  }
  25% {
    transform: translate3d(14px, -12px, 0);
    opacity: 0.75;
  }
  50% {
    transform: translate3d(-6px, -22px, 0);
    opacity: 0.5;
  }
  75% {
    transform: translate3d(18px, -6px, 0);
    opacity: 0.8;
  }
}

/* ============ 侧栏：轻量科技 · 层次 / 动效（尊重 prefers-reduced-motion）============ */
.app-shell-sider {
  position: sticky !important;
  top: 0;
  height: 100vh !important;
  max-height: 100vh !important;
  overflow: hidden;
  z-index: 30;
  /* 科技感：磨砂玻璃 + 纵深渐变 + 轻霓虹边缘 */
  background:
    radial-gradient(120% 70% at 12% 0%, rgba(59, 130, 246, 0.16) 0%, transparent 58%),
    radial-gradient(100% 60% at 10% 100%, rgba(34, 211, 238, 0.12) 0%, transparent 55%),
    linear-gradient(180deg, rgba(255, 255, 255, 0.92) 0%, rgba(248, 251, 255, 0.78) 44%, rgba(241, 245, 249, 0.92) 100%) !important;
  border-right: 1px solid rgba(59, 130, 246, 0.16);
  box-shadow:
    10px 0 46px rgba(15, 23, 42, 0.06),
    1px 0 0 rgba(255, 255, 255, 0.65) inset;
  isolation: isolate;
}

/* 极弱环境光 + 细网格，增加纵深 */
.app-shell-sider::before {
  content: '';
  position: absolute;
  inset: 0;
  pointer-events: none;
  z-index: 0;
  opacity: 0.9;
  background:
    /* 电路网格 */
    linear-gradient(rgba(100, 116, 139, 0.045) 1px, transparent 1px),
    linear-gradient(90deg, rgba(100, 116, 139, 0.045) 1px, transparent 1px),
    /* 细微对角纹理 */
    repeating-linear-gradient(135deg, rgba(99, 102, 241, 0.06) 0 2px, transparent 2px 10px);
  background-size: 20px 20px, 20px 20px, 14px 14px;
  -webkit-mask-image: linear-gradient(90deg, #000 0%, #000 78%, transparent 100%);
  mask-image: linear-gradient(90deg, #000 0%, #000 78%, transparent 100%);
}

/* 顶部霓虹扫描线（很克制） */
.app-shell-sider::after {
  content: '';
  position: absolute;
  left: 0;
  right: 0;
  top: 64px;
  height: 1px;
  pointer-events: none;
  z-index: 0;
  background: linear-gradient(90deg, transparent, rgba(34, 211, 238, 0.5), rgba(99, 102, 241, 0.45), transparent);
  opacity: 0.55;
}

.sider-decor {
  position: absolute;
  inset: 0;
  pointer-events: none;
  z-index: 0;
  background: linear-gradient(
    180deg,
    rgba(34, 211, 238, 0.06) 0%,
    transparent 32%,
    rgba(99, 102, 241, 0.04) 100%
  );
  animation: siderAmbient 14s ease-in-out infinite alternate;
}

@keyframes siderAmbient {
  0% {
    opacity: 0.5;
  }
  100% {
    opacity: 1;
  }
}

.app-shell-sider .ant-layout-sider-children {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  height: 100vh;
  max-height: 100vh;
  overflow: hidden;
}

.sider-top {
  flex-shrink: 0;
  z-index: 1;
  animation: siderLogoReveal 0.5s cubic-bezier(0.22, 1, 0.36, 1) both;
}

@keyframes siderLogoReveal {
  from {
    opacity: 0;
    transform: translate3d(-8px, 0, 0);
  }
  to {
    opacity: 1;
    transform: translate3d(0, 0, 0);
  }
}

.sider-menu-scroll {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 8px 0 0;
  scrollbar-gutter: stable;
  -webkit-overflow-scrolling: touch;
}

.sider-menu-scroll::-webkit-scrollbar {
  width: 5px;
}
.sider-menu-scroll::-webkit-scrollbar-track {
  background: transparent;
}
.sider-menu-scroll::-webkit-scrollbar-thumb {
  background: rgba(100, 116, 139, 0.28);
  border-radius: 100px;
}
.sider-menu-scroll::-webkit-scrollbar-thumb:hover {
  background: rgba(59, 130, 246, 0.4);
}

.sider-fade-enter-active,
.sider-fade-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}
.sider-fade-enter-from,
.sider-fade-leave-to {
  opacity: 0;
  transform: translate3d(-6px, 0, 0);
}

.app-shell-sider .ant-layout-sider-trigger {
  flex-shrink: 0;
  background: linear-gradient(180deg, rgba(248, 250, 252, 0.98) 0%, #f0f4f8 100%) !important;
  border-top: 1px solid rgba(59, 130, 246, 0.12) !important;
  color: #64748b !important;
  z-index: 40;
  transition:
    color 0.2s ease,
    background 0.25s ease,
    box-shadow 0.25s ease;
}

.app-shell-sider .ant-layout-sider-trigger:hover {
  color: #2563eb !important;
  background: linear-gradient(180deg, #eff6ff 0%, #dbeafe 100%) !important;
  box-shadow: 0 -4px 20px rgba(37, 99, 235, 0.12);
}

.logo {
  min-height: 64px;
  display: flex;
  align-items: center;
  padding: 0 16px 0 18px;
  gap: 12px;
  position: relative;
  border-bottom: 1px solid transparent;
  background:
    radial-gradient(120% 80% at 0% 0%, rgba(34, 211, 238, 0.14) 0%, transparent 55%),
    linear-gradient(180deg, rgba(255, 255, 255, 0.92) 0%, rgba(248, 250, 252, 0.55) 100%);
  backdrop-filter: blur(12px);
}

.logo::after {
  content: '';
  position: absolute;
  left: 12px;
  right: 12px;
  bottom: 0;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(59, 130, 246, 0.2), rgba(100, 116, 139, 0.12), transparent);
}

.logo-mark {
  position: relative;
  flex-shrink: 0;
  width: 40px;
  height: 40px;
  border-radius: 12px;
  background: linear-gradient(135deg, #071A33 0%, #1D4ED8 52%, #22D3EE 110%);
  border: 1px solid rgba(255, 255, 255, 0.28);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow:
    0 10px 26px rgba(37, 99, 235, 0.38),
    0 0 22px rgba(34, 211, 238, 0.16),
    0 0 0 1px rgba(255, 255, 255, 0.12) inset;
  transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1), box-shadow 0.3s ease;
}
.logo:hover .logo-mark {
  transform: scale(1.04);
  box-shadow:
    0 8px 24px rgba(37, 99, 235, 0.55),
    0 0 0 1px rgba(255, 255, 255, 0.18) inset;
}

.logo-ring {
  position: absolute;
  inset: -4px;
  border-radius: 14px;
  border: 1px solid rgba(96, 165, 250, 0.55);
  animation: zdLogoRing 2.6s ease-in-out infinite;
  pointer-events: none;
}

@keyframes zdLogoRing {
  0%,
  100% {
    opacity: 0.85;
    transform: scale(1);
  }
  50% {
    opacity: 0.25;
    transform: scale(1.14);
  }
}

.logo-icon {
  font-size: 22px;
  color: #fff;
  filter: drop-shadow(0 1px 2px rgba(15, 23, 42, 0.5));
}

.logo-text {
  font-weight: 800;
  font-size: 17px;
  letter-spacing: 0.03em;
  background: linear-gradient(100deg, #0f172a 0%, #1e3a5f 45%, #1d4ed8 100%);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  color: transparent;
}

.app-shell-menu {
  margin-top: 4px;
  padding: 0 10px 20px;
  border-inline: none !important;
  background: transparent !important;
}

/* 一级项入场（仅视觉，不打断操作） */
.app-shell-menu > .ant-menu-item,
.app-shell-menu > .ant-menu-submenu {
  animation: siderItemStagger 0.42s cubic-bezier(0.22, 1, 0.36, 1) backwards;
}
.app-shell-menu > .ant-menu-item:nth-child(1),
.app-shell-menu > .ant-menu-submenu:nth-child(1) { animation-delay: 0.04s; }
.app-shell-menu > .ant-menu-item:nth-child(2),
.app-shell-menu > .ant-menu-submenu:nth-child(2) { animation-delay: 0.08s; }
.app-shell-menu > .ant-menu-item:nth-child(3),
.app-shell-menu > .ant-menu-submenu:nth-child(3) { animation-delay: 0.12s; }
.app-shell-menu > .ant-menu-item:nth-child(4),
.app-shell-menu > .ant-menu-submenu:nth-child(4) { animation-delay: 0.16s; }
.app-shell-menu > .ant-menu-item:nth-child(5),
.app-shell-menu > .ant-menu-submenu:nth-child(5) { animation-delay: 0.2s; }
.app-shell-menu > .ant-menu-item:nth-child(6),
.app-shell-menu > .ant-menu-submenu:nth-child(6) { animation-delay: 0.24s; }
.app-shell-menu > .ant-menu-item:nth-child(7),
.app-shell-menu > .ant-menu-submenu:nth-child(7) { animation-delay: 0.28s; }

@keyframes siderItemStagger {
  from {
    opacity: 0;
    transform: translate3d(-10px, 6px, 0);
  }
  to {
    opacity: 1;
    transform: translate3d(0, 0, 0);
  }
}

.app-shell-menu.ant-menu-light .ant-menu-item,
.app-shell-menu.ant-menu-light .ant-menu-submenu-title {
  margin: 3px 0 !important;
  width: 100% !important;
  border-radius: 10px;
  height: 40px !important;
  line-height: 40px !important;
  color: #475569 !important;
  transition:
    background 0.25s ease,
    color 0.2s ease,
    box-shadow 0.25s ease,
    transform 0.2s ease;
}

.app-shell-menu.ant-menu-light .ant-menu-item:hover,
.app-shell-menu.ant-menu-light .ant-menu-submenu-title:hover {
  background:
    radial-gradient(120% 140% at 0% 50%, rgba(34, 211, 238, 0.16) 0%, transparent 70%),
    linear-gradient(90deg, rgba(239, 246, 255, 0.96) 0%, rgba(219, 234, 254, 0.55) 100%) !important;
  color: #1d4ed8 !important;
  box-shadow:
    0 1px 0 rgba(59, 130, 246, 0.08) inset,
    0 10px 24px rgba(15, 23, 42, 0.06);
}

.app-shell-menu.ant-menu-light .ant-menu-item:hover .anticon,
.app-shell-menu.ant-menu-light .ant-menu-submenu-title:hover .anticon {
  transform: translateX(2px);
  transition: transform 0.25s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.app-shell-menu.ant-menu-light .ant-menu-item-selected {
  /* 深蓝高亮：强反差、很“实” */
  background:
    radial-gradient(120% 140% at 18% 0%, rgba(34, 211, 238, 0.22) 0%, transparent 58%),
    linear-gradient(135deg, #1E3A8A 0%, #1D4ED8 45%, #2563EB 100%) !important;
  color: #F8FAFF !important;
  box-shadow:
    0 0 0 1px rgba(34, 211, 238, 0.18) inset,
    0 14px 30px rgba(37, 99, 235, 0.18);
  position: relative;
  overflow: visible;
  font-weight: 600;
}

.app-shell-menu.ant-menu-light .ant-menu-item-selected::before {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 3px;
  height: 22px;
  border-radius: 0 4px 4px 0;
  background: linear-gradient(180deg, #67E8F9, #2563EB);
  box-shadow: 0 0 18px rgba(103, 232, 249, 0.55);
  animation: siderActiveBar 0.35s cubic-bezier(0.22, 1, 0.36, 1) both;
}

@keyframes siderActiveBar {
  from {
    opacity: 0;
    transform: translate3d(-4px, -50%, 0) scaleY(0.3);
  }
  to {
    opacity: 1;
    transform: translate3d(0, -50%, 0) scaleY(1);
  }
}

.app-shell-menu.ant-menu-light .ant-menu-submenu-arrow {
  color: #94a3b8 !important;
  transition: transform 0.28s ease, color 0.2s ease;
}
.app-shell-menu.ant-menu-light .ant-menu-submenu-open > .ant-menu-submenu-title .ant-menu-submenu-arrow {
  color: #2563eb !important;
  transform: translateY(1px);
}
.app-shell-menu.ant-menu-light .ant-menu-sub.ant-menu-inline {
  background: rgba(241, 245, 249, 0.65) !important;
  border-radius: 10px;
  margin: 2px 0 6px;
  padding: 4px 0 6px;
  border: 1px solid rgba(59, 130, 246, 0.1);
  box-shadow: 0 2px 8px rgba(15, 23, 42, 0.04) inset;
}

.app-shell-menu.ant-menu-light .ant-menu-sub.ant-menu-inline .ant-menu-item {
  border-radius: 8px;
  margin: 1px 6px !important;
  transition: background 0.2s ease;
}

.app-shell-menu.ant-menu-light .ant-menu-sub .ant-menu-item:hover a {
  display: inline-block;
  transform: translateX(3px);
  transition: transform 0.22s cubic-bezier(0.22, 1, 0.36, 1);
}

.app-shell-menu .ant-menu-item a,
.app-shell-menu .ant-menu-item span:not(.anticon) {
  color: inherit;
  transition: color 0.2s ease;
}

.app-shell-menu.ant-menu-light .ant-menu-item-selected a,
.app-shell-menu.ant-menu-light .ant-menu-item-selected span:not(.anticon) {
  color: #F8FAFF !important;
  font-weight: 600;
}

.app-shell-menu.ant-menu-light .ant-menu-item .anticon,
.app-shell-menu.ant-menu-light .ant-menu-submenu-title .anticon {
  color: #64748b;
  transition: transform 0.25s ease, color 0.2s ease;
}
.app-shell-menu.ant-menu-light .ant-menu-item:hover .anticon,
.app-shell-menu.ant-menu-light .ant-menu-submenu-title:hover .anticon {
  color: #2563eb;
}
.app-shell-menu.ant-menu-light .ant-menu-item-selected .anticon {
  color: #F8FAFF !important;
}

.app-shell-menu .ant-menu-item .anticon {
  font-size: 16px;
}

.sider-footer {
  flex-shrink: 0;
  margin: 8px 10px 64px;
  padding: 14px 14px 16px;
  border: 1px solid rgba(59, 130, 246, 0.12);
  border-radius: 14px;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.9) 0%, rgba(239, 246, 255, 0.6) 50%, rgba(224, 242, 254, 0.4) 100%);
  box-shadow: 0 4px 20px rgba(15, 23, 42, 0.06);
  position: relative;
  overflow: hidden;
  z-index: 1;
  animation: siderFooterIn 0.6s 0.15s cubic-bezier(0.22, 1, 0.36, 1) backwards;
}

.sider-footer::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(90deg, transparent, rgba(34, 211, 238, 0.45), #3b82f6, rgba(99, 102, 241, 0.5), transparent);
  background-size: 200% 100%;
  animation: siderFooterShimmer 8s ease-in-out infinite;
}

@keyframes siderFooterIn {
  from {
    opacity: 0;
    transform: translate3d(0, 12px, 0) scale(0.98);
  }
  to {
    opacity: 1;
    transform: translate3d(0, 0, 0) scale(1);
  }
}

@keyframes siderFooterShimmer {
  0%,
  100% {
    background-position: 0% 50%;
    opacity: 0.65;
  }
  50% {
    background-position: 100% 50%;
    opacity: 1;
  }
}

.sider-footer-label {
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.16em;
  color: #64748b;
  margin-bottom: 8px;
  font-weight: 700;
}

.sider-footer-dots {
  display: flex;
  gap: 6px;
  margin-bottom: 8px;
}

.sider-footer-dots .dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: rgba(148, 163, 184, 0.35);
}

.sider-footer-dots .dot.on {
  background: #22c55e;
  box-shadow: 0 0 10px rgba(34, 197, 94, 0.6);
}
.sider-footer-dots .dot.on + .dot.on {
  animation: none;
}

.sider-footer-dots .dot.pulse {
  background: #3b82f6;
  box-shadow: 0 0 12px rgba(59, 130, 246, 0.7);
  animation: zdDotPulse 1.8s ease-in-out infinite;
}

.sider-footer-text {
  font-size: 12px;
  color: #475569;
  line-height: 1.55;
  font-weight: 500;
}

@keyframes zdDotPulse {
  0%,
  100% {
    opacity: 1;
    transform: scale(1);
  }
  50% {
    opacity: 0.45;
    transform: scale(0.85);
  }
}

/* 收折：弱化装饰、保留结构 */
.app-shell-sider.ant-layout-sider-collapsed .sider-decor {
  opacity: 0.4;
  animation: none;
}
.app-shell-sider.ant-layout-sider-collapsed .logo::after {
  left: 8px;
  right: 8px;
}
.app-shell-sider.ant-layout-sider-collapsed .logo {
  justify-content: center;
  padding: 0 8px;
}

/* 系统「减少动效」 */
@media (prefers-reduced-motion: reduce) {
  .sider-decor,
  .sider-footer::before {
    animation: none;
  }
  .logo-mark,
  .sider-top,
  .sider-footer,
  .app-shell-menu > .ant-menu-item,
  .app-shell-menu > .ant-menu-submenu {
    animation: none;
  }
  .logo-ring,
  .sider-footer-dots .dot.pulse {
    animation: none;
  }
  .app-shell-menu.ant-menu-light .ant-menu-item-selected::before {
    animation: none;
  }
}

.app-main-layout {
  min-height: 100vh;
  height: 100vh;
  background: #DCE6F3;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  position: relative;
  z-index: 1;
}
/* 仪表盘页面：把滚动容器交给外层，让悬浮卡可以负 margin 上溢覆盖 Hero 头 */
.app-main-layout.is-hero-page {
  overflow-y: auto;
  overflow-x: hidden;
}

.header-glass {
  position: sticky;
  top: 0;
  z-index: 20;
  background-image:
    linear-gradient(135deg, rgba(10, 27, 54, 0.88) 0%, rgba(16, 38, 80, 0.86) 45%, rgba(21, 49, 99, 0.82) 100%),
    var(--zd-header-bg);
  background-size: cover;
  background-position: center;
  background-repeat: no-repeat;
  padding: 0 28px !important;
  height: auto !important;
  min-height: 96px;
  line-height: normal !important;
  border-bottom: none;
  box-shadow: 0 2px 12px rgba(10, 27, 54, 0.18);
  color: #ffffff;
}

/* 非 Hero 时把 topbar / 内容区压紧 */
.header-glass:not(.is-hero) .header-topbar {
  padding: 10px 0 4px;
}
.header-glass:not(.is-hero) .header-content {
  padding: 0 0 12px;
}
.header-glass:not(.is-hero) .page-heading {
  margin-top: 0;
  font-size: 18px;
}
.header-glass:not(.is-hero) .page-sub {
  margin-top: 2px;
}

.header-glass::before {
  content: '';
  position: absolute;
  inset: 0;
  pointer-events: none;
  background-image:
    linear-gradient(rgba(160, 185, 224, 0.05) 1px, transparent 1px),
    linear-gradient(90deg, rgba(160, 185, 224, 0.05) 1px, transparent 1px);
  background-size: 32px 32px;
  mask-image: radial-gradient(120% 80% at 70% 0%, #000 30%, transparent 80%);
  -webkit-mask-image: radial-gradient(120% 80% at 70% 0%, #000 30%, transparent 80%);
  opacity: 0.55;
}

.header-glass::after {
  content: '';
  position: absolute;
  right: -120px;
  top: -80px;
  width: 360px;
  height: 240px;
  border-radius: 50%;
  pointer-events: none;
  background: radial-gradient(circle, rgba(99, 130, 220, 0.32) 0%, rgba(11, 30, 64, 0) 70%);
  filter: blur(8px);
}

/* ========== Deep Hero（仅 Dashboard）========== */
.header-glass.is-hero {
  min-height: 260px;
  padding: 0 32px 92px !important;
  background-image:
    linear-gradient(135deg, rgba(10, 27, 54, 0.82) 0%, rgba(16, 38, 80, 0.78) 50%, rgba(21, 49, 99, 0.72) 100%),
    var(--zd-header-bg);
  background-size: cover;
  background-position: center;
  background-repeat: no-repeat;
  display: block;
  overflow: hidden;
}

.header-glass.is-hero::before {
  background-image:
    linear-gradient(rgba(160, 185, 224, 0.07) 1px, transparent 1px),
    linear-gradient(90deg, rgba(160, 185, 224, 0.07) 1px, transparent 1px);
  background-size: 36px 36px;
  mask-image: radial-gradient(140% 90% at 50% 30%, #000 30%, transparent 85%);
  -webkit-mask-image: radial-gradient(140% 90% at 50% 30%, #000 30%, transparent 85%);
  opacity: 0.7;
}

.header-glass.is-hero::after {
  right: -160px;
  top: -120px;
  width: 480px;
  height: 320px;
  background: radial-gradient(circle, rgba(96, 165, 250, 0.4) 0%, rgba(10, 27, 54, 0) 65%);
}

/* 顶部窄行：品牌名 + 时间 + 操作 + 头像 */
.header-topbar {
  position: relative;
  z-index: 3;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 20px;
  padding: 14px 0 6px;
}
.brand-block {
  display: flex;
  align-items: center;
  gap: 10px;
  color: rgba(255, 255, 255, 0.92);
}
.brand-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #22D3EE;
  box-shadow: 0 0 12px rgba(34, 211, 238, 0.85);
}
.brand-name {
  font-size: 13px;
  font-weight: 600;
  letter-spacing: 0.04em;
  color: #DBE7FF;
}
.topbar-right {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}
.now-time {
  font-family: ui-monospace, 'SFMono-Regular', Menlo, Consolas, 'Liberation Mono', monospace;
  font-size: 12px;
  font-weight: 500;
  color: #A0B9E0;
  letter-spacing: 0.04em;
  padding: 4px 10px;
  border-radius: 8px;
  background: rgba(160, 185, 224, 0.08);
  border: 1px solid rgba(160, 185, 224, 0.16);
}

/* Hero 中央区：标题居中 */
.header-glass.is-hero .header-content {
  flex-direction: column;
  justify-content: center;
  align-items: center;
  padding: 32px 0 0;
  text-align: center;
  position: relative;
  z-index: 3;
}
.header-glass.is-hero .header-left {
  padding-left: 0;
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
}
.header-glass.is-hero .header-left::before {
  display: none;
}
.header-glass.is-hero .page-heading {
  font-size: 30px;
  font-weight: 700;
  letter-spacing: 0.02em;
  margin-top: 4px;
  text-shadow: 0 4px 24px rgba(34, 211, 238, 0.25);
}
.header-glass.is-hero .page-sub {
  font-size: 13px;
  color: rgba(160, 185, 224, 0.85);
  margin-top: 6px;
}

/* 全球网络装饰 */
.hero-globe {
  position: absolute;
  left: 50%;
  top: 38%;
  width: 520px;
  height: 360px;
  transform: translate(-50%, -50%);
  opacity: 0.85;
  pointer-events: none;
  z-index: 1;
  filter: drop-shadow(0 0 30px rgba(34, 211, 238, 0.18));
}

/* 底部波浪：白色平滑过渡到下方主内容区 */
.hero-wave {
  position: absolute;
  left: 0;
  right: 0;
  bottom: -1px;
  width: 100%;
  height: 80px;
  z-index: 2;
  pointer-events: none;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 24px;
  padding: 6px 0 14px;
  flex-wrap: wrap;
  position: relative;
  z-index: 3;
}

.header-left {
  min-width: 0;
  position: relative;
  padding-left: 12px;
}

.header-left::before {
  content: '';
  position: absolute;
  left: 0;
  top: 4px;
  bottom: 4px;
  width: 3px;
  border-radius: 999px;
  background: linear-gradient(180deg, #60A5FA 0%, #22D3EE 100%);
  box-shadow: 0 0 12px rgba(96, 165, 250, 0.55);
}

.page-heading {
  margin: 6px 0 0;
  font-size: 22px;
  font-weight: 700;
  color: #ffffff;
  letter-spacing: -0.03em;
  line-height: 1.25;
}

.page-sub {
  margin: 4px 0 0;
  font-size: 13px;
  color: rgba(160, 185, 224, 0.85);
}

/* legacy fallback for non-hero pages where .header-right may still exist */
.header-right,
.topbar-right > .pill-group {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
  padding: 6px 10px;
  border-radius: 14px;
  border: 1px solid rgba(160, 185, 224, 0.18);
  background: rgba(255, 255, 255, 0.06);
  backdrop-filter: blur(10px);
  box-shadow: 0 1px 0 rgba(255, 255, 255, 0.08) inset;
}

.env-pill {
  font-size: 12px;
  font-weight: 600;
  color: #FCD34D;
  background: rgba(245, 158, 11, 0.16);
  border: 1px solid rgba(245, 158, 11, 0.32);
  padding: 4px 12px;
  border-radius: 999px;
  letter-spacing: 0.02em;
}

.env-pill--mode {
  color: #A0B9E0;
  background: rgba(96, 165, 250, 0.14);
  border-color: rgba(96, 165, 250, 0.32);
}
.env-pill--mode.is-push {
  color: #6EE7B7;
  background: rgba(16, 185, 129, 0.16);
  border-color: rgba(16, 185, 129, 0.36);
}
.env-pill--mode.is-poll {
  color: #FCD34D;
  background: rgba(245, 158, 11, 0.16);
  border-color: rgba(245, 158, 11, 0.36);
}
.env-pill--mode.is-idle {
  color: #CBD5E1;
  background: rgba(148, 163, 184, 0.16);
  border-color: rgba(148, 163, 184, 0.32);
}

.action-icon-wrap {
  width: 38px;
  height: 38px;
  border-radius: 10px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 17px;
  cursor: pointer;
  color: #A0B9E0;
  background: rgba(160, 185, 224, 0.08);
  border: 1px solid rgba(160, 185, 224, 0.18);
  transition: color 0.2s ease, background 0.2s ease, border-color 0.2s ease, transform 0.15s ease;
}

.action-icon-wrap:hover {
  color: #ffffff;
  background: rgba(96, 165, 250, 0.22);
  border-color: rgba(96, 165, 250, 0.5);
  transform: translateY(-1px);
}

.user-profile-link {
  text-decoration: none;
  color: inherit;
  margin-left: 4px;
  border-radius: 12px;
  outline: none;
}
.user-profile-link:hover .user-profile {
  border-color: rgba(96, 165, 250, 0.55);
  background: rgba(96, 165, 250, 0.16);
}
.user-profile-link:focus-visible .user-profile {
  box-shadow: 0 0 0 3px rgba(96, 165, 250, 0.32);
}

.user-profile {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 4px 8px 4px 4px;
  border-radius: 12px;
  border: 1px solid rgba(160, 185, 224, 0.22);
  background: rgba(160, 185, 224, 0.08);
  transition: border-color 0.2s ease, background 0.2s ease;
  cursor: pointer;
}

.user-avatar {
  background: linear-gradient(135deg, #60A5FA 0%, #3B82F6 100%) !important;
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.45);
}

.user-meta {
  display: flex;
  flex-direction: column;
  line-height: 1.25;
}

.username {
  font-size: 14px;
  font-weight: 600;
  color: #ffffff;
}

.user-role {
  font-size: 12px;
  color: rgba(160, 185, 224, 0.78);
}

.shell-content {
  margin: 0 !important;
  padding: 24px 28px;
  position: relative;
  flex: 1;
  min-height: 0;
  height: auto;
  overflow: auto;
  display: flex;
  flex-direction: column;
  background: #DCE6F3;
}
/* Dashboard：主内容区整体 z-index 高于同列 Header，使内联 KPI 能盖住 Hero 底边波浪（不依赖 Teleport） */
.app-main-layout.is-hero-page .header-glass {
  z-index: 1;
}
.shell-content.is-hero-page {
  overflow: visible;
  position: relative;
  z-index: 2;
  padding: 0 28px 24px;
  flex: 0 0 auto;
}

.shell-content::before,
.shell-content::after {
  display: none;
}

.content-inner {
  position: relative;
  z-index: 1;
  max-width: 1600px;
  margin: 0 auto;
  padding: 0;
  border-radius: 0;
  background: transparent;
  border: none;
  box-shadow: none;
  box-sizing: border-box;
  width: 100%;
}

/* 仅安全对话页：不叠一层白底卡片，由子页面自行铺卡片，外圈保留浅灰留白 */
.content-inner:has(.chat-page-root) {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  background: transparent;
  border: none;
  box-shadow: none;
  padding: 0;
}

.content-inner:has(.chat-page-root) .page-outlet {
  flex: 1 1 auto;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

@media (max-width: 768px) {
  .shell-content {
    padding: 16px 14px 20px;
  }
  .shell-content.is-hero-page {
    padding: 0 14px 20px;
  }
  .content-inner {
    padding: 0;
  }
  .page-heading {
    font-size: 18px;
  }
  .header-glass.is-hero {
    min-height: 220px;
    padding: 0 16px 80px !important;
  }
  .header-glass.is-hero .page-heading {
    font-size: 22px;
  }
  .hero-globe {
    width: 360px;
    height: 240px;
  }
  .topbar-right {
    gap: 6px;
  }
  .now-time {
    display: none;
  }
}

.page-fade-enter-active,
.page-fade-leave-active {
  transition: opacity 0.22s ease, transform 0.22s ease;
}

.page-fade-enter-from,
.page-fade-leave-to {
  opacity: 0;
  transform: translateY(6px);
}

.page-loading {
  min-height: 240px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.route-view-shell {
  width: 100%;
}
</style>
