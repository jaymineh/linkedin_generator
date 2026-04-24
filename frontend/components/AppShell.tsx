import Link from "next/link";
import { UserButton } from "@clerk/clerk-react";

import { isClerkEnabled } from "../lib/auth";
import { useTheme } from "../lib/theme";

function ThemeToggle() {
  const { theme, toggleTheme } = useTheme();
  const isDark = theme === "dark";
  return (
    <button
      type="button"
      onClick={toggleTheme}
      className="inline-flex items-center gap-2 rounded-full border border-slate-200/80 bg-white/70 px-3 py-1.5 text-xs font-medium text-slate-700 shadow-sm backdrop-blur-sm transition hover:bg-white dark:border-slate-600 dark:bg-slate-800/70 dark:text-slate-200 dark:hover:bg-slate-800"
      aria-label={isDark ? "Switch to light mode" : "Switch to dark mode"}
    >
      <span className="tabular-nums">{isDark ? "Dark" : "Light"}</span>
      <span className="text-base leading-none">{isDark ? "☾" : "☀"}</span>
    </button>
  );
}

type NavKey = "generator" | "history";

export default function AppShell({
  children,
  active,
  helpHref = "https://github.com",
}: {
  children: React.ReactNode;
  active: NavKey;
  helpHref?: string;
}) {
  const clerkOn = isClerkEnabled();

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-indigo-50/60 text-slate-900 dark:from-slate-950 dark:via-slate-900 dark:to-indigo-950/40 dark:text-slate-100">
      <header className="sticky top-0 z-20 border-b border-slate-200/70 bg-white/75 backdrop-blur-lg dark:border-slate-800/80 dark:bg-slate-950/75">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-4 py-3 sm:px-6">
          <Link
            href="/"
            className="text-sm font-bold tracking-tight text-slate-900 transition hover:text-indigo-600 dark:text-white dark:hover:text-indigo-300 sm:text-base"
          >
            LinkedIn Post Generator
          </Link>
          <nav className="flex items-center gap-2 sm:gap-4">
            <Link
              href="/"
              className={`rounded-full px-3 py-1.5 text-xs font-medium transition sm:text-sm ${
                active === "generator"
                  ? "bg-indigo-600 text-white shadow-md shadow-indigo-600/30"
                  : "text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800"
              }`}
            >
              Generate
            </Link>
            <Link
              href="/history/"
              className={`rounded-full px-3 py-1.5 text-xs font-medium transition sm:text-sm ${
                active === "history"
                  ? "bg-indigo-600 text-white shadow-md shadow-indigo-600/30"
                  : "text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800"
              }`}
            >
              History
            </Link>
            <a
              href={helpHref}
              target="_blank"
              rel="noreferrer"
              className="hidden text-xs font-medium text-slate-500 hover:text-indigo-600 dark:text-slate-400 dark:hover:text-indigo-300 sm:inline sm:text-sm"
            >
              Help
            </a>
            <ThemeToggle />
            {clerkOn ? (
              <div className="pl-1">
                <UserButton
                  afterSignOutUrl="/"
                  appearance={{
                    elements: {
                      avatarBox: "h-8 w-8 ring-2 ring-indigo-500/30",
                    },
                  }}
                />
              </div>
            ) : null}
          </nav>
        </div>
      </header>
      <main>{children}</main>
    </div>
  );
}
