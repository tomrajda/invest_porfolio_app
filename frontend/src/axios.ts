import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_BASE_URL;

if (!BASE_URL) {
    console.error("VITE_API_BASE_URL is not set. Check your .env files.");
}
// base url for all API requests
const apiClient = axios.create({
  baseURL: BASE_URL || '/api', 
  headers: {
    'Content-Type': 'application/json',
  },
});

export default apiClient;