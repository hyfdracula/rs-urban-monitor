import jsPDF from 'jspdf'
import html2canvas from 'html2canvas'

// Available sections with their labels
export const REPORT_SECTIONS = {
  expansion: { label: '建设用地扩张分析', icon: '🏗️' },
  ecology: { label: '生态环境评估', icon: '🌿' },
  socio: { label: '社会经济分析', icon: '📊' },
  correlation: { label: '扩张与生态关联分析', icon: '🔗' },
}

/**
 * Capture a DOM element as a base64 image via html2canvas
 */
export async function captureElement(el, options = {}) {
  if (!el) return null
  try {
    const canvas = await html2canvas(el, {
      backgroundColor: '#1a1a1a',
      scale: options.scale || 2,
      useCORS: true,
      logging: false,
    })
    return canvas.toDataURL('image/png')
  } catch (err) {
    console.warn('Failed to capture element:', err)
    return null
  }
}

/**
 * Capture a Mapbox GL map as base64 image
 */
export async function captureMap(mapInstance) {
  if (!mapInstance) return null
  try {
    const canvas = mapInstance.getCanvas()
    return canvas.toDataURL('image/png')
  } catch (err) {
    console.warn('Failed to capture map:', err)
    return null
  }
}

/**
 * Build report as a hidden HTML element, then capture pages via html2canvas.
 * This avoids jsPDF font issues with Chinese characters entirely.
 */
export async function buildPdfReport(options) {
  const { title, studyArea, timeRange, sections } = options

  // Create a hidden container
  const container = document.createElement('div')
  container.style.cssText = `
    position: fixed; top: -9999px; left: -9999px;
    width: 794px; background: #1a1a1a; color: #e0e0e0;
    font-family: -apple-system, BlinkMacSystemFont, 'Microsoft YaHei', 'PingFang SC', sans-serif;
    font-size: 14px; line-height: 1.6; z-index: -1;
  `
  document.body.appendChild(container)

  // Build all pages as HTML
  const pages = []

  // ── Cover page ──
  const coverHtml = buildCoverPage(title, studyArea, timeRange, sections)
  pages.push({ html: coverHtml })

  // ── Content pages ──
  for (const section of sections) {
    const sectionHtml = buildSectionPage(section, sections)
    pages.push({ html: sectionHtml })
  }

  // Render and capture
  const doc = new jsPDF({ orientation: 'portrait', unit: 'mm', format: 'a4' })
  const pageW = doc.internal.pageSize.getWidth()
  const pageH = doc.internal.pageSize.getHeight()

  for (let i = 0; i < pages.length; i++) {
    // Set HTML content
    container.innerHTML = pages[i].html

    // Wait for images to load
    await new Promise(r => setTimeout(r, 100))

    // Capture
    const canvas = await html2canvas(container, {
      backgroundColor: '#1a1a1a',
      scale: 2,
      useCORS: true,
      logging: false,
      width: 794,
      windowWidth: 794,
    })

    const imgData = canvas.toDataURL('image/jpeg', 0.92)
    const imgW = pageW
    const imgH = (canvas.height / canvas.width) * pageW

    if (i > 0) doc.addPage()

    // If content is taller than one page, split across pages
    if (imgH <= pageH) {
      doc.addImage(imgData, 'JPEG', 0, 0, imgW, imgH)
    } else {
      // Split into multiple pages
      let srcY = 0
      const ratio = pageW / canvas.width
      const pageHpx = pageH / ratio

      while (srcY < canvas.height) {
        if (srcY > 0) doc.addPage()
        const sliceH = Math.min(pageHpx, canvas.height - srcY)

        // Create a slice canvas
        const sliceCanvas = document.createElement('canvas')
        sliceCanvas.width = canvas.width
        sliceCanvas.height = sliceH
        const ctx = sliceCanvas.getContext('2d')
        ctx.drawImage(canvas, 0, srcY, canvas.width, sliceH, 0, 0, canvas.width, sliceH)

        const sliceImg = sliceCanvas.toDataURL('image/jpeg', 0.92)
        const sliceImgH = (sliceH / canvas.width) * pageW
        doc.addImage(sliceImg, 'JPEG', 0, 0, imgW, sliceImgH)
        srcY += pageHpx
      }
    }
  }

  // Add page numbers
  const totalPages = doc.internal.pages.length
  for (let i = 1; i <= totalPages; i++) {
    doc.setPage(i)
    doc.setFontSize(8)
    doc.setTextColor(102, 102, 102)
    doc.text(`${i} / ${totalPages}`, pageW - 15, pageH - 6, { align: 'right' })
  }

  // Cleanup
  document.body.removeChild(container)

  return doc
}

// ──────────────────────────────────────────────
// HTML builders
// ──────────────────────────────────────────────

