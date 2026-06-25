import type { Agent } from "@/lib/api";
import { cn, formatDate } from "@/lib/utils";

const STATUS_STYLES: Record<string, string> = {
  idle: "bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300",
  active: "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400",
  busy: "bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400",
  offline: "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400",
  suspended: "bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400",
};

interface AgentCardProps {
  agent: Agent;
}

export function AgentCard({ agent }: AgentCardProps) {
  return (
    <article className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm transition-shadow hover:shadow-md dark:border-gray-800 dark:bg-gray-900">
      <div className="mb-3 flex items-start justify-between">
        <h3 className="font-semibold text-gray-900 dark:text-white">{agent.name}</h3>
        <span
          className={cn(
            "rounded-full px-2.5 py-0.5 text-xs font-medium capitalize",
            STATUS_STYLES[agent.status] ?? STATUS_STYLES.offline,
          )}
        >
          {agent.status}
        </span>
      </div>

      <p className="mb-4 line-clamp-2 text-sm text-gray-500 dark:text-gray-400">
        {agent.system_prompt}
      </p>

      <div className="flex items-center justify-between text-xs text-gray-400 dark:text-gray-600">
        <span>Voice: {agent.voice_id.slice(0, 8)}…</span>
        <span>{formatDate(agent.created_at)}</span>
      </div>

      <div className="mt-4 flex gap-2">
        <a
          href={`/dashboard/agents/${agent.agent_id}`}
          className="flex-1 rounded-lg border border-gray-200 bg-white px-3 py-1.5 text-center text-xs font-medium text-gray-700 hover:bg-gray-50 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-300"
        >
          View
        </a>
        <a
          href={`/dashboard/sessions/new?agent_id=${agent.agent_id}`}
          className="flex-1 rounded-lg bg-brand-600 px-3 py-1.5 text-center text-xs font-medium text-white hover:bg-brand-700"
        >
          Start Session
        </a>
      </div>
    </article>
  );
}
