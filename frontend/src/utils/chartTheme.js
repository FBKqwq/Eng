export const chartPalette = {
  primary: '#3b82f6',
  cyan: '#0891b2',
  violet: '#7c3aed',
  success: '#16a34a',
  warning: '#d97706',
  danger: '#dc2626',
  slate: '#475569',
  grid: 'rgba(148, 163, 184, 0.18)',
  label: '#64748b',
  text: '#1e293b',
  tooltipBg: 'rgba(15, 23, 42, 0.88)'
}

export const chartColors = [
  '#3b82f6',  // primary blue - 降低饱和
  '#0891b2',  // cyan
  '#7c3aed',  // violet
  '#16a34a',  // success
  '#d97706',  // warning
  '#dc2626'   // danger
]

export function tooltipStyle() {
  return {
    backgroundColor: chartPalette.tooltipBg,
    borderWidth: 0,
    padding: [8, 10],
    textStyle: {
      color: '#f8fafc',
      fontSize: 12,
      fontWeight: 600
    },
    extraCssText: 'box-shadow: 0 14px 34px rgba(15, 23, 42, 0.28); border-radius: 8px;'
  }
}

export function categoryAxis(data, extra = {}) {
  return {
    type: 'category',
    data,
    boundaryGap: extra.boundaryGap ?? true,
    axisLine: { lineStyle: { color: chartPalette.grid } },
    axisTick: { show: false },
    axisLabel: {
      color: chartPalette.label,
      fontSize: 11,
      hideOverlap: true,
      margin: 10
    },
    ...extra
  }
}

export function valueAxis(extra = {}) {
  return {
    type: 'value',
    axisLine: { show: false },
    axisTick: { show: false },
    axisLabel: {
      color: chartPalette.label,
      fontSize: 11,
      margin: 10
    },
    splitLine: {
      lineStyle: {
        color: chartPalette.grid,
        type: 'dashed'
      }
    },
    ...extra
  }
}

export function chartGrid({ legend = false, horizontal = false } = {}) {
  return {
    left: horizontal ? 12 : 10,
    right: 18,
    top: 22,
    bottom: legend ? 42 : 16,
    containLabel: true
  }
}

export function softArea(color, opacity = 0.16) {
  return {
    opacity,
    color: {
      type: 'linear',
      x: 0,
      y: 0,
      x2: 0,
      y2: 1,
      colorStops: [
        { offset: 0, color },
        { offset: 1, color: 'rgba(255,255,255,0)' }
      ]
    }
  }
}

export function legendStyle() {
  return {
    bottom: 0,
    itemWidth: 10,
    itemHeight: 6,
    textStyle: {
      color: chartPalette.label,
      fontSize: 11
    }
  }
}
