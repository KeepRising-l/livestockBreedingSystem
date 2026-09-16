/** 用户类型 */
export const USER_TYPE_MAP: Record<number, string> = {
  1: '超级管理员',
  2: '养殖场主',
  3: '员工',
}

/** 岗位类型 */
export const POST_MAP: Record<string, string> = {
  '饲喂员': '饲喂员',
  '兽医': '兽医',
  '繁育员': '繁育员',
  '库管员': '库管员',
}

/** 岗位默认基础薪资（新建薪资配置时自动带出） */
export const DEFAULT_SALARY_MAP: Record<string, number> = {
  '饲喂员': 4500,
  '兽医': 6500,
  '繁育员': 5500,
  '库管员': 4000,
}

/** 圈舍类型 */
export const PEN_TYPE_MAP: Record<string, string> = {
  'A': '育雏舍',
  'B': '育成舍',
  'C': '繁育舍',
  'D': '种畜圈舍',
}

/** 畜种 */
export const SPECIES_OPTIONS = [
  { label: '牛', value: '牛' },
  { label: '羊', value: '羊' },
  { label: '猪', value: '猪' },
]

/** 性别 */
export const GENDER_OPTIONS = [
  { label: '公', value: '公' },
  { label: '母', value: '母' },
]

/** 档案状态 */
export const ANIMAL_STATUS_MAP: Record<string, string> = {
  '在栏': '在栏',
  '种用': '种用',
  '隔离': '隔离',
  '待出栏': '待出栏',
  '已出栏': '已出栏',
  '死亡': '死亡',
}

/** 母畜生理状态 */
export const PHYSIO_STATUS_MAP: Record<string, string> = {
  '正常': '正常',
  '发情': '发情',
  '妊娠': '妊娠',
  '泌乳': '泌乳',
  '休情': '休情',
  '淘汰': '淘汰',
}

export const PHYSIO_STATUS_OPTIONS = Object.keys(PHYSIO_STATUS_MAP).map(v => ({ label: v, value: v }))

/**
 * 各畜种生长阶段日龄区间（与后端 GROWTH_STAGE_CONFIG 保持一致，
 * 用于入栏/批量入栏时按出生日期实时预览日龄和生长阶段）
 * 格式：[阶段名, 起始日龄, 结束日龄]
 */
export const GROWTH_STAGE_RANGES: Record<string, [string, number, number][]> = {
  '牛': [
    ['犊牛期', 1, 60],
    ['保育期', 61, 180],
    ['生长期', 181, 365],
    ['育肥期', 366, 540],
  ],
  '羊': [
    ['羔羊期', 1, 45],
    ['保育期', 46, 90],
    ['生长期', 91, 180],
    ['育肥期', 181, 270],
  ],
  '猪': [
    ['仔猪期', 1, 28],
    ['保育期', 29, 70],
    ['生长期', 71, 120],
    ['育肥期', 121, 180],
  ],
}

/** 可繁育起始日龄（母羊进入适配繁育周期才显示"发情"） */
export const BREEDABLE_AGE: Record<string, number> = { '牛': 365, '羊': 300, '猪': 220 }

/** 由出生日期计算日龄（无日期返回 null） */
export function calcAgeDays(birthDate: string | null | undefined, refDate?: Date): number | null {
  if (!birthDate) return null
  const birth = new Date(birthDate + 'T00:00:00')
  if (isNaN(birth.getTime())) return null
  const ref = refDate || new Date()
  const days = Math.floor((ref.getTime() - birth.getTime()) / 86400000)
  return days < 0 ? null : days
}

/** 按畜种 + 日龄判定生长阶段（日龄 < 1 按第一阶段算，超过最后区间按繁育期算） */
export function determineGrowthStage(species: string, ageDays: number | null): string {
  const stages = GROWTH_STAGE_RANGES[species]
  if (!stages || ageDays === null) return ''
  if (ageDays < stages[0][1]) return stages[0][0]
  for (const [name, start, end] of stages) {
    if (ageDays >= start && ageDays <= end) return name
  }
  return '繁育期'
}

/** 来源 */
export const SOURCE_OPTIONS = [
  { label: '自繁', value: '自繁' },
  { label: '外购', value: '外购' },
]

/** 畜种编码（饲喂方案用） */
export const SPECIES_CODE_OPTIONS = [
  { label: '牛', value: 'cattle' },
  { label: '羊', value: 'sheep' },
  { label: '猪', value: 'pig' },
]

export const SPECIES_CODE_MAP: Record<string, string> = {
  cattle: '牛',
  sheep: '羊',
  pig: '猪',
}

/** 畜种中文 → 路由值（解析 farm.livestock_types 用） */
export const SPECIES_ROUTE_MAP: Record<string, string> = {
  '牛': 'cattle',
  '羊': 'sheep',
  '猪': 'pig',
}

/** 饲喂时段 */
export const FEED_TIME_PERIOD_OPTIONS = [
  { label: '早', value: '早' },
  { label: '晚', value: '晚' },
]

/** 饲喂投喂状态 */
export const FEED_STATUS_MAP: Record<string, string> = {
  '未投喂': '未投喂',
  '已投喂': '已投喂',
  '已跳过': '已跳过',
}

/** 审核状态 */
export const AUDIT_STATUS_MAP: Record<string, string> = {
  '待审核': '待审核',
  '通过': '通过',
  '驳回': '驳回',
}

/** 物资类型 */
export const MATERIAL_TYPE_OPTIONS = [
  { label: '饲料', value: '饲料' },
  { label: '疫苗', value: '疫苗' },
  { label: '兽药', value: '兽药' },
]

/** 物资单位 */
export const MATERIAL_UNIT_OPTIONS = ['kg', '瓶', '盒', '袋', '升']

/** 库存状态 */
export const STOCK_STATUS_MAP: Record<string, string> = {
  '正常': '正常',
  '即将过期': '即将过期',
  '已过期': '已过期',
}

/** 关联模块（领用记录用） */
export const CONSUME_MODULE_OPTIONS = [
  { label: '饲喂', value: '饲喂' },
  { label: '防疫', value: '防疫' },
  { label: '诊疗', value: '诊疗' },
  { label: '其他', value: '其他' },
]

/** 配种方式 */
export const MATING_TYPE_OPTIONS = [
  { label: '本交', value: '本交' },
  { label: '人工受精', value: '人工受精' },
]

/** 配种状态 */
export const MATING_STATUS_MAP: Record<string, string> = {
  '待孕检': '待孕检',
  '成功怀孕': '成功怀孕',
  '配种失败': '配种失败',
}

/** 孕检结果 */
export const PREGNANCY_RESULT_OPTIONS = [
  { label: '阳性', value: '阳性' },
  { label: '阴性', value: '阴性' },
]

/** 繁育预警类型 */
export const ALERT_TYPE_MAP: Record<string, string> = {
  '孕检': '孕检',
  '临产': '临产',
  '未发情': '未发情',
}

/** 预警状态 */
export const ALERT_STATUS_MAP: Record<string, string> = {
  '待处理': '待处理',
  '已处理': '已处理',
  '已忽略': '已忽略',
}
