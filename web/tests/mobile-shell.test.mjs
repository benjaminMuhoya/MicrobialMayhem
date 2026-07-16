import assert from "node:assert/strict";
import test from "node:test";
import { DEFAULT_PREFERENCES, normalizePreferences } from "../app/game/preferences.ts";
import { classifyViewport } from "../app/game/viewport.ts";

test("mobile preferences normalize persisted comfort settings", () => {
  assert.deepEqual(normalizePreferences(undefined), DEFAULT_PREFERENCES);
  assert.equal(normalizePreferences({ musicVolume: 4 }).musicVolume, 1);
  assert.equal(normalizePreferences({ effectsVolume: -2 }).effectsVolume, 0);
  assert.equal(normalizePreferences({ reducedMotion: true }).reducedMotion, true);
});
test("viewport classification separates phone and tablet compositions", () => {
  assert.equal(classifyViewport(390, 844), "phone-portrait");
  assert.equal(classifyViewport(844, 390), "phone-landscape");
  assert.equal(classifyViewport(820, 1180), "tablet-portrait");
  assert.equal(classifyViewport(1180, 820), "tablet-landscape");
  assert.equal(classifyViewport(1440, 1100), "desktop");
});
