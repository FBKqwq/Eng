<template>
  <ul class="sidebar-tree">
    <SidebarTreeNode
      v-for="(item, index) in menuTree"
      :key="item.path || item.title"
      :item="item"
      :depth="0"
      :expanded-groups="expandedGroups"
      @toggle="toggleGroup"
    />
  </ul>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { menuTree } from '../menu.js'
import SidebarTreeNode from './SidebarTreeNode.vue'

const route = useRoute()
const expandedGroups = ref(new Set())

function collectParentGroups(items, targetPath, parents = []) {
  for (const item of items) {
    if (item.path === targetPath) return parents
    if (item.children) {
      const found = collectParentGroups(item.children, targetPath, [...parents, item.title])
      if (found) return found
    }
  }
  return null
}

function syncExpanded() {
  const parents = collectParentGroups(menuTree, route.path)
  if (parents) {
    parents.forEach((title) => expandedGroups.value.add(title))
  }
}

function toggleGroup(title) {
  if (expandedGroups.value.has(title)) {
    expandedGroups.value.delete(title)
  } else {
    expandedGroups.value.add(title)
  }
  expandedGroups.value = new Set(expandedGroups.value)
}

watch(() => route.path, syncExpanded, { immediate: true })
</script>

<style scoped>
.sidebar-tree {
  list-style: none;
  margin: 0;
  padding: 0;
}
</style>
