// pages/index.js
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
    unfreezeIndex: '2'
  });

  useEffect(() => {
    console.log("API URL:", API_URL);
    console.log("API Base URL:", API_BASE_URL);
    fetchTasks();
    fetchDbVersions();
    const interval = setInterval(fetchTasks, 20000);
    return () => clearInterval(interval);
  }, []);

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

  const fetchTasks = async () => {
    try {
      const res = await fetch(API_URL);
      if (!res.ok) {
        throw new Error(`HTTP error! status: ${res.status}`);
      }
      const data = await res.json();
  
      const runningRes = await fetch(`${API_URL}/running`);
      if (!runningRes.ok) {
        throw new Error(`HTTP error! status: ${runningRes.status}`);
      }
      const runningNames = await runningRes.json();
  
      const withStatus = data.map(task => ({
        ...task,
        isRunning: runningNames.includes(task.name),
      }));
  
      setTasks(withStatus);
      setError(null);
    } catch (error) {
      console.error('Error fetching tasks:', error);
      setError('Failed to fetch tasks. Please check if the backend server is running.');
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

  return (
    <div className="w-full p-4 gap-4 flex flex-col bg-gray-50">
      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative" role="alert">
          <strong className="font-bold">Error!</strong>
          <span className="block sm:inline"> {error}</span>
        </div>
      )}
      {/* Header with Logo & Title */}
      <div className="flex">
        {/* Left column with static training form */}
        <div className="w-2/5 pr-4">
          <header className="mb-6 items-center gap-4">
            {/* Left Column: Logo & Title */}
            <div className="flex flex-col items-center">
              <img src="/logo-black.svg" alt="Logo" className="h-20 w-auto object-contain mb-1" />
              <h1 className="text-2xl text-gray-800">Computer vision trainer</h1>
              <div className="flex flex-col items-center gap-2">
                <Button
                  onClick={handleRefreshDatabase}
                  disabled={isRefreshing}
                  className="mt-4"
                  variant="secondary"
                >
                  {isRefreshing ? (
                    <>
                      <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-gray-700" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
                      </svg>
                      Refreshing...
                    </>
                  ) : (
                    'Refresh Database'
                  )}
                </Button>
                
              </div>
            </div>
          </header>
          <TrainingForm
            formData={formData}
            handleChange={handleChange}
            handleSubmit={handleSubmit}
          />
        </div>
        {/* Right column with scrollable tasks list */}
        <div 
          className="w-3/5 pl-4 border-l border-gray-200" 
          style={{ maxHeight: '80vh', overflowY: 'auto' }}
        >
          
          {/* Right Column: Link to Image Set */}
          <div className="flex flex-col items-center">
            <Link
              href={process.env.NEXT_PUBLIC_TENSORBOARD_URL}
              target="_blank"
              rel="noopener noreferrer"
              className="flex flex-col items-center"
            >
              <img src="/MLflow.svg" alt="MLFlow" className="h-10 w-auto object-contain" />
            </Link>
          </div>
          <h1 className="text-4xl text-gray-800 text-center mb-6">Lista de entrenamientos:</h1>
          {tasks.map((task, index) => (
            <TaskCard
              key={index}
              task={task}
              onDelete={() => handleDelete(index)}
              onRun={() => handleRun(index)}
              onStop={() => handleStop(task.name)}
            />
          ))}
        </div>
      </div>

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
