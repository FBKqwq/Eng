<template>
  <div class="time-series-chart">
    <BaseChart :option="chartOption" :height="height" :loading="loading" />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import BaseChart from './BaseChart.vue'

const props = defineProps({
  historicalData: { type: Array, default: () => [] },
  predictions: { type: Array, default: () => [] },
  anomalies: { type: Array, default: () => [] },
  metricName: { type: String, default: '' },
  height: { type: String, default: '300px' },
  loading: { type: Boolean, default: false }
})

const chartOption = computed(() => {
  if (!props.historicalData || props.historicalData.length === 0) {
    return {}
  }

  const historyX = props.historicalData.map(d => formatTime(d.timestamp))
  const historyY = props.historicalData.map(d => d.value)
  
  const predictionX = props.predictions.map(p => formatTime(p.timestamp))
  const predictionY = props.predictions.map(p => p.predicted_value)
  const lowerBound = props.predictions.map(p => p.lower_bound)
  const upperBound = props.predictions.map(p => p.upper_bound)
  
  const anomalyMarks = props.anomalies.map(a => ({
    name: `异常点 ${formatTime(a.timestamp)}`,
    coord: [formatTime(a.timestamp), a.value],
    value: a.value,
    itemStyle: {
      color: a.level === 'critical' ? '#dc2626' : '#f59e0b'
    },
    label: {
      formatter: `${a.value}`,
      position: 'top'
    }
  }))

  return {
    title: {
      text: props.metricName || '时序数据',
      left: 'center',
      textStyle: {
        fontSize: 14,
        fontWeight: 600,
        color: '#1e293b'
      }
    },
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(255, 255, 255, 0.95)',
      borderColor: '#e2e8f0',
      borderWidth: 1,
      textStyle: {
        color: '#334155'
      },
      formatter: function(params) {
        let result = `<div style="font-weight:600;margin-bottom:8px;">${params[0].axisValue}</div>`
        params.forEach(param => {
          const color = param.seriesName.includes('预测') ? '#22c55e' : param.seriesName.includes('上限') ? '#ef4444' : param.seriesName.includes('下限') ? '#3b82f6' : '#6366f1'
          result += `<div style="display:flex;align-items:center;margin:4px 0;">
            <span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:${color};margin-right:8px;"></span>
            <span>${param.seriesName}: <strong>${param.value}</strong></span>
          </div>`
        })
        return result
      }
    },
    legend: {
      data: ['历史数据', '预测趋势', '置信区间', '异常点'],
      bottom: 10,
      textStyle: {
        fontSize: 12,
        color: '#64748b'
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '15%',
      top: '15%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: [...historyX, ...predictionX],
      axisLine: {
        lineStyle: {
          color: '#e2e8f0'
        }
      },
      axisLabel: {
        fontSize: 11,
        color: '#64748b',
        rotate: 45
      }
    },
    yAxis: {
      type: 'value',
      axisLine: {
        show: false
      },
      axisTick: {
        show: false
      },
      splitLine: {
        lineStyle: {
          color: '#f1f5f9',
          type: 'dashed'
        }
      },
      axisLabel: {
        fontSize: 11,
        color: '#64748b'
      }
    },
    series: [
      {
        name: '历史数据',
        type: 'line',
        smooth: true,
        symbol: 'circle',
        symbolSize: 6,
        lineStyle: {
          width: 2,
          color: '#6366f1'
        },
        itemStyle: {
          color: '#6366f1',
          borderWidth: 2,
          borderColor: '#fff'
        },
        emphasis: {
          scale: true,
          itemStyle: {
            shadowBlur: 10,
            shadowColor: 'rgba(99, 102, 241, 0.5)'
          }
        },
        data: historyY
      },
      {
        name: '预测趋势',
        type: 'line',
        smooth: true,
        symbol: 'diamond',
        symbolSize: 8,
        lineStyle: {
          width: 2,
          color: '#22c55e',
          type: 'dashed'
        },
        itemStyle: {
          color: '#22c55e',
          borderWidth: 2,
          borderColor: '#fff'
        },
        emphasis: {
          scale: true
        },
        data: [...Array(historyY.length).fill(null), ...predictionY]
      },
      {
        name: '置信区间',
        type: 'line',
        smooth: true,
        symbol: 'none',
        lineStyle: {
          width: 1,
          color: '#a5b4fc',
          type: 'dashed'
        },
        data: [...Array(historyY.length).fill(null), ...upperBound],
        zlevel: 0
      },
      {
        name: '置信区间',
        type: 'line',
        smooth: true,
        symbol: 'none',
        lineStyle: {
          width: 1,
          color: '#a5b4fc',
          type: 'dashed'
        },
        areaStyle: {
          color: 'rgba(99, 102, 241, 0.1)'
        },
        data: [...Array(historyY.length).fill(null), ...lowerBound],
        zlevel: 0
      },
      {
        name: '异常点',
        type: 'scatter',
        symbol: 'pin',
        symbolSize: 50,
        itemStyle: {
          color: '#f59e0b'
        },
        data: anomalyMarks,
        zlevel: 5
      }
    ]
  }
})

function formatTime(timestamp) {
  if (!timestamp) return ''
  const date = new Date(timestamp)
  return date.toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}
</script>

<style scoped>
.time-series-chart {
  width: 100%;
}
</style>
