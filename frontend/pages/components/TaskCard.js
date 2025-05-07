// components/TaskCard.js
export default function TaskCard({ task, onDelete, onRun, onStop }) {
    return (
      <div className="border border-gray-200 rounded-lg p-4 shadow-card bg-white">
        <div className="flex justify-between items-start">
          <h3 className="text-lg font-semibold text-gray-800">{task.name}</h3>
          <button
            onClick={onDelete}
            className="px-3 py-1 bg-danger-500 text-white rounded-md text-sm hover:bg-danger-600 transition-colors"
          >
            Delete
          </button>
          <button
            onClick={onRun}
            className="px-3 py-1 bg-danger-500 text-white rounded-md text-sm hover:bg-danger-600 transition-colors"
          >
            Run
          </button>
          <button
            onClick={onStop}
            className="px-3 py-1 bg-danger-500 text-white rounded-md text-sm hover:bg-danger-600 transition-colors"
          >
            Stop
          </button>
        </div>

        <p className="text-sm mt-2">
          <span className="font-medium text-gray-700">Status:</span>{" "}
          {task.status === "running" ? (
            <span className="text-green-600 font-semibold">Running</span>
          ) : task.status === "completed" ? (
            <span className="text-blue-600 font-semibold">Completed</span>
          ) : task.status === "error" ? (
            <span className="text-red-600 font-semibold">Crashed</span>
          ) : (
            <span className="text-gray-500">Idle</span>
          )}
        </p>

  
        <div className="grid grid-cols-1 md:grid-cols-2 gap-2 mt-2 text-sm">
          <p><span className="font-medium text-gray-700">Model:</span> {task.model}</p>
          <p><span className="font-medium text-gray-700">Weights:</span> {task.weights}</p>
          <p><span className="font-medium text-gray-700">Data In:</span> {task.dataIn}</p>
          <p><span className="font-medium text-gray-700">Output Directory:</span> {task.outputDirectory}</p>
        </div>
  
        <div className="grid grid-cols-1 md:grid-cols-3 gap-2 mt-3 text-sm">
          <p><span className="font-medium text-gray-700">Batch Size:</span> {task.batchSize}</p>
          <p><span className="font-medium text-gray-700">Epochs:</span> {task.epochs}</p>
          <p><span className="font-medium text-gray-700">Learning Rate:</span> {task.lr}</p>
          <p><span className="font-medium text-gray-700">Exp LR Decrease Factor:</span> {task.exp_LR_decrease_factor}</p>
          <p><span className="font-medium text-gray-700">Step Size:</span> {task.step_size}</p>
          <p><span className="font-medium text-gray-700">Gamma:</span> {task.gamma}</p>
        </div>
  
        <div className="grid grid-cols-1 md:grid-cols-3 gap-2 mt-3 text-sm">
          <p><span className="font-medium text-gray-700">Solver:</span> {task.solver}</p>
          <p><span className="font-medium text-gray-700">Momentum:</span> {task.momentum}</p>
          <p><span className="font-medium text-gray-700">Weight Decay:</span> {task.weight_decay}</p>
          <p><span className="font-medium text-gray-700">Num Workers:</span> {task.num_workers}</p>
          <p><span className="font-medium text-gray-700">Prefetch Factor:</span> {task.prefetch_factor}</p>
        </div>
  
        <p className="mt-3 text-sm text-gray-500">
          Submitted At: {new Date(task.submitted_at).toLocaleString()}
        </p>
      </div>
    );
  }