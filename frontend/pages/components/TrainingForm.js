// components/TrainingForm.js
import React from 'react';

export default function TrainingForm({ formData, handleChange, handleSubmit }) {
  return (
    <form onSubmit={handleSubmit} className="flex items-center justify-center p-12">
      
        {/* General Information */}

        <h2 className="text-xl font-bold text-gray-800 mb-4">General Information</h2>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
          {/* Task Name */}
          <div className="space-y-1">
            <label className="block text-sm font-medium text-gray-700">Task Name</label>
            <input
              type="text"
              placeholder="Task Name"
              required
              value={formData.name}
              onChange={handleChange('name')}
              className="p-2 border border-gray-300 rounded-md w-full"
            />
          </div>
          {/* Model */}
            <div className="space-y-1">
              <label className="block text-sm font-medium text-gray-700">Model</label>
              <select
                value={formData.model}
                onChange={handleChange('model')}
                className="p-2 border border-gray-300 rounded-md w-full"
              >
                <option value="DnD">DnD</option>
                <option value="PvsM">PvsM</option>
                <option value="MULTI">MULTI</option>
                <option value="PUNCT">PUNCT</option>
              </select>
          </div>
          {/* Weights */}
          <div className="space-y-1">
            <label className="block text-sm font-medium text-gray-700">Weights</label>
            <input
              type="text"
              placeholder="Weights"
              value={formData.weights}
              onChange={handleChange('weights')}
              className="p-2 border border-gray-300 rounded-md w-full"
            />
          </div>
        </div>
      
        {/* File Paths */}
        <h2 className="text-xl font-bold text-gray-800 mb-4">File Paths</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-6">
          <div className="space-y-1">
            <label className="block text-sm font-medium text-gray-700">Data In</label>
            <input
              type="text"
              placeholder="Data In"
              required
              value={formData.dataIn}
              onChange={handleChange('dataIn')}
              className="p-2 border border-gray-300 rounded-md"
            />
          </div>
          <div className="space-y-1">
            <label className="block text-sm font-medium text-gray-700">Output Directory</label>
            <input
              type="text"
              placeholder="Output Directory"
              required
              value={formData.outputDirectory}
              onChange={handleChange('outputDirectory')}
              className="p-2 border border-gray-300 rounded-md"
            />
          </div>
        </div>
      

      {/* Training Settings */}
      <h2 className="text-xl font-bold text-gray-800 mb-4">Training Settings</h2>
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 mb-6">
        <div className="space-y-1">
          <label className="block text-sm font-medium text-gray-700">Batch Size</label>
          <input
            type="number"
            required
            value={formData.batchSize}
            onChange={handleChange('batchSize')}
            className="p-2 border border-gray-300 rounded-md"
          />
        </div>
        <div className="space-y-1">
          <label className="block text-sm font-medium text-gray-700">Epochs</label>
          <input
            type="number"
            required
            value={formData.epochs}
            onChange={handleChange('epochs')}
            className="p-2 border border-gray-300 rounded-md"
          />
        </div>
        <div className="space-y-1">
          <label className="block text-sm font-medium text-gray-700">Learning Rate</label>
          <input
            type="number"
            step="0.0001"
            required
            value={formData.lr}
            onChange={handleChange('lr')}
            className="p-2 border border-gray-300 rounded-md"
          />
        </div>
        <div className="space-y-1">
          <label className="block text-sm font-medium text-gray-700">Exp LR Decrease Factor</label>
          <input
            type="number"
            step="0.1"
            required
            value={formData.expLRDecreaseFactor}
            onChange={handleChange('expLRDecreaseFactor')}
            className="p-2 border border-gray-300 rounded-md"
          />
        </div>
        <div className="space-y-1">
          <label className="block text-sm font-medium text-gray-700">Step Size</label>
          <input
            type="number"
            required
            value={formData.stepSize}
            onChange={handleChange('stepSize')}
            className="p-2 border border-gray-300 rounded-md"
          />
        </div>
        <div className="space-y-1">
          <label className="block text-sm font-medium text-gray-700">Gamma</label>
          <input
            type="number"
            step="0.01"
            required
            value={formData.gamma}
            onChange={handleChange('gamma')}
            className="p-2 border border-gray-300 rounded-md"
          />
        </div>
      </div>

      {/* Optimizer Settings */}
      <h2 className="text-xl font-bold text-gray-800 mb-4">Optimizer Settings</h2>
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
        <div className="space-y-1">
          <label className="block text-sm font-medium text-gray-700">Solver</label>
          <select
            value={formData.solver}
            onChange={handleChange('solver')}
            className="p-2 border border-gray-300 rounded-md"
          >
            <option value="sgd">sgd</option>
            <option value="adam">adam</option>
          </select>
        </div>
        <div className="space-y-1">
          <label className="block text-sm font-medium text-gray-700">Momentum</label>
          <input
            type="number"
            step="0.01"
            required
            value={formData.momentum}
            onChange={handleChange('momentum')}
            className="p-2 border border-gray-300 rounded-md"
          />
        </div>
        <div className="space-y-1">
          <label className="block text-sm font-medium text-gray-700">Weight Decay</label>
          <input
            type="number"
            step="0.0001"
            required
            value={formData.weightDecay}
            onChange={handleChange('weightDecay')}
            className="p-2 border border-gray-300 rounded-md"
          />
        </div>
        <div className="space-y-1">
          <label className="block text-sm font-medium text-gray-700">Num Workers</label>
          <input
            type="number"
            required
            value={formData.numWorkers}
            onChange={handleChange('numWorkers')}
            className="p-2 border border-gray-300 rounded-md"
          />
        </div>
        <div className="space-y-1 col-span-2 sm:col-span-1">
          <label className="block text-sm font-medium text-gray-700">Prefetch Factor</label>
          <input
            type="number"
            required
            value={formData.prefetchFactor}
            onChange={handleChange('prefetchFactor')}
            className="p-2 border border-gray-300 rounded-md"
          />
        </div>
      </div>

      <div className="mt-6">
        <button
          type="submit"
          className="w-full px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          Create Task
        </button>
      </div>
    </form>
  );
}
