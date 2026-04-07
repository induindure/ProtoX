export interface IdeaModel {
  title: string
  description: string
  features: string[]
  tech_hints: string[]
  target_users: string
}

export interface IdeaScores {
  feasibility: number
  novelty: number
  market_fit: number
  total: number
}

export interface RankedIdea {
  idea: IdeaModel
  scores: IdeaScores
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
  ideas: RankedIdea[]
}

export interface IdeaListResponse {
  records: IdeaResponse[]
}