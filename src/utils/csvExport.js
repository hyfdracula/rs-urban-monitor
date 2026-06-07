/**
 * Export an array of objects as a CSV file download.
 *
 * @param {Object[]} data - Array of row objects
 * @param {string[]} headers - Column headers (display names)
 * @param {string[]} keys - Object property keys matching headers
 * @param {string} filename - Download filename
 */
export function exportCsv(data, headers, keys, filename = 'export.csv') {
  if (!data || data.length === 0) return

  const escape = (val) => {
    const s = String(val ?? '')
    return s.includes(',') || s.includes('"') || s.includes('\n')
      ? `"${s.replace(/"/g, '""')}"`
      : s
  }

  const headerRow = headers.map(escape).join(',')
  const rows = data.map(item =>
    keys.map(k => escape(item[k])).join(',')
  )

  const csv = '﻿' + [headerRow, ...rows].join('\n')
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  link.click()
  URL.revokeObjectURL(url)
}
