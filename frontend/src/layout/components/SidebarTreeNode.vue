<template>
  <li class="tree-node" :class="{ 'is-group': hasChildren }" role="treeitem" :aria-expanded="hasChildren ? isExpanded : undefined">
    <!-- 分组节点：仅折叠/展开，不可路由 -->
    <div
      v-if="hasChildren"
      class="group-header"
      :style="{ paddingLeft: `${12 + depth * 16}px` }"
      role="button"
      tabindex="0"
      :aria-expanded="isExpanded"
      @click="emitToggle"
      @keydown.enter.prevent="emitToggle"
      @keydown.space.prevent="emitToggle"
    >
      <span class="chevron" :class="{ expanded: isExpanded }" aria-hidden="true">▸</span>
      <span class="title">{{ item.title }}</span>
    </div>
    <!-- 叶子节点：router-link 跳转 -->
    <router-link
      v-else
      :to="item.path"
      class="leaf-link"
      :class="{ active: isActive }"
      :style="{ paddingLeft: `${12 + depth * 16}px` }"
    >
      {{ item.title }}
    </router-link>
    <ul v-if="hasChildren && isExpanded" class="children" role="group">
      <SidebarTreeNode
        v-for="child in item.children"
        :key="child.path || child.title"
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

const emit = defineEmits(['toggle'])

const route = useRoute()

const hasChildren = computed(() => Array.isArray(props.item.children) && props.item.children.length > 0)
const isExpanded = computed(() => props.expandedGroups.has(props.item.title))
const isActive = computed(() => props.item.path === route.path)

function emitToggle() {
  emit('toggle', props.item.title)
}
</script>

<style scoped>
.tree-node {
  list-style: none;
}

.group-header {
  display: flex;
  align-items: center;
  gap: 6px;
  margin: 2px 8px;
  padding: 8px 10px;
  border-radius: var(--radius-sm);
  cursor: pointer;
  color: var(--color-sidebar-text);
  font-size: 14px;
  font-weight: 700;
  user-select: none;
  transition:
    background var(--transition-fast),
    color var(--transition-fast);
}

.group-header:hover {
  background: var(--color-sidebar-hover);
}

.chevron {
  display: inline-block;
  transition: transform 0.15s ease-out;
  font-size: 10px;
}

.chevron.expanded {
  transform: rotate(90deg);
}

.leaf-link {
  display: block;
  margin: 2px 8px;
  padding: 8px 10px;
  border-radius: var(--radius-sm);
  color: var(--color-sidebar-text-muted);
  font-size: 13px;
  border: 1px solid transparent;
  text-decoration: none;
  transition:
    background var(--transition-fast),
    color var(--transition-fast),
    border-color var(--transition-fast);
}

.leaf-link:hover {
  background: var(--color-sidebar-hover);
  color: var(--color-sidebar-text);
}

.leaf-link.active {
  color: #fff;
  background:
    linear-gradient(90deg, rgba(37, 99, 235, 0.32), rgba(8, 145, 178, 0.16)),
    var(--color-sidebar-active);
  border-color: rgba(96, 165, 250, 0.4);
  font-weight: 600;
}

.children {
  list-style: none;
  margin: 0;
  padding: 0;
}

@media (prefers-reduced-motion: reduce) {
  .chevron,
  .leaf-link {
    transition: none;
  }
}
</style>
