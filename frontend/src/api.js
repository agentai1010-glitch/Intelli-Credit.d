import axios from 'axios';

const api = axios.create({
    baseURL: `${import.meta.env.VITE_API_BASE_URL}/api/v1`,
    headers: {
        'Content-Type': 'application/json',
    },
});

export const uploadDocuments = async (files) => {
    const formData = new FormData();
    for (let i = 0; i < files.length; i++) {
        formData.append('files', files[i]);
    }
    const response = await api.post('/upload/', formData, {
        headers: {
            'Content-Type': 'multipart/form-data',
        },
    });
    return response.data;
};

export const scoreCompany = async (payload) => {
    const response = await api.post('/score/', payload);
    return response.data;
};

export const fetchEvidence = async (entityName, query = '') => {
    const response = await api.get('/evidence/', { params: { entity_name: entityName, query } });
    return response.data;
};

export const generateCam = async (payload) => {
    const response = await api.post('/generate-cam/', payload, { responseType: 'blob' });
    return response.data;
};

export const fetchCamHistory = async (userId) => {
    const response = await api.get('/history/', { params: { user_id: userId } });
    return response.data;
};

export const registerUser = async (payload) => {
    const response = await api.post('/register/', payload);
    return response.data;
};

export const loginUser = async (payload) => {
    const response = await api.post('/login/', payload);
    return response.data;
};

export const checkRegulatoryIntelligence = async (companyName) => {
    const response = await api.post('/regulatory/check', { company_name: companyName });
    return response.data;
};

export default api;
