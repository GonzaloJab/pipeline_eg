import { useState } from 'react';
import TestingForm from '../components/TestingForm';
import api from '../services/api';

export default function Testing() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  const handleSubmit = async (formData) => {
    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      await api.createTask(formData);
      setSuccess('Testing task started successfully!');
    } catch (error) {
      console.error('Error starting test:', error);
      setError('Failed to start testing task. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold">Model Testing</h1>
        <p className="text-gray-500 mt-2">Test your trained models with new data</p>
      </div>

      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-4" role="alert">
          <strong className="font-bold">Error!</strong>
          <span className="block sm:inline"> {error}</span>
        </div>
      )}

      {success && (
        <div className="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded relative mb-4" role="alert">
          <strong className="font-bold">Success!</strong>
          <span className="block sm:inline"> {success}</span>
        </div>
      )}

      <TestingForm onSubmit={handleSubmit} loading={loading} />
    </div>
  );
} 