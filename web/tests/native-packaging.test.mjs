import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const root = new URL("../../", import.meta.url);

test("iOS package targets modern iPhone and iPad without obsolete arm requirements", async () => {
  const [plist, project, privacy] = await Promise.all([
    readFile(new URL("web/ios/App/App/Info.plist", root), "utf8"),
    readFile(new URL("web/ios/App/App.xcodeproj/project.pbxproj", root), "utf8"),
    readFile(new URL("web/ios/App/App/PrivacyInfo.xcprivacy", root), "utf8"),
  ]);
  assert.doesNotMatch(plist, /armv7/);
  assert.match(plist, /UIInterfaceOrientationLandscapeLeft/);
  assert.match(project, /TARGETED_DEVICE_FAMILY = "1,2"/);
  assert.match(project, /IPHONEOS_DEPLOYMENT_TARGET = 15\.0/);
  assert.match(privacy, /NSPrivacyTracking/);
});

test("CI produces Android install and Play packages plus an unsigned iOS verification build", async () => {
  const [android, ios, packageJson] = await Promise.all([
    readFile(new URL(".github/workflows/build-android.yml", root), "utf8"),
    readFile(new URL(".github/workflows/build-ios.yml", root), "utf8"),
    readFile(new URL("web/package.json", root), "utf8"),
  ]);
  assert.match(android, /assembleDebug bundleRelease/);
  assert.match(android, /app-release\.aab/);
  assert.match(ios, /xcodebuild/);
  assert.match(ios, /generic\/platform=iOS Simulator/);
  assert.match(packageJson, /"android:bundle"/);
});