function buildCoverPage(title, studyArea, timeRange, sections) {
  const now = new Date()
  const dateStr = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`

  const sectionList = sections.map((s, i) => {
    const info = REPORT_SECTIONS[s.key] || { label: s.title, icon: '📄' }
    return `<div class="toc-item">${i + 1}. ${info.icon} ${info.label}</div>`
  }).join('')

  return `
    <div style="padding: 60px 50px; min-height: 1100px; display: flex; flex-direction: column;">
      <!-- Header block -->
      <div style="background: #222; border-radius: 8px; padding: 40px 35px; border-left: 4px solid #FF6B6B;">
        <div style="font-size: 28px; font-weight: 700; color: #fff; margin-bottom: 16px;">${title}</div>
        <div style="font-size: 14px; color: #aaa; margin-bottom: 6px;">📍 研究区域: ${studyArea}</div>
        <div style="font-size: 14px; color: #aaa; margin-bottom: 6px;">📅 分析时段: ${timeRange}</div>
        <div style="font-size: 12px; color: #666; margin-top: 16px;">报告生成日期: ${dateStr}</div>
      </div>

      <!-- TOC -->
      <div style="margin-top: 40px;">
        <div style="font-size: 16px; font-weight: 600; color: #ccc; margin-bottom: 16px; padding-bottom: 8px; border-bottom: 1px solid #333;">报告目录</div>
        ${sectionList}
      </div>

      <!-- Footer -->
      <div style="margin-top: auto; padding-top: 30px; border-top: 1px solid #2a2a2a;">
        <div style="font-size: 12px; color: #555; text-align: center;">RS Urban Monitor — 城市扩张与生态环境评估系统</div>
      </div>
    </div>
  `
}

function buildSectionPage(section, allSections) {
  const info = REPORT_SECTIONS[section.key] || { label: section.title, icon: '📄' }
  let html = `<div style="padding: 35px 45px;">`

  // Section header
  html += `
    <div style="background: #262626; border-radius: 6px; padding: 10px 16px; margin-bottom: 20px;">
      <span style="font-size: 18px; font-weight: 700; color: #fff;">${info.icon} ${info.label}</span>
    </div>
  `

  // Cards row
  if (section.cards && section.cards.length > 0) {
    const cardW = Math.floor((100 - section.cards.length * 1.5) / section.cards.length)
    html += `<div style="display: flex; gap: 8px; margin-bottom: 20px;">`
    for (const card of section.cards) {
      html += `
        <div style="flex: 1; background: #252525; border-radius: 6px; padding: 12px 14px;">
          <div style="font-size: 20px; font-weight: 700; color: #fff;">${card.value}</div>
          <div style="font-size: 11px; color: #888; margin-top: 4px;">${card.label}</div>
        </div>
      `
    }
    html += `</div>`
  }

  // Charts
  if (section.charts && section.charts.length > 0) {
    for (const chart of section.charts) {
      if (!chart.dataUrl) continue
      html += `<div style="margin-bottom: 16px;">`
      if (chart.label) {
        html += `<div style="font-size: 12px; color: #999; margin-bottom: 6px;">${chart.label}</div>`
      }
      html += `<img src="${chart.dataUrl}" style="width: 100%; border-radius: 4px; background: #1a1a1a;" />`
      html += `</div>`
    }
  }

  // Table
  if (section.table && section.table.headers && section.table.rows) {
    const colCount = section.table.headers.length
    const colW = Math.floor(100 / colCount)

    // Header row
    html += `<div style="margin-bottom: 16px;">`
    html += `<table style="width: 100%; border-collapse: collapse; font-size: 12px;">`
    html += `<thead><tr style="background: #2c2c2c;">`
    for (const h of section.table.headers) {
      html += `<th style="padding: 8px 6px; text-align: left; color: #ccc; font-weight: 600; border-bottom: 1px solid #444;">${h}</th>`
    }
    html += `</tr></thead><tbody>`

    // Data rows
    for (let ri = 0; ri < section.table.rows.length; ri++) {
      const bg = ri % 2 === 0 ? '#1e1e1e' : 'transparent'
      html += `<tr style="background: ${bg};">`
      for (const cell of section.table.rows[ri]) {
        html += `<td style="padding: 6px; color: #bbb; border-bottom: 1px solid #2a2a2a;">${cell}</td>`
      }
      html += `</tr>`
    }
    html += `</tbody></table></div>`
  }

  // Divider
  html += `<div style="margin-top: 20px; border-top: 1px solid #2a2a2a;"></div>`

  html += `</div>`
  return html
}

/**
 * Download a PDF (triggers browser download)
 */
export function downloadPdf(doc, filename) {
  doc.save(filename || `urban-monitor-report-${Date.now()}.pdf`)
}
