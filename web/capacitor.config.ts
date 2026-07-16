import type { CapacitorConfig } from "@capacitor/cli";

const config: CapacitorConfig = {
  appId: "com.microbialmayhem.game",
  appName: "Microbial Mayhem",
  webDir: "dist/pages",
  server: {
    androidScheme: "https",
  },
  android: {
    backgroundColor: "#061411",
    allowMixedContent: false,
  },
};

export default config;
