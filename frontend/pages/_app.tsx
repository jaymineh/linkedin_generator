import type { AppProps } from "next/app";
import { useEffect } from "react";
import { useRouter } from "next/router";

import "../styles/globals.css";
import { getAppInsights, trackPageView } from "../lib/telemetry";

export default function App({ Component, pageProps }: AppProps) {
  const router = useRouter();

  useEffect(() => {
    getAppInsights();

    const handleRouteChange = (url: string) => {
      trackPageView(url, window.location.origin + url);
    };

    handleRouteChange(router.asPath);
    router.events.on("routeChangeComplete", handleRouteChange);

    return () => {
      router.events.off("routeChangeComplete", handleRouteChange);
    };
  }, [router]);

  return <Component {...pageProps} />;
}
