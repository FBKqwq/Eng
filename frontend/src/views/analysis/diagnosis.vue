<template>
  <div class="diagnosis-page">
    <aside class="diagnosis-page__entry">
      <DiagnosisEntryPanel />
    </aside>
    <main class="diagnosis-page__main">
      <section class="page-section">
        <h2>结论区</h2>
        <ConclusionPanel />
      </section>
      <section class="page-section">
        <h2>证据区</h2>
        <div class="evidence-grid">
          <EvidenceTimeline />
          <ServiceTopology />
        </div>
      </section>
    </main>
    <aside class="diagnosis-page__aside">
      <SuggestionChecklist />
    </aside>
  </div>
</template>

<script setup>
import DiagnosisEntryPanel from '../../components/analysis-diagnosis/DiagnosisEntryPanel.vue'
import ConclusionPanel from '../../components/analysis-diagnosis/ConclusionPanel.vue'
import EvidenceTimeline from '../../components/analysis-diagnosis/EvidenceTimeline.vue'
import ServiceTopology from '../../components/analysis-diagnosis/ServiceTopology.vue'
import SuggestionChecklist from '../../components/analysis-diagnosis/SuggestionChecklist.vue'
</script>

<style scoped>
.diagnosis-page {
  display: grid;
  grid-template-columns: 240px 1fr 220px;
  gap: var(--spacing-md);
  align-items: start;
}

.diagnosis-page__main {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.diagnosis-page__main .page-section {
  margin-bottom: 0;
}

.evidence-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--spacing-md);
}

@media (max-width: 1200px) {
  .diagnosis-page {
    grid-template-columns: 1fr;
  }

  .evidence-grid {
    grid-template-columns: 1fr;
  }
}
</style>
