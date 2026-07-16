"use client";

import { openDB } from "idb";
import { useEffect } from "react";

const DB_NAME = "microbial-mayhem";

export async function savePreference(key: string, value: unknown) {
  const db = await openDB(DB_NAME, 1, {
    upgrade(database) {
      if (!database.objectStoreNames.contains("preferences")) database.createObjectStore("preferences");
    },
  });
  await db.put("preferences", value, key);
}

export async function loadPreference<T>(key: string): Promise<T | undefined> {
  const db = await openDB(DB_NAME, 1, {
    upgrade(database) {
      if (!database.objectStoreNames.contains("preferences")) database.createObjectStore("preferences");
    },
  });
  return db.get("preferences", key);
}

export function PwaRuntime() {
  useEffect(() => {
    if ("serviceWorker" in navigator && (location.protocol === "https:" || location.hostname === "localhost")) {
      navigator.serviceWorker.register("./sw.js", { scope: "./" }).catch(() => undefined);
    }
  }, []);
  return null;
}
