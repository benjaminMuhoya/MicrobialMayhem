# Mobile store release guide

## What is packaged

Microbial Mayhem 1.0.0 is an offline-capable Capacitor game with native Android and iOS projects. Core fighters, scientific data, fonts, visuals, audio, and game logic are local. There is no remote web URL in the native configuration and no visible browser chrome.

## iPhone and iPad

1. Install the full current Xcode from the Mac App Store. GitHub Actions continuously compiles an unsigned simulator application, but signing, device testing, and archiving still require your full local Xcode installation.
2. In Terminal, run `cd web`, `npm ci`, and `npm run ios:sync`.
3. Open `web/ios/App/App.xcodeproj` in Xcode.
4. Select the App target, then Signing & Capabilities. Choose your Apple Developer team. Keep bundle identifier `com.microbialmayhem.game`, or replace it everywhere with an identifier you control.
5. Confirm version 1.0 and build 1. Test on an iPhone and iPad in landscape and portrait, including an interrupted/backgrounded battle, mute switch, safe areas, trackpad, keyboard, reduced motion, and offline launch.
6. Choose **Product → Archive**, then **Distribute App → App Store Connect → Upload**.
7. In App Store Connect, create the app record, provide screenshots for required iPhone/iPad sizes, age rating, support URL, and the published `privacy.html` GitHub Pages URL. Declare that the app does not track and collects no player data, provided the release has not added analytics or external services.
8. Add review notes: “Core gameplay is offline. Scientific catalog update checking is user-initiated in Settings → Game information. No login is required.” Submit the TestFlight build first, complete internal testing, then submit for review.

## Google Play

1. In `web`, run `npm ci` and `npm run android:sync`.
2. For local testing, run `npm run android:apk`. The debug APK appears at `web/android/app/build/outputs/apk/debug/app-debug.apk`.
3. Run `npm run android:bundle` to generate the unsigned Play bundle at `web/android/app/build/outputs/bundle/release/app-release.aab`. GitHub Actions also publishes this as the `microbial-mayhem-unsigned-play-bundle` workflow artifact.
4. For Play Console, create a private upload keystore and keep it outside Git. Configure release signing through a private `keystore.properties` file or Android Studio; never commit passwords or the keystore. Sign the `.aab`, then upload it to an internal-testing track first.
5. Complete the Data safety form consistently with the privacy policy: no account, ads, tracking, or collected player data. Provide the hosted privacy-policy URL even if collection is “none.”
6. Supply phone and tablet screenshots, app icon, feature graphic, content rating, target audience, and scientific/educational description. Test the Play pre-launch report before production rollout.

## Store readiness risks that require owner/device action

- Full Xcode and Apple Developer signing are not installed/configured in this environment.
- App Store Connect and Play Console records, legal developer name, support contact/URL, tax/banking agreements, screenshots, questionnaires, and reviewer submission require the account owner.
- Physical-device frame rate, thermal behavior, battery use, audio latency, mute-switch behavior, and haptic feel require representative real iPhones, iPads, and Android devices.
- The generated artwork and scientific dataset attribution should receive the owner’s final brand/legal review.
- The 2026-07-16 production audit reports two moderate PostCSS advisories through Next. The suggested automatic fix would force an unrelated breaking downgrade to Next 9, so it was not applied. Recheck upstream Next/PostCSS releases before submission; there are currently no high or critical production audit findings.
