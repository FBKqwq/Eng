import request from './request'

export function askLogQA(data) {
  return request({
    url: '/log_qa/ask',
    method: 'post',
    data
  })
}

export function getQAHierarchy(params) {
  return request({
    url: '/log_qa/history',
    method: 'get',
    params
  })
}
