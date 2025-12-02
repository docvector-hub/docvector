"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { api, Usage } from "@/lib/api";
import { Navbar } from "@/components/layout/navbar";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  Search,
  FileText,
  Users,
  Zap,
  ArrowRight,
  Activity,
} from "lucide-react";
import Link from "next/link";

export default function DashboardPage() {
  const { user, loading: authLoading } = useAuth();
  const router = useRouter();
  const [usage, setUsage] = useState<Usage | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!authLoading && !user) {
      router.push("/login");
    }
  }, [user, authLoading, router]);

  useEffect(() => {
    if (user) {
      api
        .getBillingUsage()
        .then(setUsage)
        .catch(console.error)
        .finally(() => setLoading(false));
    }
  }, [user]);

  if (authLoading || !user) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  const usagePercent = (current: number, limit: number) => {
    if (limit === -1) return 0; // Unlimited
    return Math.min((current / limit) * 100, 100);
  };

  const formatLimit = (limit: number) => {
    if (limit === -1) return "Unlimited";
    return limit.toLocaleString();
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950">
      <Navbar />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Welcome Header */}
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            Welcome back, {user.display_name || user.username}!
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Here&apos;s an overview of your DocVector account
          </p>
        </div>

        {/* Quick Actions */}
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4 mb-8">
          <Link href="/search">
            <Card className="hover:shadow-md transition-shadow cursor-pointer h-full">
              <CardContent className="p-6 flex items-center">
                <div className="h-12 w-12 rounded-xl bg-primary-100 dark:bg-primary-900/30 flex items-center justify-center">
                  <Search className="h-6 w-6 text-primary-600" />
                </div>
                <div className="ml-4">
                  <p className="font-medium text-gray-900 dark:text-white">
                    Search Docs
                  </p>
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    Query your documentation
                  </p>
                </div>
              </CardContent>
            </Card>
          </Link>

          <Link href="/dashboard/sources">
            <Card className="hover:shadow-md transition-shadow cursor-pointer h-full">
              <CardContent className="p-6 flex items-center">
                <div className="h-12 w-12 rounded-xl bg-green-100 dark:bg-green-900/30 flex items-center justify-center">
                  <FileText className="h-6 w-6 text-green-600" />
                </div>
                <div className="ml-4">
                  <p className="font-medium text-gray-900 dark:text-white">
                    Add Sources
                  </p>
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    Index new documentation
                  </p>
                </div>
              </CardContent>
            </Card>
          </Link>

          <Link href="/dashboard/api-keys">
            <Card className="hover:shadow-md transition-shadow cursor-pointer h-full">
              <CardContent className="p-6 flex items-center">
                <div className="h-12 w-12 rounded-xl bg-purple-100 dark:bg-purple-900/30 flex items-center justify-center">
                  <Zap className="h-6 w-6 text-purple-600" />
                </div>
                <div className="ml-4">
                  <p className="font-medium text-gray-900 dark:text-white">
                    API Keys
                  </p>
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    Manage API access
                  </p>
                </div>
              </CardContent>
            </Card>
          </Link>

          <Link href="/billing">
            <Card className="hover:shadow-md transition-shadow cursor-pointer h-full">
              <CardContent className="p-6 flex items-center">
                <div className="h-12 w-12 rounded-xl bg-orange-100 dark:bg-orange-900/30 flex items-center justify-center">
                  <Activity className="h-6 w-6 text-orange-600" />
                </div>
                <div className="ml-4">
                  <p className="font-medium text-gray-900 dark:text-white">
                    Billing
                  </p>
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    Manage subscription
                  </p>
                </div>
              </CardContent>
            </Card>
          </Link>
        </div>

        {/* Usage Stats */}
        <div className="grid gap-6 md:grid-cols-3 mb-8">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">API Calls</CardTitle>
              <CardDescription>This billing period</CardDescription>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded animate-pulse"></div>
              ) : (
                <>
                  <div className="flex items-baseline gap-2">
                    <span className="text-3xl font-bold text-gray-900 dark:text-white">
                      {usage?.api_calls.toLocaleString() || 0}
                    </span>
                    <span className="text-gray-500 dark:text-gray-400">
                      / {formatLimit(usage?.api_calls_limit || 0)}
                    </span>
                  </div>
                  <div className="mt-3 h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-primary-600 rounded-full transition-all"
                      style={{
                        width: `${usagePercent(usage?.api_calls || 0, usage?.api_calls_limit || 1)}%`,
                      }}
                    ></div>
                  </div>
                </>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-base">Documents</CardTitle>
              <CardDescription>Indexed documents</CardDescription>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded animate-pulse"></div>
              ) : (
                <>
                  <div className="flex items-baseline gap-2">
                    <span className="text-3xl font-bold text-gray-900 dark:text-white">
                      {usage?.documents.toLocaleString() || 0}
                    </span>
                    <span className="text-gray-500 dark:text-gray-400">
                      / {formatLimit(usage?.documents_limit || 0)}
                    </span>
                  </div>
                  <div className="mt-3 h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-green-600 rounded-full transition-all"
                      style={{
                        width: `${usagePercent(usage?.documents || 0, usage?.documents_limit || 1)}%`,
                      }}
                    ></div>
                  </div>
                </>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-base">Team Members</CardTitle>
              <CardDescription>Active members</CardDescription>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded animate-pulse"></div>
              ) : (
                <>
                  <div className="flex items-baseline gap-2">
                    <span className="text-3xl font-bold text-gray-900 dark:text-white">
                      {usage?.team_members || 1}
                    </span>
                    <span className="text-gray-500 dark:text-gray-400">
                      / {formatLimit(usage?.team_members_limit || 0)}
                    </span>
                  </div>
                  <div className="mt-3 h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-purple-600 rounded-full transition-all"
                      style={{
                        width: `${usagePercent(usage?.team_members || 1, usage?.team_members_limit || 1)}%`,
                      }}
                    ></div>
                  </div>
                </>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Current Plan */}
        <Card>
          <CardHeader>
            <CardTitle>Current Plan</CardTitle>
            <CardDescription>
              You are on the{" "}
              <span className="font-medium text-gray-900 dark:text-white capitalize">
                {usage?.plan || "Free"}
              </span>{" "}
              plan
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  {usage?.plan === "free"
                    ? "Upgrade to unlock more features and higher limits"
                    : "Manage your subscription and billing"}
                </p>
              </div>
              <Link href="/billing">
                <Button variant="outline">
                  {usage?.plan === "free" ? "Upgrade" : "Manage"}
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Button>
              </Link>
            </div>
          </CardContent>
        </Card>
      </main>
    </div>
  );
}
