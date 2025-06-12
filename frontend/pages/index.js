import { useState, useEffect } from 'react';
import api from '../services/api';
import TaskCard from '../components/TaskCard';
import TrainingForm from '../components/TrainingForm';
import TestingForm from '../components/TestingForm';
import Link from 'next/link';

export default function Home() {
    const [tasks, setTasks] = useState([]);
    const [activeTab, setActiveTab] = useState('training'); // 'training' or 'testing'
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    // Fetch tasks periodically
    useEffect(() => {
        const fetchTasks = async () => {
            try {
                console.log('Fetching tasks...');
                const response = await api.getTasks();
                console.log('Tasks response:', response);
                setTasks(response.data.tasks || []); // Handle the new response format
                setError(null);
            } catch (err) {
                setError('Failed to fetch tasks');
                console.error('Error fetching tasks:', err);
            }
        };

        fetchTasks();
        const interval = setInterval(fetchTasks, 5000);
        return () => clearInterval(interval);
    }, []);

    const handleDeleteTask = async (taskId) => {
        try {
            setError(null); // Clear any previous errors
            const deleteResponse = await api.deleteTask(taskId);
            console.log('Delete successful:', deleteResponse);
            
            // Refresh the task list
            const response = await api.getTasks();
            setTasks(response.data.tasks || []);
        } catch (err) {
            console.error('Error deleting task:', err);
            const errorMessage = err.response?.data?.detail || err.message || 'Failed to delete task';
            setError(errorMessage);
            // Show error to user
            alert(`Error: ${errorMessage}`);
        }
    };

    const handleRunTask = async (taskId) => {
        try {
            await api.runTask(taskId);
            const response = await api.getTasks();
            setTasks(response.data.tasks || []); // Handle the new response format
            setError(null);
        } catch (err) {
            setError('Failed to run task');
            console.error('Error running task:', err);
        }
    };

    const handleStopTask = async (taskName) => {
        try {
            await api.stopTask(taskName);
            const response = await api.getTasks();
            setTasks(response.data.tasks || []); // Handle the new response format
            setError(null);
        } catch (err) {
            setError('Failed to stop task');
            console.error('Error stopping task:', err);
        }
    };

    const filteredTasks = tasks.filter(task => task.taskType === activeTab);

    return (
        <div className="container mx-auto px-4 py-8">
            <div className="flex justify-between items-center mb-8">
                <div>
                    <h1 className="text-3xl font-bold">Task Management</h1>
                    <p className="text-gray-500 mt-2">Manage your training and testing tasks</p>
                </div>
                <div className="flex gap-4">
                    {/* Show a gif saved inpublic folder*/}
                    <img src="/cat.gif" alt="Eyes" className="w-10 h-10" />
                </div>
            </div>
            
            {error && (
                <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
                    {error}
                </div>
            )}

            {/* Stats Overview */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
                <div className="bg-white p-6 rounded-lg shadow">
                    <div className="text-sm font-medium text-gray-500">Total Tasks</div>
                    <div className="mt-2 text-3xl font-semibold">{tasks.length}</div>
                </div>
                <div className="bg-white p-6 rounded-lg shadow">
                    <div className="text-sm font-medium text-gray-500">Running</div>
                    <div className="mt-2 text-3xl font-semibold text-green-600">
                        {tasks.filter(task => task.status === 'running').length}
                    </div>
                </div>
                <div className="bg-white p-6 rounded-lg shadow">
                    <div className="text-sm font-medium text-gray-500">Completed</div>
                    <div className="mt-2 text-3xl font-semibold text-blue-600">
                        {tasks.filter(task => task.status === 'completed').length}
                    </div>
                </div>
                <div className="bg-white p-6 rounded-lg shadow">
                    <div className="text-sm font-medium text-gray-500">Failed</div>
                    <div className="mt-2 text-3xl font-semibold text-red-600">
                        {tasks.filter(task => task.status === 'error').length}
                    </div>
                </div>
            </div>

            {/* Tab Navigation */}
            <div className="border-b border-gray-200 mb-4">
                <nav className="-mb-px flex">
                    <button
                        onClick={() => setActiveTab('training')}
                        className={`mr-8 py-4 px-1 border-b-2 font-medium text-sm ${
                            activeTab === 'training'
                                ? 'border-blue-500 text-blue-600'
                                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                        }`}
                    >
                        Training Tasks
                    </button>
                    <button
                        onClick={() => setActiveTab('testing')}
                        className={`py-4 px-1 border-b-2 font-medium text-sm ${
                            activeTab === 'testing'
                                ? 'border-blue-500 text-blue-600'
                                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                        }`}
                    >
                        Testing Tasks
                    </button>
                </nav>
            </div>

            {/* Task List */}
            <div className="grid grid-cols-[repeat(auto-fit,minmax(250px,1fr))] gap-4 w-full">
                {filteredTasks.map((task, index) => (
                    <TaskCard
                        key={task.name}
                        task={task}
                        onDelete={() => handleDeleteTask(task.id)}
                        onRun={() => handleRunTask(task.id)}
                        onStop={() => handleStopTask(task.name)}
                    />
                ))}
                {filteredTasks.length === 0 && (
                    <div className="col-span-3 text-center py-8 bg-gray-50 rounded-lg">
                        <p className="text-gray-500">No {activeTab} tasks found.</p>
                        <Link href={`/${activeTab}`}>
                            <button className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700">
                                Create New {activeTab.charAt(0).toUpperCase() + activeTab.slice(1)} Task
                            </button>
                        </Link>
                    </div>
                )}
            </div>
        </div>
    );
} 