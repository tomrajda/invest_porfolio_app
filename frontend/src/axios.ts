import axios from 'axios'

// base url for all API requests
const apiClient = axios.create({
  baseURL: 'https://bckndinvestporfolioapp-production.up.railway.app/api',
  headers: {
    'Content-Type': 'application/json',
  },
})

export default apiClient;