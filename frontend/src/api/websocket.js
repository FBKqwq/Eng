/**
 * WebSocket 服务模块
 * 提供实时数据推送功能
 */

class WebSocketService {
  constructor() {
    this.connections = {}
    this.callbacks = {}
    this.reconnectAttempts = {}
    this.maxReconnectAttempts = 5
  }

  getWebSocketUrl(endpoint) {
    const baseUrl = process.env.VUE_APP_API_BASE_URL || 'http://localhost:8000'
    return baseUrl.replace('http', 'ws') + '/api/v1/ws/' + endpoint
  }

  connect(endpoint, callback) {
    if (!this.callbacks[endpoint]) {
      this.callbacks[endpoint] = []
    }
    this.callbacks[endpoint].push(callback)

    if (this.connections[endpoint] && this.connections[endpoint].readyState === WebSocket.OPEN) {
      return
    }

    const url = this.getWebSocketUrl(endpoint)
    const ws = new WebSocket(url)

    ws.onopen = () => {
      console.log(`WebSocket connected to ${endpoint}`)
      this.reconnectAttempts[endpoint] = 0
    }

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        if (data.type !== 'ping') {
          this.callbacks[endpoint].forEach(cb => cb(data))
        }
      } catch (error) {
        console.error('WebSocket message parse error:', error)
      }
    }

    ws.onerror = (error) => {
      console.error(`WebSocket error on ${endpoint}:`, error)
    }

    ws.onclose = (event) => {
      console.log(`WebSocket closed on ${endpoint}:`, event.code, event.reason)
      
      if (event.code !== 1000) {
        this.scheduleReconnect(endpoint)
      }
    }

    this.connections[endpoint] = ws
  }

  scheduleReconnect(endpoint) {
    const attempts = this.reconnectAttempts[endpoint] || 0
    if (attempts >= this.maxReconnectAttempts) {
      console.error(`Max reconnection attempts reached for ${endpoint}`)
      return
    }

    this.reconnectAttempts[endpoint] = attempts + 1
    const delay = Math.pow(2, attempts) * 1000

    setTimeout(() => {
      console.log(`Reconnecting to ${endpoint} (attempt ${attempts + 1})`)
      this.connect(endpoint, () => {})
    }, delay)
  }

  disconnect(endpoint) {
    if (this.connections[endpoint]) {
      this.connections[endpoint].close(1000, 'Client requested disconnect')
      delete this.connections[endpoint]
    }
    if (this.callbacks[endpoint]) {
      delete this.callbacks[endpoint]
    }
  }

  disconnectAll() {
    Object.keys(this.connections).forEach(endpoint => {
      this.disconnect(endpoint)
    })
  }

  // 便捷方法
  onAlert(callback) {
    this.connect('alerts', callback)
  }

  onLog(callback) {
    this.connect('logs', callback)
  }

  onSystem(callback) {
    this.connect('system', callback)
  }
}

export const websocketService = new WebSocketService()

export default websocketService