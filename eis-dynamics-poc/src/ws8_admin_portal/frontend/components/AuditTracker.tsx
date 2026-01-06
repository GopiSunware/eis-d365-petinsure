'use client';

import { useEffect, useRef } from 'react';
import { usePathname } from 'next/navigation';
import { auditApi } from '@/lib/api';

/**
 * Component that automatically logs page views when navigation occurs.
 * Place this in the layout to track all page visits.
 */
export function AuditTracker() {
  const pathname = usePathname();
  const lastLoggedPath = useRef<string | null>(null);

  useEffect(() => {
    // Prevent duplicate logging for same path
    if (lastLoggedPath.current === pathname) return;
    lastLoggedPath.current = pathname;

    // Don't log login page or if no token (not logged in)
    if (pathname === '/login') return;
    const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;
    if (!token) return;

    // Map pathname to friendly page name
    const pageNames: Record<string, string> = {
      '/': 'Dashboard',
      '/ai-config': 'AI Configuration',
      '/policy-config': 'Policy Configuration',
      '/rating-config': 'Rating Configuration',
      '/claims-rules': 'Claims Rules',
      '/approvals': 'Approvals',
      '/users': 'User Management',
      '/audit': 'Audit Logs',
      '/costs': 'Cost Monitoring',
    };

    const pageName = pageNames[pathname] || pathname;

    auditApi.logEvent({
      event_type: 'page_view',
      page: pageName,
      action: 'navigate',
      entity_type: 'page',
      entity_id: pathname,
    });
  }, [pathname]);

  return null; // This component doesn't render anything
}
