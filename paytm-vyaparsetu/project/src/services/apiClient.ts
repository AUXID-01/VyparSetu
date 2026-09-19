const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

const getHeaders = () => {
  const headers: Record<string, string> = {};
  const token = localStorage.getItem('sessionToken');
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  return headers;
};

export const apiClient = {
  get: async (endpoint: string) => {
    console.log(`🚀 [API Request] GET ${endpoint}`);
    const response = await fetch(`${BASE_URL}${endpoint}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        ...getHeaders()
      }
    });
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
    const resData = await response.json();
    console.log(`📥 [API Response] GET ${endpoint}`, resData);
    return resData;
  },

  post: async (endpoint: string, data?: any, isFormData = false) => {
    const headers = getHeaders();
    if (!isFormData) {
      headers['Content-Type'] = 'application/json';
    }
    
    console.log(`🚀 [API Request] POST ${endpoint}`, isFormData ? '[FormData]' : data);

    const response = await fetch(`${BASE_URL}${endpoint}`, {
      method: 'POST',
      headers,
      body: isFormData ? data : JSON.stringify(data)
    });
    
    const resData = await response.json();
    if (!response.ok) {
      console.error(`❌ [API Error] POST ${endpoint}`, resData);
      throw new Error(resData?.error?.message || `HTTP error! status: ${response.status}`);
    }
    console.log(`📥 [API Response] POST ${endpoint}`, resData);
    return resData;
  }
};
