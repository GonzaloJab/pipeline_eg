import { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/router';
import { 
  Home,
  Database,
  Settings,
  BarChart2,
  Menu,
  X,
  FlaskConical,
  PanelLeftClose,
  PanelLeftOpen,
  LineChart
} from 'lucide-react';

export default function Layout({ children }) {
  const router = useRouter();
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const MLFLOW_URL = process.env.NEXT_PUBLIC_MLFLOW_URL || 'http://172.26.20.10:8080/';

  const navigation = [
    { name: 'Home', href: '/', icon: Home },
    { name: '+Training', href: '/training', icon: BarChart2 },
    { name: '+Testing', href: '/testing', icon: FlaskConical },
    { 
      name: 'MLflow', 
      href: MLFLOW_URL, 
      icon: LineChart,
      external: true 
    },
    { name: 'Database', href: '/database', icon: Database },
    { name: 'Settings', href: '/settings', icon: Settings },
  ];

  const isActive = (path) => router.pathname === path;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Mobile menu button - only visible on small screens */}
      <button
        className="fixed top-4 left-4 z-50 lg:hidden"
        onClick={() => setIsSidebarOpen(!isSidebarOpen)}
      >
        {isSidebarOpen ? (
          <X className="h-6 w-6" />
        ) : (
          <Menu className="h-6 w-6" />
        )}
      </button>

      {/* Sidebar */}
      <div
        className={`fixed inset-y-0 left-0 z-40 w-64 bg-white transform transition-transform duration-300 ease-in-out ${
          isSidebarOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div className="flex flex-col h-full">
          {/* Logo */}
          <div className="flex items-center justify-center h-16 px-4">
            <img src="/logo-black.svg" alt="Logo" className="h-8 w-auto" />
          </div>

          {/* Navigation */}
          <nav className="flex-1 px-4 space-y-1">
            {navigation.map((item) => {
              const Icon = item.icon;
              const LinkComponent = item.external ? 'a' : Link;
              const linkProps = item.external ? {
                href: item.href,
                target: "_blank",
                rel: "noopener noreferrer"
              } : {
                href: item.href
              };
              
              return (
                <LinkComponent
                  key={item.name}
                  {...linkProps}
                  className={`flex items-center px-4 py-3 text-sm font-medium rounded-md transition-colors ${
                    isActive(item.href)
                      ? 'bg-gray-100 text-gray-900'
                      : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                  }`}
                >
                  <Icon className="h-5 w-5 mr-3" />
                  {item.name}
                </LinkComponent>
              );
            })}
          </nav>
        </div>
      </div>

      {/* Toggle sidebar button - visible on all screen sizes */}
      <button
        className={`fixed bottom-4 ${isSidebarOpen ? 'left-56' : 'left-4'} z-50 p-2 bg-white rounded-full shadow-lg transition-all duration-300 hover:bg-gray-100`}
        onClick={() => setIsSidebarOpen(!isSidebarOpen)}
      >
        {isSidebarOpen ? (
          <PanelLeftClose className="h-5 w-5" />
        ) : (
          <PanelLeftOpen className="h-5 w-5" />
        )}
      </button>

      {/* Main content */}
      <div 
        className={`transition-all duration-300 ${
          isSidebarOpen ? 'pl-64' : 'pl-0'
        }`}
      >
        <main className="p-4 mx-auto max-w-7xl">
          <div className="max-w-[1600px] mx-auto">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
} 