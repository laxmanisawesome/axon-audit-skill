# RN/Expo/Firebase Specific Audit Checks

## Expo Configuration
- Is Expo SDK version current? Check latest against `app.json` or `package.json`
- EAS Build: does the build profile match production requirements? Are secrets in `eas.json` properly handled?
- Expo Updates: enabled? Is the fallback-to-latest behaviour configured? OTA update turned on?
- EAS Submit: is auto-submit configured? Are Apple/Google credentials properly rotated?
- Is `app.json`/`app.config.js` leaking API keys in extra/plugins config?

## React Native Security
- AsyncStorage: storing tokens or PII? Should use `expo-secure-store` instead
- App Transport Security (iOS): is arbitrary loads allowed? Should pin to specific domains
- Deep linking: is the intent URL pattern too permissive? Malicious apps could intercept
- Clipboard: is sensitive data being copied to clipboard?
- JavaScript bundle: are secrets compiled into the bundle (any string in JS code is visible)

## Firebase
- Firestore security rules: are they restrictive? Can user A read user B's data?
- Firebase Functions: are they idempotent? What happens if called twice?
- Firebase Auth: is email verification required? Are custom claims used for roles?
- Firestore indexes: are there composite indexes for common queries? Unindexed queries fail at scale
- Firestore read amplification: does a list view read 10 or 1000 documents?
- Firebase Storage: are security rules set on storage buckets? Public by default
- Firebase Analytics: PII being sent to analytics?

## Push Notifications
- Expo push token: stored and rotated? If token changes, push fails silently
- Push certificate: Apple push cert expires every year. Google FCM token expires periodically
- Notification permissions: requested at appropriate time (not on first launch)?
- Silent push: handled gracefully? Background tasks completing in time?

## RN Performance
- FlatList vs SectionList vs FlashList — are they being used correctly?
- Image caching: are remote images being cached? Missing cache = slow loads
- Re-renders: are there unnecessary re-renders on state changes?
- Hermes: enabled in production? JSC is slower
- Bundle size: is it under 50MB? Large bundles crash on old devices
