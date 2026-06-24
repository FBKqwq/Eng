import { computed, reactive } from 'vue'

const headerState = reactive({
  source: null,
  active: false,
  title: '',
  eyebrow: '',
  subtitle: '',
  tone: 'blue'
})

export function usePageHeader() {
  const pageHeader = computed(() => ({
    active: headerState.active,
    title: headerState.title,
    eyebrow: headerState.eyebrow,
    subtitle: headerState.subtitle,
    tone: headerState.tone
  }))

  function setPageHeader(source, nextHeader) {
    headerState.source = source
    headerState.active = true
    headerState.title = nextHeader.title || ''
    headerState.eyebrow = nextHeader.eyebrow || ''
    headerState.subtitle = nextHeader.subtitle || ''
    headerState.tone = nextHeader.tone || 'blue'
  }

  function clearPageHeader(source) {
    if (source && headerState.source !== source) return
    headerState.source = null
    headerState.active = false
    headerState.title = ''
    headerState.eyebrow = ''
    headerState.subtitle = ''
    headerState.tone = 'blue'
  }

  return {
    pageHeader,
    setPageHeader,
    clearPageHeader
  }
}
