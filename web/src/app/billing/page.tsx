"use client";

import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { api, Plan, Subscription, Usage } from "@/lib/api";
import { Navbar } from "@/components/layout/navbar";
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  Check,
  Building,
  Loader2,
} from "lucide-react";

function BillingContent() {
  const { user, loading: authLoading } = useAuth();
  const router = useRouter();
  const searchParams = useSearchParams();
  const [plans, setPlans] = useState<Plan[]>([]);
  const [subscription, setSubscription] = useState<Subscription | null>(null);
  const [usage, setUsage] = useState<Usage | null>(null);
  const [loading, setLoading] = useState(true);
  const [upgrading, setUpgrading] = useState<string | null>(null);
  const [billingCycle, setBillingCycle] = useState<"monthly" | "yearly">("monthly");

  const checkoutSuccess = searchParams.get("success") === "true";

  useEffect(() => {
    if (!authLoading && !user) {
      router.push("/login");
    }
  }, [user, authLoading, router]);

  useEffect(() => {
    if (user) {
      loadBillingData();
    }
  }, [user]);

  const loadBillingData = async () => {
    try {
      const [plansData, subData, usageData] = await Promise.all([
        api.getBillingPlans(),
        api.getSubscription(),
        api.getBillingUsage(),
      ]);
      setPlans(plansData);
      setSubscription(subData);
      setUsage(usageData);
    } catch (err) {
      console.error("Failed to load billing data:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleUpgrade = async (planId: string) => {
    setUpgrading(planId);
    try {
      const response = await api.createCheckout(planId, billingCycle);
      window.location.href = response.checkout_url;
    } catch (err) {
      console.error("Failed to create checkout:", err);
      alert("Failed to start checkout. Please try again.");
    } finally {
      setUpgrading(null);
    }
  };

  const handleCancel = async () => {
    if (!confirm("Are you sure you want to cancel your subscription? You'll lose access to premium features at the end of your billing period.")) {
      return;
    }

    try {
      await api.cancelSubscription();
      await loadBillingData();
    } catch (err) {
      console.error("Failed to cancel subscription:", err);
    }
  };

  const formatPrice = (price: number) => {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
      minimumFractionDigits: 0,
    }).format(price);
  };

  if (authLoading || !user) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950">
      <Navbar />

      <main className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Success Message */}
        {checkoutSuccess && (
          <div className="mb-8 p-4 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-xl">
            <div className="flex items-center gap-3">
              <Check className="h-6 w-6 text-green-600" />
              <div>
                <p className="font-medium text-green-800 dark:text-green-200">
                  Payment successful!
                </p>
                <p className="text-sm text-green-700 dark:text-green-300">
                  Your subscription has been activated. Thank you for upgrading!
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Header */}
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            Billing & Subscription
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Manage your subscription and billing information
          </p>
        </div>

        {/* Current Plan */}
        {subscription && (
          <Card className="mb-8">
            <CardHeader>
              <CardTitle>Current Subscription</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-2xl font-bold text-gray-900 dark:text-white capitalize">
                    {subscription.plan} Plan
                  </p>
                  <p className="text-gray-500 dark:text-gray-400">
                    {subscription.billing_cycle === "yearly" ? "Annual" : "Monthly"} billing
                    {subscription.current_period_end && (
                      <> · Renews {new Date(subscription.current_period_end).toLocaleDateString()}</>
                    )}
                  </p>
                </div>
                <div className="flex items-center gap-3">
                  <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                    subscription.status === "active"
                      ? "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400"
                      : subscription.status === "past_due"
                      ? "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400"
                      : "bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-400"
                  }`}>
                    {subscription.status.replace("_", " ")}
                  </span>
                  <Button variant="outline" onClick={handleCancel}>
                    Cancel
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Billing Cycle Toggle */}
        <div className="flex justify-center mb-8">
          <div className="inline-flex items-center p-1 bg-gray-100 dark:bg-gray-800 rounded-lg">
            <button
              onClick={() => setBillingCycle("monthly")}
              className={`px-4 py-2 text-sm font-medium rounded-md transition-colors ${
                billingCycle === "monthly"
                  ? "bg-white dark:bg-gray-700 text-gray-900 dark:text-white shadow-sm"
                  : "text-gray-600 dark:text-gray-400"
              }`}
            >
              Monthly
            </button>
            <button
              onClick={() => setBillingCycle("yearly")}
              className={`px-4 py-2 text-sm font-medium rounded-md transition-colors ${
                billingCycle === "yearly"
                  ? "bg-white dark:bg-gray-700 text-gray-900 dark:text-white shadow-sm"
                  : "text-gray-600 dark:text-gray-400"
              }`}
            >
              Yearly
              <span className="ml-2 text-xs text-green-600">Save 17%</span>
            </button>
          </div>
        </div>

        {/* Plans Grid */}
        {loading ? (
          <div className="flex justify-center py-12">
            <Loader2 className="h-8 w-8 animate-spin text-primary-600" />
          </div>
        ) : (
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
            {plans.map((plan) => {
              const isCurrentPlan = usage?.plan === plan.id;
              const price = billingCycle === "yearly" ? plan.price_yearly : plan.price_monthly;
              const monthlyPrice = billingCycle === "yearly" ? plan.price_yearly / 12 : plan.price_monthly;

              return (
                <Card
                  key={plan.id}
                  className={`relative ${
                    plan.id === "pro"
                      ? "border-primary-500 dark:border-primary-400 ring-2 ring-primary-500/20"
                      : ""
                  }`}
                >
                  {plan.id === "pro" && (
                    <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                      <span className="px-3 py-1 bg-primary-600 text-white text-xs font-medium rounded-full">
                        Most Popular
                      </span>
                    </div>
                  )}
                  <CardHeader>
                    <CardTitle>{plan.name}</CardTitle>
                    <CardDescription>{plan.description}</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="mb-6">
                      <span className="text-4xl font-bold text-gray-900 dark:text-white">
                        {formatPrice(monthlyPrice)}
                      </span>
                      <span className="text-gray-500 dark:text-gray-400">/mo</span>
                      {billingCycle === "yearly" && plan.price_yearly > 0 && (
                        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                          {formatPrice(price)} billed yearly
                        </p>
                      )}
                    </div>

                    <ul className="space-y-3">
                      <li className="flex items-center gap-2 text-sm">
                        <Check className="h-4 w-4 text-green-500 flex-shrink-0" />
                        <span className="text-gray-600 dark:text-gray-400">
                          {plan.features.max_documents === -1
                            ? "Unlimited"
                            : plan.features.max_documents.toLocaleString()}{" "}
                          documents
                        </span>
                      </li>
                      <li className="flex items-center gap-2 text-sm">
                        <Check className="h-4 w-4 text-green-500 flex-shrink-0" />
                        <span className="text-gray-600 dark:text-gray-400">
                          {plan.features.max_api_calls_per_month === -1
                            ? "Unlimited"
                            : (plan.features.max_api_calls_per_month / 1000).toLocaleString() + "K"}{" "}
                          API calls/mo
                        </span>
                      </li>
                      <li className="flex items-center gap-2 text-sm">
                        <Check className="h-4 w-4 text-green-500 flex-shrink-0" />
                        <span className="text-gray-600 dark:text-gray-400">
                          {plan.features.max_team_members === -1
                            ? "Unlimited"
                            : plan.features.max_team_members}{" "}
                          team members
                        </span>
                      </li>
                      {plan.features.priority_support && (
                        <li className="flex items-center gap-2 text-sm">
                          <Check className="h-4 w-4 text-green-500 flex-shrink-0" />
                          <span className="text-gray-600 dark:text-gray-400">
                            Priority support
                          </span>
                        </li>
                      )}
                      {plan.features.custom_embeddings && (
                        <li className="flex items-center gap-2 text-sm">
                          <Check className="h-4 w-4 text-green-500 flex-shrink-0" />
                          <span className="text-gray-600 dark:text-gray-400">
                            Custom embeddings
                          </span>
                        </li>
                      )}
                      {plan.features.sso && (
                        <li className="flex items-center gap-2 text-sm">
                          <Check className="h-4 w-4 text-green-500 flex-shrink-0" />
                          <span className="text-gray-600 dark:text-gray-400">
                            SSO / SAML
                          </span>
                        </li>
                      )}
                      {plan.features.sla && (
                        <li className="flex items-center gap-2 text-sm">
                          <Check className="h-4 w-4 text-green-500 flex-shrink-0" />
                          <span className="text-gray-600 dark:text-gray-400">
                            {plan.features.sla} SLA
                          </span>
                        </li>
                      )}
                    </ul>
                  </CardContent>
                  <CardFooter>
                    {isCurrentPlan ? (
                      <Button variant="outline" className="w-full" disabled>
                        Current Plan
                      </Button>
                    ) : plan.id === "free" ? (
                      <Button variant="outline" className="w-full" disabled>
                        Free Forever
                      </Button>
                    ) : (
                      <Button
                        className="w-full"
                        variant={plan.id === "pro" ? "primary" : "outline"}
                        onClick={() => handleUpgrade(plan.id)}
                        loading={upgrading === plan.id}
                      >
                        {upgrading === plan.id ? "Processing..." : "Upgrade"}
                      </Button>
                    )}
                  </CardFooter>
                </Card>
              );
            })}
          </div>
        )}

        {/* Enterprise CTA */}
        <Card className="mt-12 bg-gradient-to-r from-gray-900 to-gray-800 dark:from-gray-800 dark:to-gray-900 text-white">
          <CardContent className="p-8">
            <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-6">
              <div>
                <h3 className="text-2xl font-bold mb-2">Need a custom solution?</h3>
                <p className="text-gray-300 max-w-xl">
                  Get dedicated support, custom integrations, SLA guarantees, and
                  volume pricing for your organization.
                </p>
              </div>
              <Button
                variant="secondary"
                size="lg"
                className="flex-shrink-0"
                onClick={() => window.open("mailto:enterprise@docvector.dev")}
              >
                <Building className="h-5 w-5 mr-2" />
                Contact Sales
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* FAQ */}
        <div className="mt-12">
          <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-6">
            Frequently Asked Questions
          </h2>
          <div className="grid gap-4 md:grid-cols-2">
            <Card>
              <CardContent className="p-6">
                <h4 className="font-medium text-gray-900 dark:text-white mb-2">
                  Can I change plans anytime?
                </h4>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Yes! You can upgrade or downgrade your plan at any time. Changes
                  take effect immediately and we&apos;ll prorate the difference.
                </p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-6">
                <h4 className="font-medium text-gray-900 dark:text-white mb-2">
                  What happens if I exceed my limits?
                </h4>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  We&apos;ll notify you when you&apos;re approaching your limits.
                  You can upgrade or we&apos;ll pause usage until the next billing cycle.
                </p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-6">
                <h4 className="font-medium text-gray-900 dark:text-white mb-2">
                  Do you offer refunds?
                </h4>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Yes, we offer a 14-day money-back guarantee. If you&apos;re not
                  satisfied, contact us for a full refund.
                </p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-6">
                <h4 className="font-medium text-gray-900 dark:text-white mb-2">
                  Is my data secure?
                </h4>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Absolutely. We use industry-standard encryption and your data
                  is isolated per organization. SOC 2 compliance coming soon.
                </p>
              </CardContent>
            </Card>
          </div>
        </div>
      </main>
    </div>
  );
}

export default function BillingPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary-600"></div>
      </div>
    }>
      <BillingContent />
    </Suspense>
  );
}
