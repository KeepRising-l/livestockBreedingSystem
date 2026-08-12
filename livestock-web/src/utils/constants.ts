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
