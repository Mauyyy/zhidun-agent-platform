import { ref } from 'vue';
import { defineStore } from 'pinia';

/**
 * 跨页审阅上下文：
 * 任一页面（Dashboard 告警、ChatHall、ToolMonitor、Reports）可设置当前事件 ID，
 * 通过 EvidenceDrawer 立即查看证据链而不离开当前页。
 */
export const useAuditSessionStore = defineStore('audit-session', () => {
  const drawerOpen = ref(false);
  const currentEventId = ref<string | null>(null);
  const currentSessionId = ref<string | null>(null);

  function openEvent(eventId: string) {
    currentEventId.value = eventId;
    drawerOpen.value = true;
  }

  function closeDrawer() {
    drawerOpen.value = false;
  }

  function selectSession(sessionId: string | null) {
    currentSessionId.value = sessionId;
  }

  return {
    drawerOpen,
    currentEventId,
    currentSessionId,
    openEvent,
    closeDrawer,
    selectSession,
  };
});
