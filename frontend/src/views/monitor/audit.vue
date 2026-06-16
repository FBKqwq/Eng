<template>
  <LogMonitorShell
    :log-type="meta.logType"
    :chart-templates="meta.chartTemplates"
    :default-columns="meta.defaultColumns"
  />
</template>

<script setup>
import LogMonitorShell from '../../components/monitor/LogMonitorShell.vue'
import { getLogTypeMeta } from '../../utils/logTypeMeta.js'

const meta = getLogTypeMeta('audit')
</script>
