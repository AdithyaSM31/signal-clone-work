import type { CapacitorConfig } from "@capacitor/cli";

// The Android app bundles the static export (`out/`) and serves it from https://localhost inside the WebView.
// The API address is baked in at build time through NEXT_PUBLIC_API_URL (see the `android:apk` script), and the
// API must list https://localhost in CORS_ORIGINS.
//
// Only a local test build pointed at a plain-http API (e.g. http://localhost:8000 through `adb reverse`) gets
// cleartext/mixed-content allowed; builds against the deployed https API keep Android's defaults.
const localHttpApi = (process.env.NEXT_PUBLIC_API_URL ?? "").startsWith("http://");

const config: CapacitorConfig = {
  appId: "com.asm20.signalclone",
  appName: "Signal Clone",
  webDir: "out",
  server: localHttpApi ? { cleartext: true } : undefined,
  android: {
    allowMixedContent: localHttpApi,
    // Lets Chrome DevTools (chrome://inspect) attach to debug builds.
    webContentsDebuggingEnabled: true,
  },
};

export default config;
