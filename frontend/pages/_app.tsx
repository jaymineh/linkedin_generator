import type { AppProps } from "next/app";
import { DM_Sans } from "next/font/google";
import { useEffect } from "react";
import { useRouter } from "next/router";

import "../styles/globals.css";
import { AuthGate, ClerkRoot } from "../lib/auth";
import { ThemeProvider } from "../lib/theme";
import { getAppInsights, trackPageView } from "../lib/telemetry";

const dmSans = DM_Sans({
  subsets: ["latin"],
  variable: "--font-dm-sans",
  display: "swap",
});

function TelemetryBridge() {
  const router = useRouter();

  useEffect(() => {
    getAppInsights();

    const handleRouteChange = (url: string) => {
      trackPageView(url, typeof window !== "undefined" ? window.location.origin + url : url);
    };

    handleRouteChange(router.asPath);
    router.events.on("routeChangeComplete", handleRouteChange);

    return () => {
      router.events.off("routeChangeComplete", handleRouteChange);
    };
  }, [router]);

  return null;
}

export default function App({ Component, pageProps }: AppProps) {
  return (
    <div className={`${dmSans.variable} min-h-screen font-sans antialiased`}>
      <ThemeProvider>
        <ClerkRoot>
          <TelemetryBridge />
          <AuthGate>
            <Component {...pageProps} />
          </AuthGate>
        </ClerkRoot>
      </ThemeProvider>
    </div>
  );
}
