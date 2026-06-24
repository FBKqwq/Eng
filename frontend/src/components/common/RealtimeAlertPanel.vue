<template>
  <div class="realtime-alert-panel">
    <div class="panel-header">
      <h3>🔔 实时告警</h3>
      <span class="alert-count">{{ alerts.length }}</span>
    </div>
    
    <div class="alert-list">
      <TransitionGroup name="alert">
        <div
          v-for="alert in alerts"
          :key="alert.id"
          :class="['alert-item', alert.level]"
          @click="handleAlertClick(alert)"
        >
          <div class="alert-icon">
            {{ getAlertIcon(alert.level) }}
          </div>
          <div class="alert-content">
            <div class="alert-title">{{ alert.type }}</div>
            <div class="alert-message">{{ alert.message }}</div>
            <div class="alert-meta">
              <span class="alert-service">{{ alert.service }}</span>
              <span class="alert-time">{{ formatTime(alert.timestamp) }}</span>
            </div>
          </div>
          <div class="alert-count-badge" v-if="alert.count > 1">
            ×{{ alert.count }}
          </div>
        </div>
      </TransitionGroup>
      
      <div v-if="alerts.length === 0" class="empty-state">
        <div class="empty-icon">✅</div>
        <p>暂无告警</p>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, onUnmounted } from 'vue'
import { websocketService } from '../../api/websocket'

export default {
  name: 'RealtimeAlertPanel',
  emits: ['alert-click'],
  setup(props, { emit }) {
    const alerts = ref([])
    const maxAlerts = 20

    const getAlertIcon = (level) => {
      switch (level) {
        case 'critical':
          return '🚨'
        case 'warning':
          return '⚠️'
        case 'info':
        default:
          return 'ℹ️'
      }
    }

    const formatTime = (timestamp) => {
      if (!timestamp) return ''
      const date = new Date(timestamp)
      return date.toLocaleString('zh-CN', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: false
      })
    }

    const addAlert = (data) => {
      if (data.type === 'alert' && data.data) {
        const existingIndex = alerts.value.findIndex(
          a => a.type === data.data.type && a.service === data.data.service
        )
        
        if (existingIndex >= 0) {
          alerts.value[existingIndex] = data.data
        } else {
          alerts.value.unshift(data.data)
        }
        
        if (alerts.value.length > maxAlerts) {
          alerts.value = alerts.value.slice(0, maxAlerts)
        }
      }
    }

    const handleAlertClick = (alert) => {
      emit('alert-click', alert)
    }

    onMounted(() => {
      websocketService.onAlert(addAlert)
    })

    onUnmounted(() => {
    })

    return {
      alerts,
      getAlertIcon,
      formatTime,
      handleAlertClick
    }
  }
}
</script>

<style scoped>
.realtime-alert-panel {
  background: white;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  height: 400px;
  display: flex;
  flex-direction: column;
}

.panel-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.panel-header h3 {
  margin: 0;
  font-size: 14px;
  color: white;
}

.alert-count {
  background: rgba(255, 255, 255, 0.2);
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 12px;
  color: white;
}

.alert-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.alert-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px;
  margin-bottom: 8px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.alert-item:hover {
  transform: translateX(4px);
}

.alert-item.critical {
  background: linear-gradient(135deg, #ff6b6b 0%, #ee5a5a 100%);
  border-left: 4px solid #c0392b;
}

.alert-item.warning {
  background: linear-gradient(135deg, #fdcb6e 0%, #f39c12 100%);
  border-left: 4px solid #d68910;
}

.alert-item.info {
  background: linear-gradient(135deg, #74b9ff 0%, #0984e3 100%);
  border-left: 4px solid #0652dd;
}

.alert-icon {
  font-size: 24px;
}

.alert-content {
  flex: 1;
  color: white;
}

.alert-title {
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 4px;
}

.alert-message {
  font-size: 13px;
  margin-bottom: 6px;
  opacity: 0.9;
}

.alert-meta {
  display: flex;
  gap: 12px;
  font-size: 12px;
  opacity: 0.8;
}

.alert-count-badge {
  background: rgba(255, 255, 255, 0.3);
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 12px;
  color: white;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #666;
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 12px;
}

.empty-state p {
  margin: 0;
}

/* 动画 */
.alert-enter-active {
  animation: slideIn 0.3s ease-out;
}

.alert-leave-active {
  animation: slideOut 0.2s ease-in;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateX(-20px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

@keyframes slideOut {
  from {
    opacity: 1;
    transform: translateX(0);
  }
  to {
    opacity: 0;
    transform: translateX(20px);
  }
}
</style>