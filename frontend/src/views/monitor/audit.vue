<template>
  <LogMonitorShell :meta="meta" />
</template>

<script setup>
import LogMonitorShell from '../../components/monitor/LogMonitorShell.vue'
import { getLogTypeMeta } from '../../utils/logTypeMeta.js'

const meta = getLogTypeMeta('audit')
</script>
