// pages/index.js
import { useState, useEffect } from 'react';
import TrainingForm from '/components/TrainingForm';
import TaskCard from '/components/TaskCard';
import Link from 'next/link';

export default function Home() {
  const API_URL = process.env.NEXT_PUBLIC_API_URL;

  const [tasks, setTasks] = useState([]);
  const [formData, setFormData] = useState({
    name: '',
    model: 'PvsM',
    weights: 'DEFAULT',
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
    console.log("API URL:", process.env.NEXT_PUBLIC_API_URL);
    fetchTasks();
    const interval = setInterval(fetchTasks, 20000); // every 20 seconds
    return () => clearInterval(interval); // cleanup
  }, []);

  const fetchTasks = async () => {
    try {
      const res = await fetch(API_URL);
      const data = await res.json();
  
      const runningRes = await fetch(`${API_URL}/running`);
      const runningNames = await runningRes.json();
  
      // Mark tasks as running based on the `/running` endpoint
      const withStatus = data.map(task => ({
        ...task,
        isRunning: runningNames.includes(task.name),
      }));
  
      setTasks(withStatus);
    } catch (error) {
      console.error('Error fetching tasks:', error);
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

  return (
    <div className="w-full p-4 gap-4 flex flex-col bg-gray-50">
      {/* Header with Logo & Title */}
      <div className="flex">
        {/* Left column with static training form */}
        <div className="w-2/5 pr-4">
        <header className="mb-6 items-center gap-4">
          {/* Left Column: Logo & Title */}
          <div className="flex flex-col items-center">
            <img src="/logo-black.svg" alt="Logo" className="h-20 w-auto object-contain mb-1" />
            <h1 className="text-2xl text-gray-800">Computer vision trainer</h1>
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
              <img src="/tensorflow.svg" alt="TensorFlow" className="h-10 w-auto object-contain" />
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
    </div>
  );
}
