'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  LayoutDashboard,
  Bot,
  FileCheck,
  Shield,
  Calculator,
  DollarSign,
  ClipboardList,
  Users,
  Clock,
  Settings,
  ChevronDown,
} from 'lucide-react';
import { useState } from 'react';
import { clsx } from 'clsx';

interface NavItem {
  label: string;
  href: string;
  icon: React.ElementType;
  badge?: number;
  children?: NavItem[];
}

const navigation: NavItem[] = [
  {
    label: 'Dashboard',
    href: '/',
    icon: LayoutDashboard,
  },
  {
    label: 'Configuration',
    href: '/config',
    icon: Settings,
    children: [
      { label: 'AI Settings', href: '/ai-config', icon: Bot },
      { label: 'Claims Rules', href: '/claims-rules', icon: FileCheck },
      { label: 'Policy Config', href: '/policy-config', icon: Shield },
      { label: 'Rating Factors', href: '/rating-config', icon: Calculator },
    ],
  },
  {
    label: 'Cost Monitor',
    href: '/costs',
    icon: DollarSign,
  },
  {
    label: 'Audit Logs',
    href: '/audit',
    icon: ClipboardList,
  },
  {
    label: 'Approvals',
    href: '/approvals',
    icon: Clock,
  },
  {
    label: 'Users',
    href: '/users',
    icon: Users,
  },
];

function NavLink({
  item,
  depth = 0,
}: {
  item: NavItem;
  depth?: number;
}) {
  const pathname = usePathname();
  const [isOpen, setIsOpen] = useState(
    item.children?.some((child) => pathname === child.href) ?? false
  );

  const isActive = pathname === item.href;
  const hasChildren = item.children && item.children.length > 0;

  const Icon = item.icon;

  if (hasChildren) {
    return (
      <div>
        <button
          onClick={() => setIsOpen(!isOpen)}
          className={clsx(
            'flex items-center w-full px-3 py-2.5 text-sm font-medium rounded-lg transition-colors',
            'text-slate-300 hover:bg-sidebar-hover hover:text-white'
          )}
        >
          <Icon className="w-5 h-5 mr-3" />
          <span className="flex-1 text-left">{item.label}</span>
          <ChevronDown
            className={clsx(
              'w-4 h-4 transition-transform',
              isOpen && 'rotate-180'
            )}
          />
        </button>
        {isOpen && (
          <div className="mt-1 ml-4 space-y-1">
            {item.children?.map((child) => (
              <NavLink key={child.href} item={child} depth={depth + 1} />
            ))}
          </div>
        )}
      </div>
    );
  }

  return (
    <Link
      href={item.href}
      className={clsx(
        'flex items-center px-3 py-2.5 text-sm font-medium rounded-lg transition-colors',
        isActive
          ? 'bg-primary-600 text-white'
          : 'text-slate-300 hover:bg-sidebar-hover hover:text-white',
        depth > 0 && 'ml-2'
      )}
    >
      <Icon className="w-5 h-5 mr-3" />
      <span className="flex-1">{item.label}</span>
      {item.badge !== undefined && item.badge > 0 && (
        <span className="px-2 py-0.5 text-xs font-medium bg-primary-500 text-white rounded-full">
          {item.badge}
        </span>
      )}
    </Link>
  );
}

export function Sidebar() {
  return (
    <aside className="w-64 bg-sidebar flex flex-col">
      {/* Logo */}
      <div className="flex items-center h-16 px-4 border-b border-slate-700">
        <div className="flex items-center">
          <div className="w-8 h-8 bg-primary-500 rounded-lg flex items-center justify-center">
            <span className="text-white font-bold text-lg">E</span>
          </div>
          <div className="ml-3">
            <h1 className="text-white font-semibold text-lg">EIS Admin</h1>
            <p className="text-slate-400 text-xs">Pet Insurance Platform</p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto scrollbar-thin">
        {navigation.map((item) => (
          <NavLink key={item.href} item={item} />
        ))}
      </nav>

      {/* Footer */}
      <div className="p-4 border-t border-slate-700">
        <div className="flex items-center">
          <div className="w-8 h-8 bg-slate-600 rounded-full flex items-center justify-center">
            <span className="text-white text-sm font-medium">A</span>
          </div>
          <div className="ml-3">
            <p className="text-white text-sm font-medium">Admin User</p>
            <p className="text-slate-400 text-xs">admin@example.com</p>
          </div>
        </div>
      </div>
    </aside>
  );
}
