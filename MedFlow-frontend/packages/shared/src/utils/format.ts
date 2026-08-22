export function formatDate(iso: string | null): string {
  if (!iso) return '-'
  return iso.slice(0, 10)
}

export function formatDateTime(iso: string | null): string {
  if (!iso) return '-'
  return iso.slice(0, 19).replace('T', ' ')
}

export function formatFileSize(bytes: number): string {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}
