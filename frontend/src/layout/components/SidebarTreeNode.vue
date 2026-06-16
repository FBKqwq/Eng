<template>
  <li class="tree-node" :class="{ 'is-group': hasChildren }">
    <div
      v-if="hasChildren"
      class="group-header"
      :style="{ paddingLeft: `${12 + depth * 16}px` }"
      @click="$emit('toggle', item.title)"
    >
      <span class="chevron" :class="{ expanded: isExpanded }">▸</span>
      <span class="title">{{ item.title }}</span>
    </div>
    <router-link
      v-else
      :to="item.path"
      class="leaf-link"
      :class="{ active: isActive }"
      :style="{ paddingLeft: `${12 + depth * 16}px` }"
    >
      {{ item.title }}
    </router-link>
    <ul v-if="hasChildren && isExpanded" class="children">
      <SidebarTreeNode
        v-for="child in item.children"
        :key="child.path"
        :item="child"
        :depth="depth + 1"
        :expanded-groups="expandedGroups"
        @toggle="$emit('toggle', $event)"
      />
    </ul>
  </li>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import SidebarTreeNode from './SidebarTreeNode.vue'

const props = defineProps({
  item: { type: Object, required: true },
  depth: { type: Number, default: 0 },
  expandedGroups: { type: Set, required: true }
})

defineEmits(['toggle'])

const route = useRoute()
const hasChildren = computed(() => Array.isArray(props.item.children) && props.item.children.length > 0)
const isExpanded = computed(() => props.expandedGroups.has(props.item.title))
const isActive = computed(() => props.item.path === route.path)
</script>

<style scoped>
.tree-node {
  list-style: none;
}
.group-header {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  cursor: pointer;
  color: var(--color-sidebar-text);
  font-size: 14px;
  user-select: none;
}
.group-header:hover {
  background: var(--color-sidebar-hover);
}
.chevron {
  display: inline-block;
  transition: transform 0.15s;
  font-size: 10px;
}
.chevron.expanded {
  transform: rotate(90deg);
}
.leaf-link {
  display: block;
  padding: 8px 12px;
  color: var(--color-sidebar-text-muted);
  font-size: 13px;
  border-left: 3px solid transparent;
}
.leaf-link:hover {
  background: var(--color-sidebar-hover);
  color: var(--color-sidebar-text);
}
.leaf-link.active {
  color: #fff;
  background: var(--color-sidebar-active);
  border-left-color: var(--color-primary);
  font-weight: 600;
}
.children {
  list-style: none;
  margin: 0;
  padding: 0;
}
</style>
