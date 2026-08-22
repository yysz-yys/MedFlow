import * as dataDictApi from '../api/dataDict'
import type { DataDict } from '../types'

let dictCache: DataDict[] | null = null

export async function loadDict(): Promise<void> {
  const res = await dataDictApi.listDataDict({ page_size: 9999 })
  dictCache = res.data.items
}

export function getDictLabel(type: string, key: number): string {
  if (!dictCache) return String(key)
  const item = dictCache.find((d) => d.dict_type === type && d.dict_key === key)
  return item?.dict_label ?? String(key)
}

export function getDictOptions(type: string): { label: string; value: number }[] {
  if (!dictCache) return []
  return dictCache
    .filter((d) => d.dict_type === type)
    .sort((a, b) => a.sort_order - b.sort_order)
    .map((d) => ({ label: d.dict_label, value: d.dict_key }))
}
