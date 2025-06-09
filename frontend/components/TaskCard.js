// components/TaskCard.js
export default function TaskCard({ task, onDelete, onRun, onStop }) {
  // Prepare a status element based on task.status
  const statusElement =
    task.status === "running" ? (
      <>
        <svg
          className="animate-spin h-4 w-4 text-gray-500"
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
        >
          <circle
            className="opacity-25"
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            strokeWidth="4"
          ></circle>
          <path
            className="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
          ></path>
        </svg>
        <span className="text-green-600 font-semibold">Running</span>
      </>
    ) : task.status === "completed" ? (
      <>
        <span className="inline-block w-3 h-3 rounded-full bg-green-600"></span>
        <span className="text-green-600 font-semibold">Completed</span>
      </>
    ) : task.status === "error" ? (
      <>
        <span className="inline-block w-3 h-3 rounded-full bg-red-600"></span>
        <span className="text-red-600 font-semibold">Crashed</span>
      </>
    ) : (
      <>
        <span className="inline-block w-3 h-3 rounded-full bg-gray-400"></span>
        <span className="text-gray-500">Idle</span>
      </>
    );

  return (
    <div className="border border-gray-200 rounded-lg p-4 shadow-card bg-white">
      {/* Header: Name, Submitted Date, Status, and Control Buttons */}
      <div className="flex justify-between items-center mb-4">
        <div>
          <h3 className="text-lg font-semibold text-gray-800">{task.name}</h3>
          <span className="text-gray-500 text-sm">
            {new Date(task.submitted_at).toLocaleString()}
          </span>
        </div>
        <div className="flex items-center gap-2">
          {/* Status element */}
          <div className="flex items-center gap-1">
            {statusElement}
          </div>
          {/* Control buttons */}
          <button
            onClick={onDelete}
            className="px-3 py-1 bg-red-500 text-white rounded-md text-sm hover:bg-red-600 transition-colors"
          >
            Delete
          </button>
          <button
            onClick={onRun}
            className="px-3 py-1 bg-green-700 text-white rounded-md text-sm hover:bg-green-900 transition-colors"
          >
            Run
          </button>
          <button
            onClick={onStop}
            className="px-3 py-1 bg-yellow-500 text-white rounded-md text-sm hover:bg-yellow-600 transition-colors"
          >
            Stop
          </button>
        </div>
      </div>

      {/* Simplified table for properties */}
      <table className="min-w-full text-sm">
        <tbody>
          <tr className="border-b">
            <td className="p-1">Modelo: {task.model} | Weights: {task.weights}</td>
          </tr>
          <tr className="border-b">
            <td className="p-1">Dataset Type: {task.datasetType}</td>
          </tr>
          <tr className="border-b">
            <td className="p-1">Batch Size: {task.batchSize} | Epochs: {task.epochs} | Learning Rate: {task.lr} | Exp LR Factor: {task.exp_LR_decrease_factor}</td>
          </tr>
         
          {/* <tr className="border-b">
            <td className="p-1">Step Size: {task.step_size} | Gamma: {task.gamma}</td>
          </tr>
          <tr className="border-b">
            <td className="p-1 font">Solver: {task.solver} | Momentum: {task.momentum}</td>
          </tr>
          <tr className="border-b">
            <td className="p-1">Weight Decay: {task.weight_decay} | Num Workers: {task.num_workers}</td>
          </tr>
          <tr className="border-b">
            <td className="p-1">Prefetch Factor: {task.prefetch_factor}</td>
          </tr> */}
          <tr className="border-b">
            <td className="p-1">Data In: {task.dataIn}</td>
          </tr>
          <tr className="border-b">
            <td className="p-1">Output Dir: {task.outputDirectory}</td>
          </tr>
        </tbody>
      </table>
    </div>
  );
}