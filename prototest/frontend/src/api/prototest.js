import axios from 'axios'

const BASE_URL = 'http://localhost:8002/api'

export const runTests = async (files, projectName, techStack) => {
  const response = await axios.post(`${BASE_URL}/test`, {
    files,
    project_name: projectName,
    tech_stack: techStack,
  })
  return response.data
}