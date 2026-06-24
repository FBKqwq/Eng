<template>
  <section class="particle-pipeline" aria-label="实时日志粒子管道">
    <div class="particle-pipeline__overlay">
      <div class="particle-pipeline__identity">
        <span class="particle-pipeline__pulse" />
        <strong>实时日志数据管道</strong>
        <span>INGEST → KAFKA → LOGSTASH → ELASTICSEARCH</span>
        <div class="particle-pipeline__legend" aria-label="日志粒子颜色图例">
          <span v-for="item in logLegend" :key="item.key">
            <i :style="{ backgroundColor: item.color }" />
            {{ item.label }}
          </span>
        </div>
      </div>
      <dl class="particle-pipeline__metrics">
        <div>
          <dt>窗口日志</dt>
          <dd>{{ formatNumber(totalLogs) }}</dd>
        </div>
        <div>
          <dt>平均流速</dt>
          <dd>{{ flowPercent }}%</dd>
        </div>
        <div>
          <dt>异常扰动</dt>
          <dd :class="{ danger: telemetry.anomalyRate > 0.35 }">{{ anomalyPercent }}%</dd>
        </div>
        <div>
          <dt>粒子加速度</dt>
          <dd>{{ accelerationPercent }}%</dd>
        </div>
        <div>
          <dt>健康稳定度</dt>
          <dd>{{ telemetry.healthScore }}</dd>
        </div>
      </dl>
    </div>
  </section>
</template>

<script setup>
import { computed } from 'vue'
import { formatNumber } from '../../utils/format.js'

const props = defineProps({
  telemetry: { type: Object, required: true },
  totalLogs: { type: Number, default: 0 }
})

const flowPercent = computed(() => Math.round(props.telemetry.flowRate * 100))
const anomalyPercent = computed(() => Math.round(props.telemetry.anomalyRate * 100))
const accelerationPercent = computed(() => Math.round(props.telemetry.acceleration * 100))

const logLegend = [
  { key: 'application', label: '应用', color: '#38bdf8' },
  { key: 'behavior', label: '行为', color: '#22d3ee' },
  { key: 'web_server', label: 'Web', color: '#818cf8' },
  { key: 'performance', label: '性能', color: '#34d399' },
  { key: 'security', label: '安全', color: '#fb7185' },
  { key: 'infrastructure', label: '设施', color: '#fbbf24' },
  { key: 'audit', label: '审计', color: '#c084fc' }
]
</script>

<style scoped>
.particle-pipeline {
  position: relative;
  height: 78px;
  overflow: hidden;
  border: 1px solid rgba(255, 255, 255, 0.86);
  border-radius: 18px;
  background: linear-gradient(115deg, rgba(255, 255, 255, 0.84), rgba(246, 250, 253, 0.62));
  box-shadow: 0 12px 32px rgba(40, 58, 78, 0.1), inset 0 1px rgba(255, 255, 255, 0.96);
  backdrop-filter: blur(28px) saturate(165%);
  -webkit-backdrop-filter: blur(28px) saturate(165%);
}

.particle-pipeline::before,
.particle-pipeline::after {
  position: absolute;
  z-index: 3;
  top: 0;
  width: 70px;
  height: 4px;
  background: #38bdf8;
  content: '';
}

.particle-pipeline::before { left: 0; }
.particle-pipeline::after { right: 0; background: #f97316; }

.particle-pipeline__overlay {
  position: relative;
  z-index: 2;
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 100%;
  padding: 12px 16px;
  pointer-events: none;
}

.particle-pipeline__identity {
  display: grid;
  grid-template-columns: auto auto;
  align-items: center;
  gap: 2px 8px;
  color: #172033;
}

.particle-pipeline__identity strong {
  font-size: 14px;
  letter-spacing: 0.08em;
}

.particle-pipeline__identity > span:last-child {
  grid-column: 2;
  color: #397497;
  font-family: var(--font-mono);
  font-size: 9px;
  letter-spacing: 0.08em;
}

.particle-pipeline__legend {
  grid-column: 2;
  display: flex;
  flex-wrap: wrap;
  gap: 2px 10px;
  margin-top: 3px;
  color: #64748b;
  font-size: 8px;
}

.particle-pipeline__legend span {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  white-space: nowrap;
}

.particle-pipeline__legend i {
  width: 9px;
  height: 2px;
  box-shadow: 0 0 7px currentColor;
}

.particle-pipeline__pulse {
  grid-row: 1 / 3;
  width: 9px;
  height: 9px;
  border-radius: 50%;
  background: #22d3ee;
  box-shadow: 0 0 0 5px rgba(34, 211, 238, 0.12), 0 0 18px #22d3ee;
}

.particle-pipeline__metrics {
  display: grid;
  grid-template-columns: repeat(5, minmax(76px, 1fr));
  margin: 0;
  border: 1px solid rgba(125, 211, 252, 0.22);
  overflow: hidden;
  border-color: rgba(148, 163, 184, 0.2);
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.52);
  backdrop-filter: blur(16px);
}

.particle-pipeline__metrics div {
  padding: 7px 11px;
  border-left: 1px solid rgba(148, 163, 184, 0.16);
}

.particle-pipeline__metrics div:first-child { border-left: 0; }
.particle-pipeline__metrics dt {
  color: #7a8797;
  font-size: 9px;
  white-space: nowrap;
}
.particle-pipeline__metrics dd {
  margin: 2px 0 0;
  color: #172033;
  font-family: var(--font-mono);
  font-size: 13px;
  font-weight: 900;
}
.particle-pipeline__metrics dd.danger { color: #fb7185; }

@media (max-width: 1050px) {
  .particle-pipeline__metrics div:nth-child(-n + 2) { display: none; }
}
</style>
