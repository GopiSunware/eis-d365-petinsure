'use client';

import { usePathname } from 'next/navigation';
import { Bell, Search, ChevronRight, Home } from 'lucide-react';
import Link from 'next/link';

const pathLabels: Record<string, string> = {
  '/': 'Dashboard',
  '/ai-config': 'AI Settings',
  '/claims-rules': 'Claims Rules',
  '/policy-config': 'Policy Configuration',
  '/rating-config': 'Rating Factors',
  '/costs': 'Cost Monitor',
  '/audit': 'Audit Logs',
  '/approvals': 'Approvals',
  '/users': 'User Management',
};

export function Header() {
  const pathname = usePathname();

  const getBreadcrumbs = () => {
    const paths = pathname.split('/').filter(Boolean);
    const crumbs = [{ label: 'Home', href: '/' }];

    if (paths.length > 0) {
      let currentPath = '';
      paths.forEach((path) => {
        currentPath += `/${path}`;
        const label = pathLabels[currentPath] || path.charAt(0).toUpperCase() + path.slice(1);
        crumbs.push({ label, href: currentPath });
      });
    }

    return crumbs;
  };

  const breadcrumbs = getBreadcrumbs();
  const currentPage = pathLabels[pathname] || 'Dashboard';

  return (
    <header className="bg-white border-b border-slate-200">
      <div className="flex items-center justify-between h-16 px-6">
        {/* Breadcrumb */}
        <div className="flex items-center">
          <nav className="flex items-center space-x-1 text-sm">
            {breadcrumbs.map((crumb, index) => (
              <div key={crumb.href} className="flex items-center">
                {index > 0 && (
                  <ChevronRight className="w-4 h-4 text-slate-400 mx-1" />
                )}
                {index === 0 ? (
                  <Link
                    href={crumb.href}
                    className="text-slate-500 hover:text-slate-700"
                  >
                    <Home className="w-4 h-4" />
                  </Link>
                ) : index === breadcrumbs.length - 1 ? (
                  <span className="text-slate-900 font-medium">
                    {crumb.label}
                  </span>
                ) : (
                  <Link
                    href={crumb.href}
                    className="text-slate-500 hover:text-slate-700"
                  >
                    {crumb.label}
                  </Link>
                )}
              </div>
            ))}
          </nav>
        </div>

        {/* Right side */}
        <div className="flex items-center space-x-4">
          {/* Search */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <input
              type="text"
              placeholder="Search..."
              className="w-64 pl-10 pr-4 py-2 text-sm bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            />
          </div>

          {/* Notifications */}
          <button className="relative p-2 text-slate-500 hover:text-slate-700 hover:bg-slate-100 rounded-lg transition-colors">
            <Bell className="w-5 h-5" />
            <span className="absolute top-1 right-1 w-2 h-2 bg-danger-500 rounded-full"></span>
          </button>
        </div>
      </div>
    </header>
  );
}
