<template>
  <ul class="sidebar-tree" role="tree">
    <SidebarTreeNode
      v-for="item in menuTree"
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

/** 已展开的分组标题集合（组件内交互状态，不持久化） */
const expandedGroups = ref(new Set())

/**
 * 在 menuTree 中查找目标 path 对应叶子的所有父分组标题
 * @returns {string[] | null} 父级标题链，未命中返回 null
 */
function collectParentGroups(items, targetPath, parents = []) {
  for (const item of items) {
    if (item.path === targetPath) return parents
    if (item.children?.length) {
      const found = collectParentGroups(item.children, targetPath, [...parents, item.title])
      if (found) return found
    }
  }
  return null
}

/** 路由变化时自动展开命中叶子的父分组 */
function syncExpanded() {
  const parents = collectParentGroups(menuTree, route.path)
  if (!parents?.length) return

  const next = new Set(expandedGroups.value)
  parents.forEach((title) => next.add(title))
  expandedGroups.value = next
}

/** 手动折叠/展开分组 */
function toggleGroup(title) {
  const next = new Set(expandedGroups.value)
  if (next.has(title)) {
    next.delete(title)
  } else {
    next.add(title)
  }
  expandedGroups.value = next
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
