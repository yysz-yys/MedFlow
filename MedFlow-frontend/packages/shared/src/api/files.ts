import request from './request'

export function uploadFile(relatedType: string, relatedId: number, file: File) {
  const form = new FormData()
  form.append('related_type', relatedType)
  form.append('related_id', String(relatedId))
  form.append('file', file)
  return request.post<{ id: number; file_name: string }>('/files/upload', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

export function downloadFile(id: number) {
  return request.get(`/files/${id}/download`, { responseType: 'blob' })
}

export function deleteFile(id: number) {
  return request.delete(`/files/${id}`)
}
