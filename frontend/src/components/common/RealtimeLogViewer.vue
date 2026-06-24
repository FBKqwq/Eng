<template>
  <div class="realtime-log-viewer">
    <div class="viewer-header">
      <h3>📜 实时日志流</h3>
      <div class="header-actions">
        <span class="status-indicator" :class="{ connected: isConnected }">
          {{ isConnected ? '🟢 已连接' : '🔴 已断开' }}
        </span>
        <button class="clear-btn" @click="clearLogs">清空</button>
      </div>
    </div>
    
    <div class="log-container" ref="logContainer">
      <div
        v-for="log in logs"
        :key="log.id"
        :class="['log-item', log.level.toLowerCase()]"
      >
        <span class="log-time">{{ formatTime(log.timestamp) }}</span>
        <span class="log-level" :class="log.level.toLowerCase()">
          [{{ log.level }}]
        </span>
        <span class="log-source">{{ log.source }}</span>
        <span class="log-message">{{ log.message }}</span>
      </div>
      
      <div v-if="logs.length === 0" class="empty-state">
        等待接收日志...
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, onUnmounted } from 'vue'
import { websocketService } from '../../api/websocket'

export default {
  name: 'RealtimeLogViewer',
  setup() {
    const logs = ref([])
    const isConnected = ref(false)
    const logContainer = ref(null)
    const maxLogs = 100

    const formatTime = (timestamp) => {
      if (!timestamp) return ''
      const date = new Date(timestamp)
      return date.toLocaleTimeString('zh-CN', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: false
      })
    }

    const addLog = (data) => {
      if (data.type === 'log' && data.data) {
        logs.value.unshift(data.data)
        
        if (logs.value.length > maxLogs) {
          logs.value = logs.value.slice(0, maxLogs)
        }

        // 自动滚动到底部
        setTimeout(() => {
          if (logContainer.value) {
            logContainer.value.scrollTop = 0
          }
        }, 10)
      }
    }

    const clearLogs = () => {
      logs.value = []
    }

    onMounted(() => {
      isConnected.value = true
      websocketService.onLog(addLog)
    })

    onUnmounted(() => {
      isConnected.value = false
    })

    return {
      logs,
      isConnected,
      logContainer,
      formatTime,
      clearLogs
    }
  }
}
</script>

<style scoped>
.realtime-log-viewer {
  background: #1a1a2e;
  border-radius: 8px;
  overflow: hidden;
  height: 400px;
  display: flex;
  flex-direction: column;
}

.viewer-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: #16213e;
  border-bottom: 1px solid #0f3460;
}

.viewer-header h3 {
  margin: 0;
  font-size: 14px;
  color: #e9ecef;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.status-indicator {
  font-size: 12px;
  padding: 4px 8px;
  border-radius: 4px;
  background: #dc3545;
  color: white;
}

.status-indicator.connected {
  background: #28a745;
}

.clear-btn {
  padding: 4px 10px;
  background: #495057;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
}

.clear-btn:hover {
  background: #6c757d;
}

.log-container {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
}

.log-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 8px 0;
  border-bottom: 1px solid #2d3436;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 13px;
}

.log-time {
  color: #636e72;
  min-width: 70px;
}

.log-level {
  min-width: 60px;
  font-weight: 600;
}

.log-level.info {
  color: #0984e3;
}

.log-level.warn {
  color: #fdcb6e;
}

.log-level.error {
  color: #ff6b6b;
}

.log-level.debug {
  color: #a29bfe;
}

.log-source {
  color: #00b894;
  min-width: 120px;
}

.log-message {
  color: #e9ecef;
  flex: 1;
}

.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #636e72;
}

.log-container::-webkit-scrollbar {
  width: 6px;
}

.log-container::-webkit-scrollbar-track {
  background: #16213e;
}

.log-container::-webkit-scrollbar-thumb {
  background: #4a69bd;
  border-radius: 3px;
}
</style>