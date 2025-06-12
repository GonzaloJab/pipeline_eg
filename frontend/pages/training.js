import TrainingForm from '../components/TrainingForm';

export default function Training() {
  return (
    <div className="max-w-7xl mx-auto">
      <h1 className="text-3xl font-bold mb-8">Training Configuration</h1>
      <TrainingForm
        onSuccess={() => {
          // You can add success handling here if needed
          console.log('Training task created successfully');
        }}
      />
    </div>
  );
} 