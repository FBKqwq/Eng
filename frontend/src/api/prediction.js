/**
 * 预测与异常检测 API 封装
 * 
 * 对应后端: /api/v1/prediction/*
 */

import request from './request'

/**
 * 时序异常检测
 * @param {Object} data - 检测参数
 * @param {string} data.metric_name - 指标名称
 * @param {Array} data.data - 时序数据点 [{timestamp, value}, ...]
 * @param {string} [data.method='zscore'] - 检测方法: zscore/iqr/mad
 * @param {number} [data.threshold=2.0] - 异常阈值
 * @param {number} [data.sensitivity=1.0] - 灵敏度
 */
export function detectAnomaly(data) {
  return request({
    url: '/prediction/anomaly',
    method: 'post',
    data
  })
}

/**
 * 趋势预测
 * @param {Object} data - 预测参数
 * @param {string} data.metric_name - 指标名称
 * @param {Array} data.data - 历史时序数据
 * @param {string} [data.method='linear'] - 预测方法: linear/moving_average/exponential_smoothing
 * @param {number} [data.forecast_steps=5] - 预测步数
 * @param {number} [data.interval_minutes=5] - 数据间隔分钟数
 */
export function predictTrend(data) {
  return request({
    url: '/prediction/trend',
    method: 'post',
    data
  })
}

/**
 * 综合预测（异常检测 + 趋势预测）
 * @param {Object} data - 预测参数
 * @param {string} data.metric_name - 指标名称
 * @param {Array} data.data - 时序数据
 * @param {string} [data.detect_method='zscore'] - 异常检测方法
 * @param {string} [data.predict_method='linear'] - 趋势预测方法
 * @param {number} [data.forecast_steps=5] - 预测步数
 * @param {number} [data.threshold=2.0] - 异常阈值
 * @param {number} [data.interval_minutes=5] - 数据间隔分钟数
 */
export function prediction(data) {
  return request({
    url: '/prediction',
    method: 'post',
    data
  })
}
