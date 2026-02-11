import Link from "next/link";

import { Switch } from "@/components/ui/switch";

export default function PricingPage() {
  return (
    <div className="mx-auto max-w-6xl px-4 py-12">
      <h1 className="text-3xl font-semibold tracking-tight">Pricing</h1>
      <p className="mt-2 text-sm text-muted-foreground">
        Choose a plan that matches how you build.
      </p>

      <div className="mt-8 flex items-center gap-3">
        <span className="text-sm">Monthly</span>
        <Switch />
        <span className="text-sm">Annual</span>
      </div>

      <div className="mt-8 grid grid-cols-1 gap-4 md:grid-cols-3">
        {["Free", "Pro", "Max"].map((plan) => (
          <div key={plan} className="rounded-xl border bg-card p-6">
            <div className="text-lg font-semibold">{plan}</div>
            <div className="mt-2 text-sm text-muted-foreground">
              Plan details will be finalized soon.
            </div>
            <div className="mt-5">
              <Link
                href="/signup"
                className="inline-flex h-10 items-center justify-center rounded-md bg-primary px-4 text-sm font-medium text-primary-foreground"
              >
                Get Started
              </Link>
            </div>
          </div>
        ))}
      </div>

      <div className="mt-12">
        <h2 className="text-xl font-semibold">Feature matrix</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          A high-level comparison of included features.
        </p>

        <div className="mt-4 overflow-x-auto rounded-xl border">
          <table className="w-full text-left text-sm">
            <thead className="bg-muted">
              <tr>
                <th className="p-3">Feature</th>
                <th className="p-3">Free</th>
                <th className="p-3">Pro</th>
                <th className="p-3">Max</th>
              </tr>
            </thead>
            <tbody>
              {["Feature A", "Feature B", "Feature C"].map((f) => (
                <tr key={f} className="border-t">
                  <td className="p-3">{f}</td>
                  <td className="p-3">✓</td>
                  <td className="p-3">✓</td>
                  <td className="p-3">✓</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="mt-12">
        <h2 className="text-xl font-semibold">FAQ</h2>
        <div className="mt-4 space-y-3">
          {["Billing", "Upgrading", "Cancelation"].map((q) => (
            <details key={q} className="rounded-lg border bg-card px-4 py-3">
              <summary className="cursor-pointer text-sm font-medium">
                {q} (placeholder)
              </summary>
              <p className="mt-2 text-sm text-muted-foreground">
                This answer is being refined as the product ships.
              </p>
            </details>
          ))}
        </div>
      </div>

      <div className="mt-16 rounded-2xl bg-gradient-to-br from-muted to-background p-10">
        <div className="text-2xl font-semibold">Start building with Atoms</div>
        <p className="mt-2 text-sm text-muted-foreground">
          Final CTA section per UI docs.
        </p>
        <div className="mt-5">
          <Link
            href="/signup"
            className="inline-flex h-10 items-center justify-center rounded-md bg-primary px-5 text-sm font-medium text-primary-foreground"
          >
            Try for free
          </Link>
        </div>
      </div>
    </div>
  );
}
