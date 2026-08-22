export interface SchedulePeriod {
  start: string  // "08:00"
  end: string    // "11:30"
  label: string  // "上午 08:00-11:30"
}

export interface SchedulePeriods {
  morning: SchedulePeriod
  afternoon: SchedulePeriod
  evening: SchedulePeriod
  /** 供 v-for 遍历的平铺数组 */
  all: Array<{ key: string; label: string; start: string; end: string }>
  /** WeekToolbar 提示文字 */
  hintShort: string
}

const FALLBACK_RAW = '08:00,11:30,13:30,17:00,19:00,21:30'

export function parseScheduleConfig(raw?: string | null): SchedulePeriods {
  let parts: string[]
  if (raw) {
    const split = raw.split(',')
    parts = split.length === 6
      ? split.map(s => s.trim())
      : FALLBACK_RAW.split(',')
  } else {
    parts = FALLBACK_RAW.split(',')
  }

  const [ms, me, as, ae, es, ee] = parts

  const morning =   { start: ms, end: me, label: `上午 ${ms}-${me}` }
  const afternoon = { start: as, end: ae, label: `下午 ${as}-${ae}` }
  const evening =   { start: es, end: ee, label: `晚上 ${es}-${ee}` }

  return {
    morning,
    afternoon,
    evening,
    all: [
      { key: 'morning',   label: morning.label,   start: ms, end: me },
      { key: 'afternoon', label: afternoon.label, start: as, end: ae },
      { key: 'evening',   label: evening.label,   start: es, end: ee },
    ],
    hintShort: `${morning.label} | ${afternoon.label} | ${evening.label}`,
  }
}
