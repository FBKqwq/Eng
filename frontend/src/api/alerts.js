import request from './request'

/** 离线演示时临时改为 true；默认走后端 M5 预警 API */
export const USE_MOCK = false

/**
 * 活跃预警 → GET /alerts/active?limit=
 *
 * limit 1~200，默认 50。
 *
 * 解包后 res.data：
 * { items[{ alert_id, alert_type, severity, status, title, affected_service, evidence_count, created_at, updated_at }], total }
 *
 * 角标计数：消费方用 data.total（TopBar F6-07）。
 *
 * 失败：catch (e) { e.error?.code }，常见 query_failed
 */
export const getActiveAlerts = (params) => {
  if (USE_MOCK) {
    return Promise.resolve({ data: { items: [], total: 0 } })
  }
  return request.get('/alerts/active', { params })
}

/**
 * 确认预警 → POST /alerts/{alert_id}/ack
 *
 * body 可选 { operator }。
 *
 * 解包后 res.data：
 * { alert_id, status: 'acknowledged' }
 *
 * 失败：catch (e) { e.error?.code }，常见 query_failed
 */
export const acknowledgeAlert = (alertId, body) => {
  if (USE_MOCK) {
    return Promise.resolve({
      data: { alert_id: alertId, status: 'acknowledged' }
    })
  }
  return request.post(`/alerts/${alertId}/ack`, body)
}
