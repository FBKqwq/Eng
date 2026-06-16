import request from './request'

export const USE_MOCK = true

const mockAlerts = []

export const getActiveAlerts = () => {
  if (USE_MOCK) return Promise.resolve({ data: mockAlerts })
  return request.get('/alerts/active')
}

export const acknowledgeAlert = (id) => {
  if (USE_MOCK) return Promise.resolve({ data: { id, status: 'acknowledged' } })
  return request.post(`/alerts/${id}/ack`)
}
