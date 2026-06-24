import request from './request'

export function analyzeRootCause(data) {
  return request({
    url: '/root_cause/analyze',
    method: 'post',
    data
  })
}

export function getAnalysisHistory(params) {
  return request({
    url: '/root_cause/history',
    method: 'get',
    params
  })
}

export function submitFeedback(analysisId, data) {
  return request({
    url: `/root_cause/${analysisId}/feedback`,
    method: 'post',
    data
  })
}
