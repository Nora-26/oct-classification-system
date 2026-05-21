import axios from 'axios';

const API_BASE = 'http://localhost:8000';

export const predictImage = async (file) => {
  const formData = new FormData();
  formData.append('file', file);
  const response = await axios.post(`${API_BASE}/predict`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  });
  return response.data;
};