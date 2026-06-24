<template>
  <div class="time-range-picker">
    <div class="preset-buttons">
      <button
        v-for="preset in presets"
        :key="preset.value"
        :class="['preset-btn', { active: selectedPreset === preset.value }]"
        @click="selectPreset(preset.value)"
      >
        {{ preset.label }}
      </button>
    </div>
    
    <div class="custom-range" v-if="selectedPreset === 'custom'">
      <div class="time-input-group">
        <label>开始时间</label>
        <input
          type="datetime-local"
          v-model="startTime"
          @change="applyCustomRange"
        />
      </div>
      <span class="separator">→</span>
      <div class="time-input-group">
        <label>结束时间</label>
        <input
          type="datetime-local"
          v-model="endTime"
          @change="applyCustomRange"
        />
      </div>
      <button class="apply-btn" @click="applyCustomRange">应用</button>
    </div>

    <div class="quick-actions">
      <button class="action-btn" @click="refreshData">
        🔄 刷新
      </button>
      <button class="action-btn" @click="toggleAutoRefresh">
        {{ autoRefresh ? '⏸️ 暂停' : '⏯️ 自动刷新' }}
      </button>
    </div>
  </div>
</template>

<script>
import { ref, watch, onMounted, onUnmounted } from 'vue'

export default {
  name: 'TimeRangePicker',
  emits: ['change', 'refresh'],
  props: {
    modelValue: {
      type: Object,
      default: () => ({
        preset: '1h',
        start: null,
        end: null
      })
    },
    autoRefreshInterval: {
      type: Number,
      default: 10000
    }
  },
  setup(props, { emit }) {
    const presets = [
      { label: '5分钟', value: '5m' },
      { label: '15分钟', value: '15m' },
      { label: '1小时', value: '1h' },
      { label: '6小时', value: '6h' },
      { label: '24小时', value: '24h' },
      { label: '7天', value: '7d' },
      { label: '自定义', value: 'custom' }
    ]

    const selectedPreset = ref(props.modelValue.preset || '1h')
    const startTime = ref('')
    const endTime = ref('')
    const autoRefresh = ref(false)
    let refreshTimer = null

    const calculateRange = (preset) => {
      const now = new Date()
      let start = new Date()

      switch (preset) {
        case '5m':
          start.setMinutes(now.getMinutes() - 5)
          break
        case '15m':
          start.setMinutes(now.getMinutes() - 15)
          break
        case '1h':
          start.setHours(now.getHours() - 1)
          break
        case '6h':
          start.setHours(now.getHours() - 6)
          break
        case '24h':
          start.setDate(now.getDate() - 1)
          break
        case '7d':
          start.setDate(now.getDate() - 7)
          break
      }

      return {
        start: start.toISOString(),
        end: now.toISOString(),
        preset: preset
      }
    }

    const selectPreset = (preset) => {
      selectedPreset.value = preset
      
      if (preset !== 'custom') {
        const range = calculateRange(preset)
        emit('change', range)
      }
    }

    const applyCustomRange = () => {
      if (startTime.value && endTime.value) {
        emit('change', {
          start: new Date(startTime.value).toISOString(),
          end: new Date(endTime.value).toISOString(),
          preset: 'custom'
        })
      }
    }

    const refreshData = () => {
      emit('refresh')
    }

    const toggleAutoRefresh = () => {
      autoRefresh.value = !autoRefresh.value
      
      if (autoRefresh.value) {
        startAutoRefresh()
      } else {
        stopAutoRefresh()
      }
    }

    const startAutoRefresh = () => {
      if (refreshTimer) return
      refreshTimer = setInterval(() => {
        emit('refresh')
      }, props.autoRefreshInterval)
    }

    const stopAutoRefresh = () => {
      if (refreshTimer) {
        clearInterval(refreshTimer)
        refreshTimer = null
      }
    }

    watch(() => props.modelValue, (newVal) => {
      if (newVal) {
        selectedPreset.value = newVal.preset || '1h'
      }
    }, { deep: true })

    onMounted(() => {
      if (props.modelValue.preset) {
        selectedPreset.value = props.modelValue.preset
      }
    })

    onUnmounted(() => {
      stopAutoRefresh()
    })

    return {
      presets,
      selectedPreset,
      startTime,
      endTime,
      autoRefresh,
      selectPreset,
      applyCustomRange,
      refreshData,
      toggleAutoRefresh
    }
  }
}
</script>

<style scoped>
.time-range-picker {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 12px;
  padding: 16px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.preset-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.preset-btn {
  padding: 8px 16px;
  border: 1px solid #e9ecef;
  border-radius: 6px;
  background: white;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.preset-btn:hover {
  border-color: #667eea;
  color: #667eea;
}

.preset-btn.active {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-color: #667eea;
  color: white;
}

.custom-range {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 12px;
  background: #f8f9fa;
  border-radius: 6px;
}

.time-input-group {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.time-input-group label {
  font-size: 12px;
  color: #666;
}

.time-input-group input {
  padding: 6px 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}

.separator {
  font-size: 18px;
  color: #999;
}

.apply-btn {
  padding: 6px 12px;
  background: #667eea;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 14px;
  cursor: pointer;
}

.apply-btn:hover {
  background: #5a6fd6;
}

.quick-actions {
  display: flex;
  gap: 8px;
  margin-left: auto;
}

.action-btn {
  padding: 8px 12px;
  border: 1px solid #e9ecef;
  border-radius: 6px;
  background: white;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.action-btn:hover {
  background: #f8f9fa;
  border-color: #667eea;
}
</style>