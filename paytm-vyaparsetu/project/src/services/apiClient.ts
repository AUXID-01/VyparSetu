const BASE_URL = 'http://localhost:8000/api/v1';

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
    const response = await fetch(`${BASE_URL}${endpoint}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        ...getHeaders()
      }
    });
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
    return response.json();
  },

  post: async (endpoint: string, data?: any, isFormData = false) => {
    const headers = getHeaders();
    if (!isFormData) {
      headers['Content-Type'] = 'application/json';
    }
    
    const response = await fetch(`${BASE_URL}${endpoint}`, {
      method: 'POST',
      headers,
      body: isFormData ? data : JSON.stringify(data)
    });
    
    const resData = await response.json();
    if (!response.ok) throw new Error(resData?.error?.message || `HTTP error! status: ${response.status}`);
    return resData;
  }
};
