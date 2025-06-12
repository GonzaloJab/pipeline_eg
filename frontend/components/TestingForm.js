import { useState, useEffect } from 'react';
import { AVAILABLE_MODELS_OPTIONS_TEST } from './formData/models_test';
import { GPU_MEMORY_OPTIONS } from './formData/gpu';
import api from '../services/api';

export default function TestingForm({ onSuccess }) {
    const [formData, setFormData] = useState({
        name: '',
        taskType: 'testing',
        model: 'GAMMA_ARCHI',
        weights: [
            '/media/isend/ssd_storage/2_EYES_INFER/MODELS/GAMMA/v2_weights/D1.pth',
            '/media/isend/ssd_storage/2_EYES_INFER/MODELS/GAMMA/v2_weights/D2.pth',
            '/media/isend/ssd_storage/2_EYES_INFER/MODELS/GAMMA/v2_weights/PvsMEFFNET_DATA_AUG_SELECTIVE_unfreeze_3-epoch20_val_loss0.3071_val_acc0.9263.pth',
            '/media/isend/ssd_storage/2_EYES_INFER/MODELS/GAMMA/v2_weights/D4_EFFNET_CRACKS_FLAKES_SLIVERS_CLEANED-epoch0_val_loss0.4925_val_acc0.9054.pth',
            '/media/isend/ssd_storage/2_EYES_INFER/MODELS/GAMMA/v2_weights/D5_EFFNET-epoch41_val_loss_0.7089_valACC_0.8826.pth'
        ],
        testDataset: '/media/isend/nas/PHOTO_BANK/4_TEST_DATA/9_TOY_GAMMA_TESTSET',
        batchSize: 32,
        numWorkers: 10,
        prefetchFactor: 2,
        gpu: '8GB'
    });

    const [csvFiles, setCsvFiles] = useState([]);
    const [error, setError] = useState(null);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        const fetchCSVFiles = async () => {
            try {
                const response = await api.getCSVFiles();
                setCsvFiles(response.data);
            } catch (err) {
                setError('Failed to fetch CSV files');
                console.error('Error fetching CSV files:', err);
            }
        };

        fetchCSVFiles();
    }, []);

    const handleChange = (field) => (e) => {
        const value = e.target.type === 'number' ? parseFloat(e.target.value) : e.target.value;
        setFormData({ ...formData, [field]: value });

        // Reset weights array when model changes
        if (field === 'model') {
            setFormData(prev => ({
                ...prev,
                [field]: value,
                weights: []
            }));
        }
    };

    const handleModelPathChange = (index, value) => {
        const newWeights = [...formData.weights];
        newWeights[index] = value;
        setFormData({ ...formData, weights: newWeights });
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError(null);
        setLoading(true);
        try {
            const taskData = {
                ...formData,
                model: formData.model,
                weights: formData.model === 'GAMMA_ARCHI' 
                    ? formData.weights 
                    : [formData.weights[0] || ''], // Single path for non-GAMMA_ARCHI
            };
            
            await api.createTask(taskData);
            setLoading(false);
            if (onSuccess) onSuccess();
        } catch (err) {
            console.error('Error creating testing task:', err);
            setError(err.response?.data?.detail || 'Failed to create testing task.');
            setLoading(false);
        }
    };

    // Model path input fields based on selected model
    const renderModelPathInputs = () => {
        if (formData.model === 'GAMMA_ARCHI') {
            const pathTypes = ['DnD', 'nD', 'PvsM', 'Punct', 'Mult'];
            return (
                <div className="grid grid-cols-1 gap-4 mt-4">
                    {pathTypes.map((type, index) => (
                        <div key={type}>
                            <label className="block text-sm font-medium text-gray-700">
                                {type} Model Path
                            </label>
                            <input
                                type="text"
                                value={formData.weights[index] || ''}
                                onChange={(e) => handleModelPathChange(index, e.target.value)}
                                required
                                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                                placeholder={`Enter ${type} model path`}
                            />
                        </div>
                    ))}
                </div>
            );
        } else {
            return (
                <div>
                    <label className="block text-sm font-medium text-gray-700">
                        Model Path
                    </label>
                    <input
                        type="text"
                        value={formData.weights[0] || ''}
                        onChange={(e) => handleModelPathChange(0, e.target.value)}
                        required
                        className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                        placeholder="Enter model path"
                    />
                </div>
            );
        }
    };

    return (
        <div className="bg-white shadow rounded-lg">
            {error && (
                <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
                    {error}
                </div>
            )}
            <form onSubmit={handleSubmit} className="px-4 py-5 sm:p-6">
                <div className="space-y-4">
                    {/* First row: 3 columns */}
                    <div className="grid grid-cols-3 gap-4">
                        {/* Task Name */}
                        <div>
                            <label className="block text-sm font-medium text-gray-700">
                                Task Name
                            </label>
                            <input
                                type="text"
                                value={formData.name}
                                onChange={handleChange("name")}
                                required
                                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                            />
                        </div>

                        {/* Model Selection */}
                        <div>
                            <label className="block text-sm font-medium text-gray-700">
                                Model
                            </label>
                            <select
                                value={formData.model}
                                onChange={handleChange("model")}
                                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                            >
                                {AVAILABLE_MODELS_OPTIONS_TEST.map(model => (
                                    <option key={model} value={model}>
                                        {model}
                                    </option>
                                ))}
                            </select>
                        </div>

                        {/* GPU Memory */}
                        <div>
                            <label className="block text-sm font-medium text-gray-700">
                                GPU Memory
                            </label>
                            <select
                                value={formData.gpu}
                                onChange={handleChange("gpu")}
                                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                            >
                                {GPU_MEMORY_OPTIONS.map(option => (
                                    <option key={option.value} value={option.value}>
                                        {option.label}
                                    </option>
                                ))}
                            </select>
                        </div>
                    </div>

                    {/* Model Paths Section */}
                    {renderModelPathInputs()}

                    {/* Test Dataset */}
                    <div>
                        <label className="block text-sm font-medium text-gray-700">
                            Dataset Path
                        </label>
                        <input
                            type="text"
                            value={formData.testDataset}
                            onChange={handleChange("testDataset")}
                            required
                            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                        />
                    </div>

                    {/* Testing Parameters */}
                    <div className="space-y-4">
                        <h3 className="text-lg font-semibold">Testing Parameters</h3>
                        <div className="grid grid-cols-3 gap-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-700">
                                    Batch Size
                                </label>
                                <input
                                    type="number"
                                    value={formData.batchSize}
                                    onChange={handleChange("batchSize")}
                                    required
                                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                                />
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-gray-700">
                                    Num Workers
                                </label>
                                <input
                                    type="number"
                                    value={formData.numWorkers}
                                    onChange={handleChange("numWorkers")}
                                    required
                                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                                />
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-gray-700">
                                    Prefetch Factor
                                </label>
                                <input
                                    type="number"
                                    value={formData.prefetchFactor}
                                    onChange={handleChange("prefetchFactor")}
                                    required
                                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                                />
                            </div>
                        </div>
                    </div>

                    <button
                        type="submit"
                        disabled={loading}
                        className={`w-full py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white 
                            ${loading ? 'bg-blue-400 cursor-not-allowed' : 'bg-blue-600 hover:bg-blue-700'} 
                            focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500`}
                    >
                        {loading ? 'Creating...' : 'Create Testing Task'}
                    </button>
                </div>
            </form>
        </div>
    );
}