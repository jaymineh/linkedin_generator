import { ApplicationInsights } from "@microsoft/applicationinsights-web";

type EventProperties = Record<string, string | boolean | undefined>;
type EventMeasurements = Record<string, number | undefined>;

const connectionString = process.env.NEXT_PUBLIC_APPLICATIONINSIGHTS_CONNECTION_STRING;

let appInsightsInstance: ApplicationInsights | null = null;

function sanitizeProperties(properties: EventProperties = {}): Record<string, string | boolean> {
  return Object.fromEntries(Object.entries(properties).filter(([, value]) => value !== undefined)) as Record<
    string,
    string | boolean
  >;
}

function sanitizeMeasurements(measurements: EventMeasurements = {}): Record<string, number> {
  return Object.fromEntries(
    Object.entries(measurements).filter(([, value]) => typeof value === "number")
  ) as Record<string, number>;
}

export function getAppInsights(): ApplicationInsights | null {
  if (typeof window === "undefined" || !connectionString) {
    return null;
  }

  if (!appInsightsInstance) {
    appInsightsInstance = new ApplicationInsights({
      config: {
        connectionString,
        enableAutoRouteTracking: false,
      },
    });
    appInsightsInstance.loadAppInsights();
  }

  return appInsightsInstance;
}

export function trackPageView(name: string, uri?: string): void {
  getAppInsights()?.trackPageView({ name, uri });
}

export function trackEvent(
  name: string,
  properties: EventProperties = {},
  measurements: EventMeasurements = {}
): void {
  getAppInsights()?.trackEvent({
    name,
    properties: sanitizeProperties(properties),
    measurements: sanitizeMeasurements(measurements),
  });
}

export function trackException(error: Error, properties: EventProperties = {}): void {
  getAppInsights()?.trackException({
    exception: error,
    properties: sanitizeProperties(properties),
  });
}
