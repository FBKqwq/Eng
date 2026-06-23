/**
 * /logs/aggregate 响应 → 图表 props 解析（按 template + chartType + variant）
 */

const FUNNEL_DEFAULT_STEPS = [
  'page_view',
  'product_click',
  'add_to_cart',
  'checkout_click',
  'pay_button_click'
]

const RISK_LEVEL_COLORS = {
  low: '#16a34a',
  medium: '#d97706',
  high: '#dc2626',
  critical: '#7f1d1d'
}

function formatBucketKey(key) {
  if (key == null || key === '') return '未知'
  return String(key)
}

function bucketCount(bucket) {
  return Number(bucket?.count ?? 0)
}

function bucketValue(bucket) {
  const value = bucket?.value
  if (value != null && !Number.isNaN(Number(value))) return Number(value)
  return bucketCount(bucket)
}

/**
 * @param {object} config chartTemplates 项
 * @param {object|null} aggregateData API data
 * @returns {{ chartProps: object, meta: { unit: string, caliber: string, empty: boolean } }}
 */
export function resolveChartData(config, aggregateData) {
  if (!aggregateData) {
    return emptyResult(config)
  }

  const template = config.template
  const chartType = config.chartType
  const variant = config.options?.variant || inferVariant(config)
  const buckets = aggregateData.buckets ?? []
  const extra = aggregateData.extra ?? {}

  if (template === 'errors') {
    return resolveErrorsChart(config, chartType, variant, buckets, extra)
  }
  if (template === 'latency') {
    return resolveLatencyChart(config, chartType, variant, buckets, extra)
  }
  if (template === 'behavior_funnel') {
    return resolveFunnelChart(config, buckets, extra)
  }
  if (template === 'security') {
    return resolveSecurityChart(config, chartType, variant, buckets, extra)
  }
  if (template === 'infra_health') {
    return resolveInfraChart(config, chartType, buckets, extra)
  }
  if (template === 'traffic') {
    return resolveTrafficChart(config, chartType, buckets, extra)
  }

  return genericTermsChart(config, chartType, buckets)
}

function inferVariant(config) {
  const groupBy = config.options?.group_by
  if (config.template === 'errors') {
    if (config.chartType === 'trend') return 'trend'
    if (groupBy === 'status_code') return 'status_code'
    return 'error_code'
  }
  if (config.template === 'security') {
    if (groupBy === 'client_ip') return 'client_ip'
    return 'risk_level'
  }
  if (config.template === 'latency') {
    return config.options?.percentile || 'p95'
  }
  return 'default'
}

function resolveErrorsChart(config, chartType, variant, buckets, extra) {
  if (chartType === 'trend') {
    const seriesData = buckets.map((b) => bucketCount(b))
    return {
      chartProps: {
        categories: buckets.map((b) => formatBucketKey(b.key)),
        series: [{ name: '错误量', data: seriesData, area: true }]
      },
      meta: {
        unit: '条',
        caliber: 'ERROR 级别或 HTTP ≥400 的日志量，按时间桶计数',
        empty: !seriesData.some((n) => n > 0)
      }
    }
  }

  if (chartType === 'pie') {
    const source =
      variant === 'status_code' && extra.by_status_code?.length
        ? extra.by_status_code
        : extra.by_error_code?.length
          ? extra.by_error_code
          : buckets

    const data = source.map((b) => ({
      name: formatBucketKey(b.key),
      value: bucketCount(b)
    }))

    return {
      chartProps: { data },
      meta: {
        unit: '条',
        caliber:
          variant === 'status_code'
            ? 'HTTP 状态码分布（application + web_server）'
            : 'error_code 分布（application + web_server）',
        empty: !data.some((d) => d.value > 0)
      }
    }
  }

  return genericTermsChart(config, chartType, buckets)
}

function resolveLatencyChart(config, chartType, variant, buckets, extra) {
  const percentile = variant === 'p50' || variant === 'p99' ? variant : 'p95'
  const pctKey = percentile === 'p50' ? 'p50' : percentile === 'p99' ? 'p99' : 'p95'

  if (chartType === 'bar') {
    const categories = buckets.map((b) => formatBucketKey(b.key))
    const data = buckets.map((b) => Number(b.extra?.[pctKey] ?? 0))
    return {
      chartProps: {
        categories,
        series: [{ name: `${percentile.toUpperCase()} (ms)`, data }]
      },
      meta: {
        unit: 'ms',
        caliber: `各服务 response_time_ms 的 ${percentile.toUpperCase()} 分位`,
        empty: !data.some((n) => n > 0)
      }
    }
  }

  const global = extra.global_percentiles || {}
  const categories = ['全局', ...buckets.map((b) => formatBucketKey(b.key))]
  const data = [
    Number(global[pctKey] ?? 0),
    ...buckets.map((b) => Number(b.extra?.[pctKey] ?? 0))
  ]

  return {
    chartProps: {
      categories,
      series: [{ name: `${percentile.toUpperCase()} (ms)`, data }]
    },
    meta: {
      unit: 'ms',
      caliber: '全局与各服务延迟分位对比',
      empty: !data.some((n) => n > 0)
    }
  }
}

