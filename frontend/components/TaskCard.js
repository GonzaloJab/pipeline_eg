// components/TaskCard.js
import React, { useState } from 'react';

export default function TaskCard({ task, onDelete, onRun, onStop }) {
  const [isDeleting, setIsDeleting] = useState(false);
  const [isRunning, setIsRunning] = useState(false);
  const [isStopping, setIsStopping] = useState(false);
  const [error, setError] = useState(null);

  const handleRun = async () => {
    try {
      setError(null);
      setIsRunning(true);
      await onRun(task.id);
    } catch (error) {
      setError(error.message);
    } finally {
      setIsRunning(false);
    }
  };

  const handleStop = async () => {
    try {
      setError(null);
      setIsStopping(true);
      await onStop(task.name);
    } catch (error) {
      setError(error.message);
    } finally {
      setIsStopping(false);
    }
  };

  const handleDelete = async () => {
    try {
      setError(null);
      setIsDeleting(true);
      await onDelete(task.id);
    } catch (error) {
      setError(error.message);
    } finally {
      setIsDeleting(false);
    }
  };

  const taskType = task.taskType?.toLowerCase() || 'unknown';
  
  // Determine background color based on status
  let bgColor = 'bg-white';
  let statusElement = null;

  switch (task.status?.toLowerCase()) {
    case 'running':
      bgColor = 'bg-blue-50';
      statusElement = (
        <span className="px-2 py-1 text-xs rounded-full bg-blue-100 text-blue-800">
          Running
        </span>
      );
      break;
    case 'queued':
      bgColor = 'bg-purple-50';
      statusElement = (
        <span className="px-2 py-1 text-xs rounded-full bg-purple-100 text-purple-800">
          {task.queue_position ? `Queued (#${task.queue_position})` : 'Queued'}
        </span>
      );
      break;
    case 'completed':
      bgColor = 'bg-green-50';
      statusElement = (
        <span className="px-2 py-1 text-xs rounded-full bg-green-100 text-green-800">
          Completed
        </span>
      );
      break;
    case 'error':
      bgColor = 'bg-red-50';
      statusElement = (
        <span className="px-2 py-1 text-xs rounded-full bg-red-100 text-red-800">
          Error
        </span>
      );
      break;
    default:
      statusElement = (
        <span className="px-2 py-1 text-xs rounded-full bg-gray-100 text-gray-800">
          Idle
        </span>
      );
  }

  // Determine background color based on task type
  const bgColorBasedOnType = taskType === 'testing' ? 'bg-yellow-50' : 'bg-blue-50';

  return (
    <div className="w-full mb-4">
      <div className={`border border-gray-200 rounded-lg p-4 shadow-sm ${bgColorBasedOnType}`}>
        {/* Header: Name, Type, and Status */}
        <div className="flex justify-between items-start mb-4">
          <div className="flex-grow">
            <div className="flex items-center gap-2">
              <h3 className="text-lg font-semibold text-gray-800">Task: {task.name} </h3>
              {statusElement}
            </div>
            <div className="text-gray-500 text-sm mt-1">
              Submitted: {new Date(task.submitted_at).toLocaleString()}
            </div>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium text-gray-600">
              GPU: {task.gpu}
            </span>
          </div>
        </div>

        {/* Task Details */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
          <div className="space-y-2">
            <div className="text-sm text-gray-600">
              <span className="font-medium">Model:</span> {task.model}
            </div>
            <div className="text-sm text-gray-600">
              <span className="font-medium">Weights:</span> {Array.isArray(task.weights) ? task.weights.join(', ') : task.weights}
            </div>
            {taskType === 'training' && (
              <div className="text-sm text-gray-600">
                <span className="font-medium">Dataset:</span> {task.datasetType}
              </div>
            )}
          </div>
          
          <div className="space-y-2">
            {taskType === 'training' ? (
              <>
                <div className="text-sm text-gray-600">
                  <span className="font-medium">Batch Size:</span> {task.batchSize}
                  <span className="font-medium ml-4">Epochs:</span> {task.epochs}
                </div>
                <div className="text-sm text-gray-600">
                  <span className="font-medium">Learning Rate:</span> {task.lr}
                  <span className="font-medium ml-4">Gamma:</span> {task.gamma}
                </div>
                <div className="text-sm text-gray-600">
                  <span className="font-medium">Solver:</span> {task.solver}
                  <span className="font-medium ml-4">Momentum:</span> {task.momentum}
                </div>
              </>
            ) : (
              <div className="text-sm text-gray-600">
                <span className="font-medium">Test Dataset:</span> {task.testDataset}
                <div className="mt-1">
                  <span className="font-medium">Batch Size:</span> {task.batchSize}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Error Message */}
        {task.status === 'error' && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded text-sm text-red-700">
            <div className="font-medium mb-1">Error Details:</div>
            <div className="whitespace-pre-wrap break-words">
              {task.error || 'An error occurred during task execution. Check the logs for more details.'}
            </div>
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex justify-end gap-2 mt-4">
          <button
            onClick={handleDelete}
            className="px-3 py-1.5 bg-red-500 text-white rounded-md text-sm hover:bg-red-600 transition-colors"
          >
            Delete
          </button>
          {task.status !== 'completed' && (
            <button
              onClick={handleRun}
              className="px-3 py-1.5 bg-green-600 text-white rounded-md text-sm hover:bg-green-700 transition-colors"
            >
              Run
            </button>
          )}
          {(task.status === 'running' || task.status === 'queued') && (
            <button
              onClick={handleStop}
              className="px-3 py-1.5 bg-yellow-500 text-white rounded-md text-sm hover:bg-yellow-600 transition-colors"
            >
              Stop
            </button>
          )}
        </div>
      </div>
    </div>
  );
}