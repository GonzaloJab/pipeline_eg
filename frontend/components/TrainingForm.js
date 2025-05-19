// components/TrainingForm.js
import React from 'react';
import Button from "@/components/ui/Button";

export default function TrainingForm({ formData, handleChange, handleSubmit }) {
  return (
    <form
      onSubmit={handleSubmit}
      className="max-w-screen-lg mx-auto p-6 bg-white shadow-md rounded-md"
    >
      {/* General Section */}
      
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
        <div className="space-y-1">
          <label className="block text-sm font-medium text-gray-700">
            Nombre tarea
          </label>
          <input
            type="text"
            placeholder="Task Name"
            required
            value={formData.name}
            onChange={handleChange("name")}
            className="w-full p-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <div className="space-y-1">
          <label className="block text-sm font-medium text-gray-700">
            Modelo
          </label>
          <select
            value={formData.model}
            onChange={handleChange("model")}
            className="w-full p-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="DnD">DnD</option>
            <option value="PvsM">PvsM</option>
            <option value="MULTI">MULTI</option>
            <option value="PUNCT">PUNCT</option>
          </select>
        </div>
        <div className="space-y-1">
          <label className="block text-sm font-medium text-gray-700">
            Pesos
          </label>
          <input
            type="text"
            placeholder="Weights"
            value={formData.weights}
            onChange={handleChange("weights")}
            className="w-full p-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      </div>

      {/* File Paths Section */}
      <h2 className="text-2xl font-semibold text-gray-800 mb-4">
        Rutas de archivos
      </h2>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-6">
        <div className="space-y-1">
          <label className="block text-sm font-medium text-gray-700">
            Imágenes:
          </label>
          <input
            type="text"
            placeholder="Data In"
            required
            value={formData.dataIn}
            onChange={handleChange("dataIn")}
            className="w-full p-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <div className="space-y-1">
          <label className="block text-sm font-medium text-gray-700">
            Guardar en:
          </label>
          <input
            type="text"
            placeholder="Output Directory"
            required
            value={formData.outputDirectory}
            onChange={handleChange("outputDirectory")}
            className="w-full p-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      </div>

      {/* Training Settings Section */}
      <h2 className="text-2xl font-semibold text-gray-800 mb-4">
        Hiperparámetros
      </h2>
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 mb-6">
        {/* Each input for settings can use similar styling */}
        <div className="space-y-1">
          <label className="block text-sm font-medium text-gray-700">
            Batch Size
          </label>
          <input
            type="number"
            required
            value={formData.batchSize}
            onChange={handleChange("batchSize")}
            className="w-full p-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <div className="space-y-1">
          <label className="block text-sm font-medium text-gray-700">
            Epochs
          </label>
          <input
            type="number"
            required
            value={formData.epochs}
            onChange={handleChange("epochs")}
            className="w-full p-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <div className="space-y-1">
          <label className="block text-sm font-medium text-gray-700">
            Learning Rate
          </label>
          <input
            type="number"
            step="0.0001"
            required
            value={formData.lr}
            onChange={handleChange("lr")}
            className="w-full p-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        {/* Add more inputs similarly */}
      </div>

      {/* Optimizer Settings Section */}
      <h2 className="text-2xl font-semibold text-gray-800 mb-4">
        Optimizer Settings
      </h2>
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
        <div className="space-y-1">
          <label className="block text-sm font-medium text-gray-700">
            Solver
          </label>
          <select
            value={formData.solver}
            onChange={handleChange("solver")}
            className="w-full p-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="sgd">sgd</option>
            <option value="adam">adam</option>
          </select>
        </div>
        {/* Similarly for Momentum, Weight Decay, etc. */}
      </div>

      <div className="mt-6">
        <Button
          variant="default"
          type="submit"
          className="w-full bg-red-500 text-white py-2 rounded-md hover:bg-red-600"
        >
          Create Task
        </Button>
      </div>
    </form>
  );
}
