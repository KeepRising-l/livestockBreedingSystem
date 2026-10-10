import { ElLoading } from 'element-plus'

/**
 * xlsx 体积很大（打包后约 420KB），改为「惰性 + 缓存」加载：只有用户真正点导入/导出时才拉取。
 *
 * 之前是顶层 `import * as XLSX from 'xlsx'`，会把这份大依赖绑进使用方的 chunk。
 * 而数据大屏（DashboardView）是登录后的默认首页，它只是「可能用到导出」，
 * 结果打开首页就白白多下载 420KB。改为动态 import 后，xlsx 变成独立异步 chunk，
 * 首屏不再加载；同一个会话内多次调用只加载一次（模块级缓存 Promise）。
 */
let xlsxModule: Promise<typeof import('xlsx')> | null = null

function loadXLSX(): Promise<typeof import('xlsx')> {
  if (!xlsxModule) xlsxModule = import('xlsx')
  return xlsxModule
}

/** 读取 Excel 第一个 sheet，转为二维数组（首行为表头；日期单元格保留为 Date 对象） */
export async function readExcel(file: File): Promise<{ headers: string[]; rows: any[][] }> {
  const XLSX = await loadXLSX()
  const buf = await file.arrayBuffer()
  const wb = XLSX.read(buf, { type: 'array', cellDates: true })
  const ws = wb.Sheets[wb.SheetNames[0]]
  if (!ws) return { headers: [], rows: [] }
  const data = XLSX.utils.sheet_to_json(ws, { header: 1, defval: '', raw: true }) as any[][]
  const headers = (data[0] || []).map((h) => String(h ?? '').trim())
  return { headers, rows: data.slice(1) }
}

/** 单元格日期格式化为 YYYY-MM-DD（兼容 Date 对象与字符串）。不依赖 xlsx，保持同步 */
export function fmtDateCell(v: unknown): string {
  if (v instanceof Date && !isNaN(v.getTime())) {
    const p = (n: number) => String(n).padStart(2, '0')
    return `${v.getFullYear()}-${p(v.getMonth() + 1)}-${p(v.getDate())}`
  }
  return v == null ? '' : String(v).trim()
}

/** 生成并下载批量入栏导入模板（需 await：xlsx 为惰性加载） */
export async function downloadImportTemplate(): Promise<void> {
  const XLSX = await loadXLSX()
  const headers = ['品种', '性别', '出生日期（必填）', '入栏日期', '来源', '备注']
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

/** 多 sheet 导出 Excel 并下载（需 await：xlsx 为惰性加载） */
export async function exportToExcel(filename: string, sheets: ExportSheet[]): Promise<void> {
  const XLSX = await loadXLSX()
  const wb = XLSX.utils.book_new()
  for (const s of sheets) {
    const ws = XLSX.utils.aoa_to_sheet([s.headers, ...s.rows])
    ws['!cols'] = s.headers.map((h) => ({ wch: Math.max(10, h.length * 2) }))
    XLSX.utils.book_append_sheet(wb, ws, s.name.slice(0, 31))
  }
  XLSX.writeFile(wb, filename)
}

/**
 * 异步导出 Excel：构建期间显示全屏 loading，并把同步的大 JSON 构建让出主线程分片处理，
 * 避免大数据量导出时界面冻结假死。构建完成自动关闭 loading 并下载。
 * @returns Promise<void>，导出过程（含 loading 展示）在 resolve 时结束
 */
export async function exportToExcelAsync(filename: string, sheets: ExportSheet[], loadingText = '正在生成 Excel...') {
  const loading = ElLoading.service({ lock: true, text: loadingText, background: 'rgba(0,0,0,0.45)' })
  try {
    // 先渲染一个空闲帧，让 loading 能画出来（避免直接同步阻塞 UI 看不到反馈）
    await new Promise((r) => setTimeout(r, 0))
    // 惰性加载 xlsx：首次导出时才下载该 chunk；loading 已先行展示，等依赖期间有反馈
    const XLSX = await loadXLSX()
    // 分片让出主线程：sheet 数多时避免一次大循环卡死交互
    const fns = sheets.map((s) => ({ headers: s.headers, rows: s.rows, name: s.name }))
    // 主线程内构造 workbook（xlsx 写文件本身同步），逐 sheet 分片执行
    const wb = XLSX.utils.book_new()
    for (let i = 0; i < fns.length; i++) {
      const s = fns[i]
      const ws = XLSX.utils.aoa_to_sheet([s.headers, ...s.rows])
      ws['!cols'] = s.headers.map((h) => ({ wch: Math.max(10, h.length * 2) }))
      XLSX.utils.book_append_sheet(wb, ws, s.name.slice(0, 31))
      // 每处理一个 sheet 让出主线程，防止 loading 期间交互冻结
      await new Promise((r) => setTimeout(r, 0))
    }
    XLSX.writeFile(wb, filename)
  } finally {
    loading.close()
  }
}