function resolveFunnelChart(config, buckets, extra) {
  const steps = extra.funnel_steps?.length ? extra.funnel_steps : FUNNEL_DEFAULT_STEPS
  const bucketMap = new Map(buckets.map((b) => [b.key, b]))
  const ordered = steps.map((step) => bucketMap.get(step) || { key: step, count: 0 })

  const categories = ordered.map((b) => formatBucketKey(b.key))
  const counts = ordered.map((b) => bucketCount(b))
  const conversionRates = ordered.map((b) => {
    const rate = b.extra?.conversion_rate
    return rate != null ? `${(Number(rate) * 100).toFixed(1)}%` : ''
  })

  return {
    chartProps: {
      categories,
      series: [
        {
          name: '步骤计数',
          data: counts,
          conversionRates
        }
      ]
    },
    meta: {
      unit: '次',
      caliber: '行为日志固定五步漏斗，转化率相对上一步',
      empty: !counts.some((n) => n > 0)
    }
  }
}

function resolveSecurityChart(config, chartType, variant, buckets, extra) {
  if (variant === 'client_ip' || config.options?.group_by === 'client_ip') {
    const source = extra.by_client_ip?.length ? extra.by_client_ip : buckets
    const categories = source.map((b) => formatBucketKey(b.key))
    const data = source.map((b) => bucketCount(b))
    return {
      chartProps: {
        categories,
        series: [{ name: '访问次数', data }]
      },
      meta: {
        unit: '次',
        caliber: '安全日志 client_ip Top N',
        empty: !data.some((n) => n > 0)
      }
    }
  }

  if (chartType === 'pie') {
    const data = buckets.map((b) => ({
      name: formatBucketKey(b.key),
      value: bucketCount(b),
      itemStyle: { color: RISK_LEVEL_COLORS[String(b.key).toLowerCase()] }
    }))
    return {
      chartProps: { data },
      meta: {
        unit: '条',
        caliber: 'security 日志 risk_level 分布',
        empty: !data.some((d) => d.value > 0)
      }
    }
  }

  const blocked = extra.blocked_count ?? 0
  return {
    chartProps: {
      categories: ['拦截次数'],
      series: [{ name: '拦截', data: [Number(blocked)] }]
    },
    meta: {
      unit: '次',
      caliber: 'is_blocked=true 或 status=403 的拦截计数',
      empty: Number(blocked) <= 0
    }
  }
}

function resolveInfraChart(config, chartType, buckets, extra) {
  const metricField = extra.metric_field || 'cpu_percent'
  const unit = metricField.includes('percent') ? '%' : metricField.includes('lag') ? '条' : ''

  if (chartType === 'pie' || chartType === 'bar') {
    const categories = buckets.map((b) => formatBucketKey(b.key))
    const data = buckets.map((b) => bucketValue(b))
    const chartProps =
      chartType === 'pie'
        ? {
            data: categories.map((name, i) => ({ name, value: data[i] }))
          }
        : {
            categories,
            series: [{ name: metricField, data }]
          }

    return {
      chartProps,
      meta: {
        unit,
        caliber: `基础设施 component 分组，指标均值 ${metricField}（后端固定字段）`,
        empty: !data.some((n) => n > 0)
      }
    }
  }

  const globalAvg = extra.avg_metric_global
  return {
    chartProps: {
      categories: buckets.map((b) => formatBucketKey(b.key)),
      series: [{ name: metricField, data: buckets.map((b) => bucketValue(b)), area: true }]
    },
    meta: {
      unit,
      caliber: `全局均值 ${globalAvg != null ? Number(globalAvg).toFixed(1) : '—'}${unit}`,
      empty: !buckets.length
    }
  }
}

function resolveTrafficChart(config, chartType, buckets, extra) {
  const byService = extra.by_service || []
  const seriesData = buckets.map((b) => bucketCount(b))

  if (chartType === 'trend') {
    return {
      chartProps: {
        categories: buckets.map((b) => formatBucketKey(b.key)),
        series: [{ name: '请求量', data: seriesData, area: true }]
      },
      meta: {
        unit: '条/桶',
        caliber: 'application + web_server 日志量时间序列（模板固定范围）',
        empty: !seriesData.some((n) => n > 0)
      }
    }
  }

  if (chartType === 'bar' && byService.length) {
    return {
      chartProps: {
        categories: byService.map((b) => formatBucketKey(b.key)),
        series: [{ name: '服务流量', data: byService.map((b) => bucketCount(b)) }]
      },
      meta: {
        unit: '条',
        caliber: '按 service_name 的流量 Top N',
        empty: !byService.some((b) => bucketCount(b) > 0)
      }
    }
  }

  return genericTermsChart(config, chartType, buckets)
}

function genericTermsChart(config, chartType, buckets) {
  if (chartType === 'pie') {
    const data = buckets.map((b) => ({
      name: formatBucketKey(b.key),
      value: bucketCount(b)
    }))
    return {
      chartProps: { data },
      meta: { unit: '条', caliber: config.description || 'terms 聚合分布', empty: !data.length }
    }
  }

  const categories = buckets.map((b) => formatBucketKey(b.key))
  const data = buckets.map((b) => bucketCount(b))
  return {
    chartProps: {
      categories,
      series: [{ name: config.title || '计数', data }]
    },
    meta: { unit: '条', caliber: config.description || '计数分布', empty: !data.some((n) => n > 0) }
  }
}

function emptyResult(config) {
  return {
    chartProps: { categories: [], series: [], data: [] },
    meta: {
      unit: '',
      caliber: config.description || '',
      empty: true
    }
  }
}

export function buildMetricsPayload(config, logType) {
  const opts = config.options ?? {}
  const payload = {
    ...(logType ? { log_types: [logType] } : {}),
    top_n: opts.top_n ?? 10
  }

  if (config.chartType === 'trend' || opts.interval) {
    payload.interval = opts.interval ?? '1m'
  }

  return payload
}
