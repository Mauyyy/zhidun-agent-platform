<template>
  <div class="threshold-panel">
    <div class="row">
      <span class="lbl">综合评分阈值</span>
      <span class="val">T1={{ t1 }} · T2={{ t2 }}</span>
    </div>
    <a-slider
      :value="range"
      range
      :min="0"
      :max="100"
      :marks="{ 0: '0', 50: '50', 100: '100' }"
      @change="onChange"
    />
    <div class="hint">小于 T1 放行；T1—T2 之间二次确认；超过 T2 阻断。</div>
    <div v-if="lastUpdatedAt" class="hint mini">最近调整：{{ lastUpdatedAt }}</div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { storeToRefs } from 'pinia';
import { useRiskPolicyStore } from '@/stores/policyConfig';

const policy = useRiskPolicyStore();
const { t1, t2, lastUpdatedAt } = storeToRefs(policy);

const range = computed<[number, number]>(() => [t1.value, t2.value]);

function onChange(v: number | [number, number]) {
  if (!Array.isArray(v)) return;
  policy.setThresholds({ t1: v[0], t2: v[1] });
}
</script>

<style scoped>
.threshold-panel {
  margin-top: 14px;
  padding: 14px;
  border-radius: 10px;
  background: rgba(238, 242, 255, 0.55);
  border: 1px solid rgba(99, 102, 241, 0.18);
}
.row {
  display: flex;
  justify-content: space-between;
  margin-bottom: 4px;
  font-size: 12px;
}
.lbl {
  color: #475569;
  font-weight: 500;
}
.val {
  font-weight: 600;
  color: #4338CA;
  font-family: 'SFMono-Regular', Consolas, monospace;
}
.hint {
  font-size: 11.5px;
  color: #64748B;
  margin-top: 6px;
}
.hint.mini {
  font-size: 10.5px;
  opacity: 0.8;
  color: #94A3B8;
}
.threshold-panel :deep(.ant-slider-track) {
  background: linear-gradient(90deg, #10B981 0%, #F59E0B 50%, #F43F5E 100%) !important;
}
.threshold-panel :deep(.ant-slider-handle::after) {
  box-shadow: 0 0 0 2px #6366F1, 0 4px 8px rgba(99, 102, 241, 0.32) !important;
}
</style>
