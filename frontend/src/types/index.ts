export interface IdeaModel {
  title: string
  description: string
  features: string[]
  tech_hints: string[]
  target_users: string
}

export interface IdeaRequest {
  domain: string
  app_type: string
  constraints?: string
  session_id?: string
}

export interface IdeaResponse {
  session_id: string
  record_id: string
  domain: string
  app_type: string
  ideas: IdeaModel[]
}

export interface IdeaListResponse {
  records: IdeaResponse[]
}
