"use client";

/**
 * Agents dashboard page - protected route example.
 */

import { useAuth } from '@/lib/auth/auth-context';
import { Button } from '@/components/ui/button';

export default function AgentsPage() {
  const { user, logout } = useAuth();

  return (
    <div className="container mx-auto p-8">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold mb-2">Agents Dashboard</h1>
          <p className="text-muted-foreground">
            Welcome back, {user?.name}!
          </p>
        </div>
        <Button onClick={logout} variant="outline">
          Logout
        </Button>
      </div>

      <div className="bg-card border border-border rounded-lg p-8">
        <h2 className="text-xl font-semibold mb-4">Your Profile</h2>
        <div className="space-y-2">
          <p><strong>Email:</strong> {user?.email}</p>
          <p><strong>User ID:</strong> {user?.user_id}</p>
          <p><strong>Subscription:</strong> {user?.subscription_tier}</p>
        </div>
      </div>

      <div className="mt-8 bg-muted/50 border border-border rounded-lg p-6">
        <h3 className="text-lg font-semibold mb-2">🎉 Authentication Working!</h3>
        <p className="text-muted-foreground">
          This page is protected. You can only see this because you're authenticated.
          Try logging out and accessing this page - you'll be redirected to login.
        </p>
      </div>
    </div>
  );
}
