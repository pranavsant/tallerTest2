import Link from "next/link";

export default function HomePage() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center px-6 py-24">
      <div className="mx-auto max-w-3xl text-center">
        {/* Badge */}
        <span className="mb-6 inline-flex items-center rounded-full bg-brand-100 px-4 py-1.5 text-sm font-medium text-brand-700 dark:bg-brand-900/30 dark:text-brand-300">
          Production Ready
        </span>

        {/* Heading */}
        <h1 className="mb-6 text-5xl font-bold tracking-tight text-gray-900 dark:text-white sm:text-6xl">
          Overseer{" "}
          <span className="bg-gradient-to-r from-brand-600 to-purple-600 bg-clip-text text-transparent">
            AI
          </span>
        </h1>

        {/* Sub-heading */}
        <p className="mb-10 text-xl leading-relaxed text-gray-600 dark:text-gray-400">
          AI-powered oversight and monitoring platform. Real-time voice and text agent
          interactions, live WebSocket streaming, and telephony integrations — all in one
          production-ready stack.
        </p>

        {/* CTA buttons */}
        <div className="flex flex-col items-center gap-4 sm:flex-row sm:justify-center">
          <Link
            href="/dashboard"
            className="inline-flex h-12 items-center justify-center rounded-lg bg-brand-600 px-8 text-sm font-semibold text-white shadow-md transition-all hover:bg-brand-700 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-600"
          >
            Open Dashboard
          </Link>
          <a
            href="http://localhost:8000/docs"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex h-12 items-center justify-center rounded-lg border border-gray-300 bg-white px-8 text-sm font-semibold text-gray-700 shadow-sm transition-all hover:bg-gray-50 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-200 dark:hover:bg-gray-800"
          >
            API Docs →
          </a>
        </div>

        {/* Tech badges */}
        <div className="mt-16 flex flex-wrap justify-center gap-3">
          {[
            "Next.js 14",
            "FastAPI",
            "Supabase",
            "Tailwind CSS",
            "TypeScript",
            "Python 3.11",
            "WebSockets",
            "Twilio",
            "ElevenLabs",
            "PostgreSQL",
            "Docker",
          ].map((tech) => (
            <span
              key={tech}
              className="rounded-full border border-gray-200 bg-white px-4 py-1.5 text-xs font-medium text-gray-600 shadow-sm dark:border-gray-700 dark:bg-gray-900 dark:text-gray-400"
            >
              {tech}
            </span>
          ))}
        </div>
      </div>
    </main>
  );
}
