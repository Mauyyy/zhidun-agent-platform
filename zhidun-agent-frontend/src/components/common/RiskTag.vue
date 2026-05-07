<template>
  <a-tag :color="color" class="risk-tag">
    <span class="dot" :style="{ background: hex }" />
    <span class="label">{{ labelText }}</span>
    <span v-if="showScore && score != null" class="score">R={{ score }}</span>
  </a-tag>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useRiskPolicyStore, type RiskBand } from '@/stores/policyConfig';

const props = withDefaults(
  defineProps<{
    /** 综合风险 R, 0–100 */
    score?: number | null;
    /** 显式指定风险段，否则按 store 阈值自动判定 */
    band?: RiskBand;
    /** 自定义文案，否则用「低/中/高 风险」 */
    label?: string;
    showScore?: boolean;
  }>(),
  { showScore: true }
);

const policy = useRiskPolicyStore();

const computedBand = computed<RiskBand>(() => {
  if (props.band) return props.band;
  return policy.classify(props.score ?? 0);
});

const color = computed(() => {
  if (computedBand.value === 'high') return 'red';
  if (computedBand.value === 'mid') return 'orange';
  return 'green';
});

const hex = computed(() => policy.tone[computedBand.value]);

const labelText = computed(() => {
  if (props.label) return props.label;
  return computedBand.value === 'high' ? '高风险' : computedBand.value === 'mid' ? '中风险' : '低风险';
});
</script>

<style scoped>
.risk-tag {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  border-radius: 999px;
  padding: 2px 10px;
}
.dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  display: inline-block;
}
.score {
  font-family: 'SFMono-Regular', Consolas, Menlo, monospace;
  font-weight: 600;
  margin-left: 4px;
  opacity: 0.85;
}
</style>
