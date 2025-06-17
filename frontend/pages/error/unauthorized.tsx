import { useRouter } from 'next/router';

export default function UnauthorizedError() {
  const router = useRouter();

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100">
      <div className="bg-white p-8 rounded-lg shadow-md max-w-md w-full">
        <h1 className="text-2xl font-bold text-red-600 mb-4">Access Denied</h1>
        <p className="text-gray-600 mb-6">
          Sorry, you don't have permission to access this resource. This could be due to:
        </p>
        <ul className="list-disc list-inside text-gray-600 mb-6">
          <li>Invalid origin domain</li>
          <li>Missing or invalid authentication</li>
          <li>Insufficient permissions</li>
        </ul>
        <button
          onClick={() => router.push('/')}
          className="w-full bg-blue-500 text-white py-2 px-4 rounded hover:bg-blue-600 transition-colors"
        >
          Return to Home
        </button>
      </div>
    </div>
  );
} 