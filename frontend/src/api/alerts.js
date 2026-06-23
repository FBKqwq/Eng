import request from './request'

export const USE_MOCK = true

/** 活跃预警 → GET /alerts/active?limit=；解包后 res.data：{ items, total } */
export const getActiveAlerts = (params) => {
  if (USE_MOCK) {
    return Promise.resolve({ data: { items: [], total: 0 } })
  }
  return request.get('/alerts/active', { params })
}

/** 确认预警 → POST /alerts/{alert_id}/ack；解包后 res.data：{ alert_id, status } */
export const acknowledgeAlert = (alertId, body) => {
  if (USE_MOCK) {
    return Promise.resolve({
      data: { alert_id: alertId, status: 'acknowledged' }
    })
  }
  return request.post(`/alerts/${alertId}/ack`, body)
}
