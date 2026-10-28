import { api } from './client'

export interface AuthUser {
  id: string
  email: string
}

interface MessageResponse {
  message: string
}

export const signup = async (email: string, password: string): Promise<MessageResponse> => {
  const { data } = await api.post<MessageResponse>('/auth/signup', { email, password })
  return data
}

export const login = async (email: string, password: string): Promise<AuthUser> => {
  const { data } = await api.post<AuthUser>('/auth/login', { email, password })
  return data
}

export const logout = async (): Promise<void> => {
  await api.post('/auth/logout')
}

export const getMe = async (): Promise<AuthUser> => {
  const { data } = await api.get<AuthUser>('/auth/me')
  return data
}

export const verifyEmail = async (email: string, code: string): Promise<AuthUser> => {
  const { data } = await api.post<AuthUser>('/auth/verify-email', { email, code })
  return data
}

export const resendVerification = async (email: string): Promise<MessageResponse> => {
  const { data } = await api.post<MessageResponse>('/auth/resend-verification', { email })
  return data
}