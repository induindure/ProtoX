import axios from 'axios'

const BASE_URL = 'http://localhost:8001/api'

export const generateCode = async (idea, techStack) => {
  const response = await axios.post(`${BASE_URL}/generate-code`, {
    idea: idea,
    tech_stack: techStack,
  })
  return response.data
}