import axios from 'axios';

// Create axios instance with base configuration
const axiosInstance = axios.create({
    baseURL: process.env.NEXT_PUBLIC_API_URL,
    timeout: 5000,
    headers: {
        'Content-Type': 'application/json'
    }
});

// Add response interceptor for error handling
axiosInstance.interceptors.response.use(
    response => response,
    error => {
        if (error.code === 'ECONNABORTED') {
            return Promise.reject(new Error('Request timeout: The server took too long to respond'));
        }
        if (error.response?.status === 503) {
            return Promise.reject(new Error('Server is temporarily unavailable. Please try again later.'));
        }
        if (error.response?.status === 404) {
            return Promise.reject(new Error('The requested resource was not found.'));
        }
        return Promise.reject(error);
    }
);

// Create API paths object to avoid typos and make path management easier
const API_PATHS = {
    base: '/trains',
    database: {
        versions: '/trains/database/versions',
        labels: '/trains/database/labels',
        refresh: '/trains/database/refresh',
        selected: '/trains/database/selected'
    },
    csv: '/trains/csv-files'
};

// Retry configuration
const RETRY_COUNT = 2;
const RETRY_DELAY = 2000; // 2 seconds

// Helper function to delay execution
const delay = ms => new Promise(resolve => setTimeout(resolve, ms));

// Helper function to handle retries
const withRetry = async (fn, retries = RETRY_COUNT) => {
    let lastError;
    
    for (let i = 0; i < retries; i++) {
        try {
            return await fn();
        } catch (error) {
            console.log(`Attempt ${i + 1} failed:`, error);
            lastError = error;
            if (i < retries - 1) {
                await delay(RETRY_DELAY);
            }
        }
    }
    throw lastError;
};

const api = {
    // Task Management
    getTasks: async ({ page = 1, pageSize = 10, status = null } = {}) => {
        const makeRequest = async () => {
            console.log('Making getTasks request to:', API_PATHS.base);
            const params = new URLSearchParams({
                page,
                page_size: pageSize,
                ...(status && { status })
            });
            
            try {
                const response = await axiosInstance.get(`${API_PATHS.base}?${params}`);
                
                // Check if the response contains the expected data structure
                if (!response.data || !Array.isArray(response.data.tasks)) {
                    throw new Error('Invalid response format from server');
                }
                
                return response;
            } catch (error) {
                console.error('Error in getTasks:', error);
                throw error;
            }
        };
        
        return withRetry(makeRequest);
    },
    createTask: (taskData) => withRetry(() => axiosInstance.post('/tasks', taskData)),
    deleteTask: async (taskId) => {
        try {
            console.log('Deleting task:', taskId);
            const response = await withRetry(() => axiosInstance.delete(`${API_PATHS.base}/${taskId}`));
            console.log('Delete response:', response);
            return response;
        } catch (error) {
            console.error('Error deleting task:', error);
            throw error;
        }
    },
    runTask: (taskId) => withRetry(() => axiosInstance.post(`${API_PATHS.base}/${taskId}/run`)),
    stopTask: (taskName) => withRetry(() => axiosInstance.post(`${API_PATHS.base}/stop/${taskName}`)),
    getTaskLogs: (taskName) => `${process.env.NEXT_PUBLIC_API_URL}${API_PATHS.base}/logs/${taskName}`,
    getQueuedTasks: () => withRetry(() => axiosInstance.get(`${API_PATHS.base}/queue`)),
    getRunningTasks: () => withRetry(() => axiosInstance.get(`${API_PATHS.base}/running`)),
    getTaskNames: () => withRetry(() => axiosInstance.get(`${API_PATHS.base}/names`)),
    
    // Database Management
    getDatabaseVersions: () => withRetry(() => axiosInstance.get(API_PATHS.database.versions)),
    refreshDatabase: () => withRetry(() => axiosInstance.post(API_PATHS.database.refresh)),
    getDatabaseLabels: () => withRetry(() => axiosInstance.get(API_PATHS.database.labels)),
    getCSVFiles: () => withRetry(() => axiosInstance.get(API_PATHS.csv)),
    
    // Local Storage Management
    getSelectedDatabase: () => {
        // Get the selected database from localStorage
        try {
            const selectedDb = localStorage.getItem('selectedTrainingDb');
            return Promise.resolve({ data: selectedDb ? JSON.parse(selectedDb) : null });
        } catch (error) {
            console.error('Error reading from localStorage:', error);
            return Promise.resolve({ data: null });
        }
    },
    setSelectedDatabase: (database) => {
        try {
            localStorage.setItem('selectedTrainingDb', JSON.stringify(database));
            return Promise.resolve({ success: true });
        } catch (error) {
            console.error('Error writing to localStorage:', error);
            return Promise.reject(error);
        }
    }
};

export default api;