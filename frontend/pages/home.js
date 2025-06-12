// pages/s.js
import { useState, useEffect } from 'react';
import TrainingForm from '../components/TrainingForm';
import TaskCard from '../components/TaskCard';
import Link from 'next/link';
import Button from '../components/ui/Button';

export default function Home() {
  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/trains';
  const API_BASE_URL = API_URL.replace(/\/trains$/, '');

  const [tasks, setTasks] = useState([]);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [dbVersions, setDbVersions] = useState([]);
  const [showVersions, setShowVersions] = useState(false);
  const [error, setError] = useState(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [pageSize] = useState(10);
  const [isLoading, setIsLoading] = useState(false);
  const [retryCount, setRetryCount] = useState(0);
  const [formData, setFormData] = useState({
    name: '',
    model: 'PvsM',
    weights: 'DEFAULT',
    datasetType: '',
    selectedDatabase: '',
    dataIn: '/media/isend/nas/PHOTO_BANK/3_SAVED_DATASETS/data_out_230712.8 - PvsM',
    outputDirectory: '/media/isend/ssd_storage/1_EYES_TRAIN/outputs/',
    batchSize: '16',
    epochs: '1',
    lr: '0.001',
    expLRDecreaseFactor: '3',
    stepSize: '20',
    gamma: '0.1',
    solver: 'adam',
    momentum: '0.9',
    weightDecay: '0.0001',
    numWorkers: '20',
    prefetchFactor: '10',
    unfreezeIndex: '0'
  });

  const fetchTasks = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const response = await api.getTasks({ 
        page: currentPage, 
        pageSize,
      });
      
      if (response?.data) {
        setTasks(response.data.tasks || []);
        setTotalPages(response.data.total_pages || 1);
        // Reset retry count on success
        setRetryCount(0);
      }
    } catch (error) {
      console.error('Error fetching tasks:', error);
      setError(error.message);
      // Increment retry count
      setRetryCount(prev => prev + 1);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    console.log("API URL:", API_URL);
    console.log("API Base URL:", API_BASE_URL);
    fetchTasks();
    fetchDbVersions();
    
    // Adjust polling interval based on retry count
    const pollInterval = Math.min(30000 + (retryCount * 5000), 60000); // Max 60s
    const interval = setInterval(fetchTasks, pollInterval);
    
    return () => clearInterval(interval);
  }, [currentPage, retryCount]);

  const fetchDbVersions = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/database/versions`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const versions = await response.json();
      setDbVersions(versions);
      setError(null);
    } catch (error) {
      console.error('Error fetching database versions:', error);
      setError('Failed to fetch database versions. Please check if the backend server is running.');
    }
  };

  const handleChange = (field) => (e) => {
    setFormData({ ...formData, [field]: e.target.value });
  };
  const handleSubmit = async (e) => {
    e.preventDefault();
    const payload = {
      ...formData,
      batch_size: Number(formData.batchSize),
      epochs: Number(formData.epochs),
      lr: Number(formData.lr),
      exp_LR_decrease_factor: Number(formData.expLRDecreaseFactor),
      step_size: Number(formData.stepSize),
      gamma: Number(formData.gamma),
      momentum: Number(formData.momentum),
      weight_decay: Number(formData.weightDecay),
      num_workers: Number(formData.numWorkers),
      prefetch_factor: Number(formData.prefetchFactor)
    };

    try {
      await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      setFormData((prev) => ({ ...prev, name: '' }));
      fetchTasks();
    } catch (error) {
      console.error('Error creating task:', error);
    }
  };
  const handleDelete = async (index) => {
    try {
      await fetch(`${API_URL}/${index}`, { method: 'DELETE' });
      fetchTasks();
    } catch (error) {
      console.error('Error deleting task:', error);
    }
  };
  const handleRun = async (index) => {
    try {
      await fetch(`${API_URL}/${index}/run`, { method: 'POST' });
      fetchTasks();
    } catch (error) {
      console.error('Error running task:', error);
    }
  }
  const handleStop = async (task_name) => {
    try {
      await fetch(`${API_URL}/stop/${task_name}`, { method: 'POST' });
      fetchTasks();
    } catch (error) {
      console.error('Error running task:', error);
    }
  }

  const handleRefreshDatabase = async () => {
    try {
      setIsRefreshing(true);
      const baseUrl = process.env.NEXT_PUBLIC_API_URL.replace(/\/trains$/, '');
      const response = await fetch(`${baseUrl}/refresh-database`, {
        method: 'POST',
      });
      
      if (!response.ok) {
        throw new Error('Failed to refresh database');
      }
      
      // Refresh both tasks and database versions
      await Promise.all([fetchTasks(), fetchDbVersions()]);
    } catch (error) {
      console.error('Error refreshing database:', error);
    } finally {
      setIsRefreshing(false);
    }
  };

  // Calculate task statistics
  const taskStats = {
    total: tasks.length,
    running: tasks.filter(task => task.status === 'running').length,
    completed: tasks.filter(task => task.status === 'completed').length,
    error: tasks.filter(task => task.status === 'error').length,
  };

  // Add pagination controls
  const handlePageChange = (newPage) => {
    setCurrentPage(newPage);
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold">Entrenador de modelos</h1>
        <p className="text-gray-500 mt-2">Listado de tareas de entrenamiento y pruebas</p>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="bg-red-50 border-l-4 border-red-400 p-4 mb-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-sm text-red-700">
                {error}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Stats Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        <div className="bg-white p-6 rounded-lg shadow">
          <div className="text-sm font-medium text-gray-500">Total Tasks</div>
          <div className="mt-2 text-3xl font-semibold">{taskStats.total}</div>
        </div>
        <div className="bg-white p-6 rounded-lg shadow">
          <div className="text-sm font-medium text-gray-500">Running</div>
          <div className="mt-2 text-3xl font-semibold text-green-600">{taskStats.running}</div>
        </div>
        <div className="bg-white p-6 rounded-lg shadow">
          <div className="text-sm font-medium text-gray-500">Completed</div>
          <div className="mt-2 text-3xl font-semibold text-blue-600">{taskStats.completed}</div>
        </div>
        <div className="bg-white p-6 rounded-lg shadow">
          <div className="text-sm font-medium text-gray-500">Failed</div>
          <div className="mt-2 text-3xl font-semibold text-red-600">{taskStats.error}</div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="flex gap-4 mb-8">
        <Link href="/training">
          <Button variant="default">New Training Task</Button>
        </Link>
        <Link href="/database">
          <Button variant="secondary">Manage Database</Button>
        </Link>
      </div>

      {/* Recent Tasks */}
      <div className="bg-white shadow rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          <h2 className="text-lg font-medium text-gray-900 mb-4">Recent Tasks</h2>
          <div className="space-y-4">
            {isLoading ? (
              <div className="flex justify-center items-center py-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
                <span className="ml-2">Loading tasks...</span>
              </div>
            ) : tasks.length === 0 ? (
              <div className="text-center py-8 bg-gray-50 rounded-lg">
                <p className="text-gray-500">No tasks found</p>
                {error && (
                  <button
                    onClick={fetchTasks}
                    className="mt-4 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
                  >
                    Retry
                  </button>
                )}
              </div>
            ) : (
              tasks.map((task, index) => (
                <TaskCard
                  key={task.id}
                  task={task}
                  onDelete={() => handleDelete(index)}
                  onRun={() => handleRun(index)}
                  onStop={() => handleStop(task.name)}
                />
              ))
            )}
          </div>
        </div>
      </div>

      {/* Pagination Controls */}
      {!isLoading && !error && totalPages > 1 && (
        <div className="flex justify-center mt-6 gap-2">
          <button
            onClick={() => handlePageChange(currentPage - 1)}
            disabled={currentPage === 1}
            className="px-4 py-2 bg-gray-200 rounded disabled:opacity-50"
          >
            Previous
          </button>
          <span className="px-4 py-2">
            Page {currentPage} of {totalPages}
          </span>
          <button
            onClick={() => handlePageChange(currentPage + 1)}
            disabled={currentPage === totalPages}
            className="px-4 py-2 bg-gray-200 rounded disabled:opacity-50"
          >
            Next
          </button>
        </div>
      )}

      {/* Database Versions Dialog */}
      {showVersions && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg p-6 max-w-md w-full">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-semibold">Database Version History</h2>
              <button
                onClick={() => setShowVersions(false)}
                className="text-gray-500 hover:text-gray-700"
              >
                ×
              </button>
            </div>
            <div className="max-h-96 overflow-y-auto">
              {dbVersions.map((version, index) => (
                <div
                  key={version.version}
                  className={`p-3 ${
                    index === 0 ? 'bg-green-50' : 'bg-white'
                  } border-b`}
                >
                  <div className="font-medium">{version.version}</div>
                  <div className="text-sm text-gray-500">
                    Created: {new Date(version.created_at).toLocaleString()}
                  </div>
                  {index === 0 && (
                    <span className="inline-block mt-1 text-xs bg-green-100 text-green-800 px-2 py-0.5 rounded">
                      Current
                    </span>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
