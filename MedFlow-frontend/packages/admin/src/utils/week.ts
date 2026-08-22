/**
 * 周日作为一周的第一天，返回周日的 00:00:00 作为 start，
 * 周六的 23:59:59 作为 end（实际只需日期，不用时分秒）
 */
export function getWeekRange(date: Date): { start: Date; end: Date } {
  const day = date.getDay() // 0=Sun, 6=Sat
  const start = new Date(date)
  start.setDate(date.getDate() - day)
  start.setHours(0, 0, 0, 0)

  const end = new Date(start)
  end.setDate(start.getDate() + 6)
  end.setHours(23, 59, 59, 999)

  return { start, end }
}

/** 返回本周周日到周六的 YYYY-MM-DD 字符串数组 */
export function getWeekDates(date: Date): string[] {
  const { start } = getWeekRange(date)
  const dates: string[] = []
  for (let i = 0; i < 7; i++) {
    const d = new Date(start)
    d.setDate(start.getDate() + i)
    dates.push(formatDate(d))
  }
  return dates
}

/** 格式化为 YYYY-MM-DD */
export function formatDate(date: Date): string {
  const y = date.getFullYear()
  const m = String(date.getMonth() + 1).padStart(2, '0')
  const d = String(date.getDate()).padStart(2, '0')
  return `${y}-${m}-${d}`
}
