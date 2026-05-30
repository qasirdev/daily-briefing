export default function Home() {
  return (
    <main className="mx-auto flex min-h-full w-full max-w-3xl flex-col gap-6 px-6 py-16">
      <header>
        <p className="text-sm font-medium uppercase tracking-wide text-briefing-primary">
          AI Daily Briefing Assistant
        </p>
        <h1 className="mt-2 text-4xl font-semibold tracking-tight text-foreground">
          Daily Briefing
        </h1>
      </header>

      <section
        className="rounded-xl border border-black/10 bg-white p-6 shadow-sm dark:border-white/10 dark:bg-zinc-950"
        aria-label="Briefing dashboard placeholder"
      >
        <p className="text-lg text-zinc-600 dark:text-zinc-300">
          Your personalized briefing will appear here once agent orchestration is
          connected in MVP 2.
        </p>
      </section>
    </main>
  );
}
