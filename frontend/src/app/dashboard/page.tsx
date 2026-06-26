import type { Metadata } from "next";
import { AgentList } from "@/components/agents/AgentList";

export const metadata: Metadata = {
  title: "Dashboard",
};

export default function DashboardPage() {
  return (
    <>
      {/* Page header */}
      <div className="mb-8">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Dashboard</h2>
        <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
          Manage your AI agents, sessions, and calls.
        </p>
      </div>

      {/* Stats */}
      <div className="mb-10 grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
        {[
          { label: "Total Agents", value: "—", accent: "text-brand-600" },
          { label: "Active Sessions", value: "—", accent: "text-green-600" },
          { label: "Calls Today", value: "—", accent: "text-purple-600" },
          { label: "Messages Sent", value: "—", accent: "text-orange-600" },
        ].map((stat) => (
          <div
            key={stat.label}
            className="rounded-card border border-gray-200 bg-surface p-6 shadow-card dark:border-gray-800 dark:bg-surface-dark-muted"
          >
            <p className="text-xs font-medium uppercase tracking-wide text-gray-500 dark:text-gray-400">
              {stat.label}
            </p>
            <p className={`mt-2 text-3xl font-bold ${stat.accent}`}>{stat.value}</p>
          </div>
        ))}
      </div>

      {/* Agents section */}
      <section>
        <div className="mb-4 flex items-center justify-between">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Agents</h3>
          <a
            href="/dashboard/agents/new"
            className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-semibold text-white transition-colors hover:bg-brand-700"
          >
            + New Agent
          </a>
        </div>
        <AgentList />
      </section>
    </>
  );
}
