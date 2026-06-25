import { AgentList } from "@/components/agents/AgentList";

export default function DashboardPage() {
  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950">
      {/* Header */}
      <header className="border-b border-gray-200 bg-white dark:border-gray-800 dark:bg-gray-900">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-6">
          <div className="flex items-center gap-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand-600">
              <span className="text-sm font-bold text-white">O</span>
            </div>
            <span className="text-lg font-semibold text-gray-900 dark:text-white">
              Overseer AI
            </span>
          </div>
          <nav className="flex items-center gap-6 text-sm font-medium text-gray-600 dark:text-gray-400">
            <a href="/dashboard" className="text-brand-600 dark:text-brand-400">
              Dashboard
            </a>
            <a href="/dashboard/sessions" className="hover:text-gray-900 dark:hover:text-white">
              Sessions
            </a>
            <a href="/dashboard/calls" className="hover:text-gray-900 dark:hover:text-white">
              Calls
            </a>
          </nav>
        </div>
      </header>

      {/* Main content */}
      <main className="mx-auto max-w-7xl px-6 py-10">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Dashboard</h1>
          <p className="mt-2 text-gray-600 dark:text-gray-400">
            Manage your AI agents, sessions, and calls.
          </p>
        </div>

        {/* Stats */}
        <div className="mb-10 grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {[
            { label: "Total Agents", value: "—", color: "bg-blue-50 text-blue-700" },
            { label: "Active Sessions", value: "—", color: "bg-green-50 text-green-700" },
            { label: "Calls Today", value: "—", color: "bg-purple-50 text-purple-700" },
            { label: "Messages Sent", value: "—", color: "bg-orange-50 text-orange-700" },
          ].map((stat) => (
            <div
              key={stat.label}
              className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm dark:border-gray-800 dark:bg-gray-900"
            >
              <p className="text-sm font-medium text-gray-500 dark:text-gray-400">{stat.label}</p>
              <p className="mt-2 text-3xl font-bold text-gray-900 dark:text-white">{stat.value}</p>
            </div>
          ))}
        </div>

        {/* Agents section */}
        <section>
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">Agents</h2>
            <a
              href="/dashboard/agents/new"
              className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-700"
            >
              + New Agent
            </a>
          </div>
          <AgentList />
        </section>
      </main>
    </div>
  );
}
