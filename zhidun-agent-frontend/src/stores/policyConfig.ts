import { computed, ref } from 'vue';
import { defineStore } from 'pinia';

/**
 * 全局策略阈值与权重 store
 * 跨页共享：风险评分 R 的阈值 T1/T2、规则/语义/上下文/资源四维权重、风险主题色等
 * 由「策略编排」修改，可在 ChatHall / Tool 监控 / 策略沙箱 中读取
 */
export type RiskBand = 'low' | 'mid' | 'high';

export interface RiskWeights {
  rule: number;
  cls: number;
  ctx: number;
  res: number;
}

export const useRiskPolicyStore = defineStore('risk-policy', () => {
  const t1 = ref<number>(40);
  const t2 = ref<number>(70);
  const weights = ref<RiskWeights>({ rule: 0.3, cls: 0.3, ctx: 0.2, res: 0.2 });
  const lastUpdatedAt = ref<string | null>(null);

  /** 设置阈值，自动校验 0 ≤ T1 ≤ T2 ≤ 100 */
  function setThresholds(next: { t1: number; t2: number }) {
    const a = Math.max(0, Math.min(100, next.t1));
    const b = Math.max(a, Math.min(100, next.t2));
    t1.value = a;
    t2.value = b;
    lastUpdatedAt.value = new Date().toISOString();
  }

  function setWeights(next: Partial<RiskWeights>) {
    weights.value = { ...weights.value, ...next };
    lastUpdatedAt.value = new Date().toISOString();
  }

  function classify(r: number | null | undefined): RiskBand {
    const v = Number(r ?? 0);
    if (v >= t2.value) return 'high';
    if (v >= t1.value) return 'mid';
    return 'low';
  }

  const tone = computed(() => ({
    low: '#10B981',
    mid: '#F59E0B',
    high: '#F43F5E',
  }));

  return {
    t1,
    t2,
    weights,
    lastUpdatedAt,
    tone,
    setThresholds,
    setWeights,
    classify,
  };
});
