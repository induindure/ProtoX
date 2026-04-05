import axios from 'axios'
import type { IdeaRequest, IdeaResponse, IdeaListResponse } from '../types'

const api = axios.create({
  baseURL: 'http://localhost:8000',
  headers: { 'Content-Type': 'application/json' },
})

export const generateIdeas = async (payload: IdeaRequest): Promise<IdeaResponse> => {
  const { data } = await api.post<IdeaResponse>('/ideas/generate', payload)
  return data
}

export const getHistory = async (): Promise<IdeaListResponse> => {
  const { data } = await api.get<IdeaListResponse>('/ideas/history')
  return data
}

export const getIdea = async (recordId: string): Promise<IdeaResponse> => {
  const { data } = await api.get<IdeaResponse>(`/ideas/${recordId}`)
  return data
}

export const deleteIdea = async (recordId: string): Promise<void> => {
  await api.delete(`/ideas/${recordId}`)
}
