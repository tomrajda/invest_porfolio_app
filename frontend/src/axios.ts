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

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    // check if error is 401 and wether contains response
    if (error.response && error.response.status === 401) {
      console.error("The token has expired or is invalid. Logging out...");
      
      // 1. delete token from localStorage
      localStorage.removeItem('access_token');
      
      // 2. force the page to refresh to restore the application state.
      // Restore view AuthForm.vue
      window.location.reload(); 
    }
    return Promise.reject(error); // pass the error on to the calling function
  }
);

export default apiClient;