<template>
  <div class="diagnosis-page page-grid" style="grid-template-columns: 240px 1fr 220px; gap: 16px;">
    <DiagnosisEntryPanel />
    <div>
      <ConclusionPanel />
      <section class="page-section" style="margin-top: 16px;">
        <EvidenceTimeline />
        <ServiceTopology />
      </section>
    </div>
    <SuggestionChecklist />
  </div>
</template>

<script setup>
import DiagnosisEntryPanel from '../../components/analysis-diagnosis/DiagnosisEntryPanel.vue'
import ConclusionPanel from '../../components/analysis-diagnosis/ConclusionPanel.vue'
import EvidenceTimeline from '../../components/analysis-diagnosis/EvidenceTimeline.vue'
import ServiceTopology from '../../components/analysis-diagnosis/ServiceTopology.vue'
import SuggestionChecklist from '../../components/analysis-diagnosis/SuggestionChecklist.vue'
</script>
