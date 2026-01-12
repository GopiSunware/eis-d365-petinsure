import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import { Suspense } from 'react';
import './globals.css';
import { Providers } from './providers';
import { Sidebar } from '@/components/layout/Sidebar';
import { Header } from '@/components/layout/Header';
import { ProgressBar } from '@/components/layout/ProgressBar';
import { AuditTracker } from '@/components/AuditTracker';
import { ChatProvider } from '@/components/ChatProvider';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'PetInsure360 Admin Portal',
  description: 'Configuration & Monitoring Portal for PetInsure360 Platform',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <Providers>
          <AuditTracker />
          <Suspense fallback={null}>
            <ProgressBar />
          </Suspense>
          <div className="flex h-screen overflow-hidden bg-slate-50">
            <Sidebar />
            <div className="flex flex-col flex-1 overflow-hidden">
              <Header />
              <ChatProvider>
                {children}
              </ChatProvider>
            </div>
          </div>
        </Providers>
      </body>
    </html>
  );
}
