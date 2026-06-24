<template>
  <div class="dashboard-screen">
    <DashboardWebGLFlow
      :telemetry="particleTelemetry"
      :sources="logSources.data.value?.buckets || []"
    />

    <div class="dashboard-screen__content">
      <DashboardParticlePipeline
        :telemetry="particleTelemetry"
        :total-logs="totalLogs"
      />

      <div class="dashboard-screen__top">
        <DashboardHealthPanel
          :health-score="healthScore"
          :total-logs="totalLogs"
          :error-rate="errorRate"
          :average-latency="averageLatency"
          :p95-latency="p95Latency"
          :alert-total="alertTotal"
          :loading="loading"
        />
        <DashboardReportPanel :report="latestReport" />
      </div>

      <div class="dashboard-screen__middle">
        <DashboardTrafficPanel
          :traffic-buckets="traffic.data.value?.buckets"
          :error-buckets="errorTrend.data.value?.buckets"
          :loading="traffic.loading.value || errorTrend.loading.value"
        />
        <DashboardAlertTable :alerts="alerts" :total="alertTotal" />
      </div>

      <div class="dashboard-screen__bottom">
        <div class="dashboard-screen__analytics">
          <div class="dashboard-screen__errors">
            <DashboardErrorServices :buckets="errorDistribution.data.value?.extra?.by_service || []" />
            <DashboardErrorCodes :buckets="errorDistribution.data.value?.buckets || []" />
          </div>
          <DashboardLatencyPanel
            :buckets="latency.data.value?.buckets || []"
            :loading="latency.loading.value"
          />
        </div>
        <DashboardSourceStatus :buckets="logSources.data.value?.buckets || []" />
      </div>
    </div>
  </div>
</template>

<script setup>
import DashboardWebGLFlow from '../../components/dashboard/DashboardWebGLFlow.vue'
import DashboardParticlePipeline from '../../components/dashboard/DashboardParticlePipeline.vue'
import DashboardHealthPanel from '../../components/dashboard/DashboardHealthPanel.vue'
import DashboardReportPanel from '../../components/dashboard/DashboardReportPanel.vue'
import DashboardTrafficPanel from '../../components/dashboard/DashboardTrafficPanel.vue'
import DashboardAlertTable from '../../components/dashboard/DashboardAlertTable.vue'
import DashboardErrorServices from '../../components/dashboard/DashboardErrorServices.vue'
import DashboardErrorCodes from '../../components/dashboard/DashboardErrorCodes.vue'
import DashboardLatencyPanel from '../../components/dashboard/DashboardLatencyPanel.vue'
import DashboardSourceStatus from '../../components/dashboard/DashboardSourceStatus.vue'
import { useDashboardData } from '../../components/dashboard/useDashboardData.js'
import '../../components/dashboard/dashboard-screen.css'

const {
  traffic,
  errorTrend,
  errorDistribution,
  latency,
  logSources,
  alerts,
  alertTotal,
  latestReport,
  totalLogs,
  errorRate,
  averageLatency,
  p95Latency,
  healthScore,
  particleTelemetry,
  loading
} = useDashboardData()
</script>
