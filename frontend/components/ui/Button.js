export default function Button({ children, variant = 'default', className = '', ...props }) {
  const baseStyles = 'px-4 py-2 rounded-md font-medium text-sm focus:outline-none focus:ring-2 focus:ring-offset-2';
  
  const variants = {
    default: 'bg-blue-600 text-white hover:bg-blue-700 focus:ring-blue-500',
    secondary: 'bg-gray-100 text-gray-700 hover:bg-gray-200 focus:ring-gray-500',
    danger: 'bg-red-600 text-white hover:bg-red-700 focus:ring-red-500'
  };

  const variantStyle = variants[variant] || variants.default;
  
  return (
    <button
      className={`${baseStyles} ${variantStyle} ${className}`}
      {...props}
    >
      {children}
    </button>
  );
} 