export const chartPalette = {
  primary: '#6f9eac',
  cyan: '#7aaeb3',
  violet: '#8f98ad',
  success: '#6d9482',
  warning: '#b28b5a',
  danger: '#b96a61',
  slate: '#59636e',
  grid: 'rgba(175, 186, 198, 0.18)',
  label: '#8e9aa6',
  text: '#e5ebf1',
  tooltipBg: 'rgba(10, 13, 18, 0.96)'
}

export const chartColors = [
  chartPalette.primary,
  chartPalette.warning,
  chartPalette.success,
  chartPalette.danger,
  chartPalette.violet,
  chartPalette.slate
]

export function tooltipStyle() {
  return {
    backgroundColor: chartPalette.tooltipBg,
    borderColor: 'rgba(188, 199, 210, 0.24)',
    borderWidth: 1,
    padding: [8, 10],
    textStyle: {
      color: '#eef3f7',
      fontSize: 12,
      fontWeight: 700
    },
    extraCssText: 'box-shadow: 0 14px 34px rgba(0, 0, 0, 0.34); border-radius: 3px;'
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
    top: 20,
    bottom: legend ? 42 : 16,
    containLabel: true
  }
}

export function softArea(color, opacity = 0.12) {
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
