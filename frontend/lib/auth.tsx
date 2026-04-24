import { ClerkProvider, SignedIn, SignedOut, SignInButton, SignUpButton } from "@clerk/clerk-react";
import type { ReactNode } from "react";

const publishableKey = process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY ?? "";

export function isClerkEnabled(): boolean {
  return Boolean(publishableKey);
}

export function ClerkRoot({ children }: { children: ReactNode }) {
  if (!publishableKey) {
    return <>{children}</>;
  }
  return <ClerkProvider publishableKey={publishableKey}>{children}</ClerkProvider>;
}

export function AuthGate({ children }: { children: ReactNode }) {
  if (!publishableKey) {
    return <>{children}</>;
  }

  return (
    <>
      <SignedIn>{children}</SignedIn>
      <SignedOut>
        <div className="flex min-h-screen flex-col items-center justify-center bg-gradient-to-br from-slate-50 via-indigo-50/80 to-violet-100 px-6 py-16 dark:from-slate-950 dark:via-slate-900 dark:to-indigo-950">
          <div className="max-w-md rounded-3xl border border-white/60 bg-white/80 p-10 text-center shadow-xl shadow-indigo-500/10 backdrop-blur-md dark:border-white/10 dark:bg-slate-900/80 dark:shadow-indigo-950/40">
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-indigo-600 dark:text-indigo-300">
              LinkedIn Post Generator
            </p>
            <h1 className="mt-3 text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
              Sign in to continue
            </h1>
            <p className="mt-3 text-sm leading-relaxed text-slate-600 dark:text-slate-300">
              Create posts, learn your writing style, and keep history synced to your account.
            </p>
            <div className="mt-8 flex flex-col gap-3 sm:flex-row sm:justify-center">
              <SignInButton mode="modal">
                <button
                  type="button"
                  className="rounded-xl bg-indigo-600 px-5 py-2.5 text-sm font-semibold text-white shadow-lg shadow-indigo-600/25 transition hover:bg-indigo-500"
                >
                  Sign in
                </button>
              </SignInButton>
              <SignUpButton mode="modal">
                <button
                  type="button"
                  className="rounded-xl border border-slate-200 bg-white px-5 py-2.5 text-sm font-semibold text-slate-800 transition hover:bg-slate-50 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100 dark:hover:bg-slate-700"
                >
                  Create account
                </button>
              </SignUpButton>
            </div>
          </div>
        </div>
      </SignedOut>
    </>
  );
}
