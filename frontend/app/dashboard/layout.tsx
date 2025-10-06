"use client";

/**
 * Dashboard layout with authentication protection.
 * All routes under /dashboard require authentication.
 */

import { ProtectedRoute } from '@/components/auth/protected-route';

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-background">
        {/* Dashboard layout structure */}
        {children}
      </div>
    </ProtectedRoute>
  );
}
