import type { CapacitorConfig } from "@capacitor/cli";

const config: CapacitorConfig = {
  appId: "com.microbialmayhem.game",
  appName: "Microbial Mayhem",
  webDir: "dist/pages",
  backgroundColor: "#061411",
  server: {
    androidScheme: "https",
  },
  android: {
    backgroundColor: "#061411",
    allowMixedContent: false,
  },
  ios: {
    backgroundColor: "#061411",
    preferredContentMode: "mobile",
    webContentsDebuggingEnabled: false,
  },
};

export default config;
