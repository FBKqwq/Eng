/**
 * 日志分析 API
 * 提供日志模式分析、异常检测、聚类分析功能
 */

import request from './request'

/**
 * 综合日志分析
 * @param {Object} params - 分析参数
 * @param {Array} params.logs - 日志条目列表
 * @param {number} params.top_n - 返回前N个模式
 * @param {number} params.anomaly_threshold - 异常阈值
 * @param {number} params.max_clusters - 最大聚类数
 * @returns {Promise}
 */
export function logAnalysis(params) {
  return request({
    url: '/api/v1/log_analysis',
    method: 'post',
    data: params
  })
}

/**
 * 日志模式分析
 * @param {Object} params - 分析参数
 * @returns {Promise}
 */
export function analyzePattern(params) {
  return request({
    url: '/api/v1/log_analysis/pattern',
    method: 'post',
    data: params
  })
}

/**
 * 异常模式检测
 * @param {Object} params - 检测参数
 * @returns {Promise}
 */
export function detectAnomaly(params) {
  return request({
    url: '/api/v1/log_analysis/anomaly',
    method: 'post',
    data: params
  })
}

/**
 * 日志聚类分析
 * @param {Object} params - 分析参数
 * @returns {Promise}
 */
export function analyzeCluster(params) {
  return request({
    url: '/api/v1/log_analysis/cluster',
    method: 'post',
    data: params
  })
}
