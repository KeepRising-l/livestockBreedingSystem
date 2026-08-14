import * as XLSX from 'xlsx'

/** 读取 Excel 第一个 sheet，转为二维数组（首行为表头；日期单元格保留为 Date 对象） */
export async function readExcel(file: File): Promise<{ headers: string[]; rows: any[][] }> {
  const buf = await file.arrayBuffer()
  const wb = XLSX.read(buf, { type: 'array', cellDates: true })
  const ws = wb.Sheets[wb.SheetNames[0]]
  if (!ws) return { headers: [], rows: [] }
  const data = XLSX.utils.sheet_to_json(ws, { header: 1, defval: '', raw: true }) as any[][]
  const headers = (data[0] || []).map((h) => String(h ?? '').trim())
  return { headers, rows: data.slice(1) }
}

/** 单元格日期格式化为 YYYY-MM-DD（兼容 Date 对象与字符串） */
export function fmtDateCell(v: unknown): string {
  if (v instanceof Date && !isNaN(v.getTime())) {
    const p = (n: number) => String(n).padStart(2, '0')
    return `${v.getFullYear()}-${p(v.getMonth() + 1)}-${p(v.getDate())}`
  }
  return v == null ? '' : String(v).trim()
}

/** 生成并下载批量入栏导入模板 */
export function downloadImportTemplate() {
  const headers = ['品种', '性别', '出生日期', '入栏日期', '来源', '备注']
  const example = ['西门塔尔', '母', '2026-03-01', '2026-08-14', '外购', '示例行，导入前可删除']
  const ws = XLSX.utils.aoa_to_sheet([headers, example])
  ws['!cols'] = [{ wch: 14 }, { wch: 8 }, { wch: 12 }, { wch: 12 }, { wch: 8 }, { wch: 30 }]
  const wb = XLSX.utils.book_new()
  XLSX.utils.book_append_sheet(wb, ws, '批量入栏模板')
  XLSX.writeFile(wb, '批量入栏导入模板.xlsx')
}

export interface ExportSheet {
  name: string
  headers: string[]
  rows: (string | number)[][]
}

/** 多 sheet 导出 Excel 并下载 */
export function exportToExcel(filename: string, sheets: ExportSheet[]) {
  const wb = XLSX.utils.book_new()
  for (const s of sheets) {
    const ws = XLSX.utils.aoa_to_sheet([s.headers, ...s.rows])
    ws['!cols'] = s.headers.map((h) => ({ wch: Math.max(10, h.length * 2) }))
    XLSX.utils.book_append_sheet(wb, ws, s.name.slice(0, 31))
  }
  XLSX.writeFile(wb, filename)
}
