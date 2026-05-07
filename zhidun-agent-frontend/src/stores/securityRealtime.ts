import { computed, ref } from 'vue';
import { defineStore } from 'pinia';
import {
  fetchDashboardOverview,
  fetchDashboardRealtimeSnapshot,
  fetchRiskMatrixSummary,
  getAuditEventDetail,
  listSecurityEvents,
  subscribeSecurityStream,
} from '@/api/services';
import { SECURITY_POLL_INTERVAL_MS, SECURITY_REALTIME_MODE } from '@/config/env';
import type {
  AuditEventDetail,
  DashboardOverview,
  RiskMatrixSummary,
  SecurityEventListItem,
  SecurityRealtimeEvent,
} from '@/types/api';

type RuntimeMode = 'push' | 'poll' | 'idle';

export const useSecurityRealtimeStore = defineStore('security-realtime', () => {
  const started = ref(false);
  const runtimeMode = ref<RuntimeMode>('idle');
  const coreLoading = ref(false);
  const matrixLoading = ref(false);
  const tableLoading = ref(false);

  const overview = ref<DashboardOverview | null>(null);
  const matrix = ref<RiskMatrixSummary | null>(null);
  const events = ref<SecurityEventListItem[]>([]);
  const eventsPage = ref(1);
  const eventsPageSize = ref(24);
  const eventsTotal = ref(0);

  const detailMap = ref<Record<string, AuditEventDetail>>({});
  const activeDetailId = ref<string | null>(null);
  const lastSyncAt = ref<string | null>(null);
  const lastError = ref<string | null>(null);

  let stopPush: (() => void) | null = null;
  let pollTimer: number | null = null;
  let autoFallbackTriggered = false;

  const statusText = computed(() => {
    if (!started.value) return '未启动';
    if (runtimeMode.value === 'push') return '实时联动：推送模式';
    if (runtimeMode.value === 'poll') return '实时联动：轮询模式';
    return '实时联动：空闲';
  });

  function markSynced() {
    lastSyncAt.value = new Date().toISOString();
    lastError.value = null;
  }

  function setError(message: string) {
    lastError.value = message;
  }

  async function loadCoreSnapshot(silent = false) {
    if (!silent) coreLoading.value = true;
    try {
      const [overviewRes, matrixRes] = await Promise.all([
        fetchDashboardOverview(),
        fetchRiskMatrixSummary(),
      ]);
      overview.value = overviewRes;
      matrix.value = matrixRes;
      await loadEvents(eventsPage.value, eventsPageSize.value, true);
      markSynced();
    } catch {
      setError('核心快照更新失败');
    } finally {
      if (!silent) coreLoading.value = false;
    }
  }

  async function loadMatrix(silent = false) {
    if (!silent) matrixLoading.value = true;
    try {
      matrix.value = await fetchRiskMatrixSummary();
      markSynced();
    } catch {
      setError('风险矩阵更新失败');
    } finally {
      if (!silent) matrixLoading.value = false;
    }
  }

  async function loadEvents(page = 1, pageSize = 10, silent = false) {
    if (!silent) tableLoading.value = true;
    try {
      const res = await listSecurityEvents({ page, pageSize });
      events.value = res.items;
      eventsPage.value = res.page;
      eventsPageSize.value = res.pageSize;
      eventsTotal.value = res.total;
      markSynced();
    } catch {
      setError('事件列表更新失败');
    } finally {
      if (!silent) tableLoading.value = false;
    }
  }

  async function loadDetail(eventId: string, silent = false) {
    if (!eventId) return null;
    try {
      const data = await getAuditEventDetail(eventId);
      detailMap.value = { ...detailMap.value, [eventId]: data };
      markSynced();
      return data;
    } catch {
      if (!silent) setError('事件详情更新失败');
      return null;
    }
  }

  async function refreshFromRealtimeSnapshot() {
    try {
      const snap = await fetchDashboardRealtimeSnapshot();
      overview.value = snap.overview;
      // latestEvents 优先用于首页“近期风险事件”展示
      if (snap.latestEvents?.length) {
        events.value = snap.latestEvents;
      }
      markSynced();
    } catch {
      // 快照接口不可用时，降级为常规刷新
      await loadCoreSnapshot(true);
    }
  }

  async function handleRealtimeEvent(evt: SecurityRealtimeEvent) {
    if (evt.type === 'dashboard.updated') {
      await refreshFromRealtimeSnapshot();
      return;
    }
    if (evt.type === 'event.created' || evt.type === 'event.updated') {
      await loadEvents(eventsPage.value, eventsPageSize.value, true);
      if (evt.eventId && activeDetailId.value === evt.eventId) {
        await loadDetail(evt.eventId, true);
      }
      return;
    }
    if (evt.type === 'audit.trace.appended') {
      if (evt.eventId && activeDetailId.value === evt.eventId) {
        await loadDetail(evt.eventId, true);
      }
      return;
    }
    if (evt.type === 'report.updated' && evt.eventId && activeDetailId.value === evt.eventId) {
      await loadDetail(evt.eventId, true);
    }
  }

  function clearSchedulers() {
    if (stopPush) {
      stopPush();
      stopPush = null;
    }
    if (pollTimer != null) {
      window.clearInterval(pollTimer);
      pollTimer = null;
    }
  }

  function startPolling() {
    clearSchedulers();
    runtimeMode.value = 'poll';
    pollTimer = window.setInterval(async () => {
      await Promise.all([
        refreshFromRealtimeSnapshot(),
        loadEvents(eventsPage.value, eventsPageSize.value, true),
        activeDetailId.value ? loadDetail(activeDetailId.value, true) : Promise.resolve(null),
      ]);
    }, Math.max(1500, SECURITY_POLL_INTERVAL_MS));
  }

  function startPush(preferAutoFallback: boolean) {
    clearSchedulers();
    runtimeMode.value = 'push';
    stopPush = subscribeSecurityStream(
      (evt) => {
        void handleRealtimeEvent(evt);
      },
      () => {
        setError('推送链路暂不可用');
        if (preferAutoFallback && !autoFallbackTriggered) {
          autoFallbackTriggered = true;
          startPolling();
        }
      }
    );
  }

  async function start() {
    if (started.value) return;
    started.value = true;
    autoFallbackTriggered = false;
    await loadCoreSnapshot();

    if (SECURITY_REALTIME_MODE === 'poll') {
      startPolling();
      return;
    }
    if (SECURITY_REALTIME_MODE === 'push') {
      startPush(false);
      return;
    }
    // auto
    startPush(true);
  }

  function stop() {
    clearSchedulers();
    runtimeMode.value = 'idle';
    started.value = false;
  }

  function setActiveDetail(eventId: string | null) {
    activeDetailId.value = eventId;
  }

  async function forceRefreshAll() {
    await loadCoreSnapshot(true);
    if (activeDetailId.value) await loadDetail(activeDetailId.value, true);
  }

  return {
    started,
    runtimeMode,
    statusText,
    coreLoading,
    matrixLoading,
    tableLoading,
    overview,
    matrix,
    events,
    eventsPage,
    eventsPageSize,
    eventsTotal,
    detailMap,
    activeDetailId,
    lastSyncAt,
    lastError,
    start,
    stop,
    setActiveDetail,
    loadEvents,
    loadMatrix,
    loadDetail,
    forceRefreshAll,
  };
});
