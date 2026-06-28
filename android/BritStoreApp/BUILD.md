# How to Build the BritStore Android App

## Option 1: Android Studio (Recommended)
1. Open Android Studio
2. File → Open → select `android/BritStoreApp/`
3. Let Gradle sync finish
4. Build → Build Bundle(s) / APK(s) → Build APK(s)
5. APK will be at `app/build/outputs/apk/debug/app-debug.apk`

## Option 2: Command Line
```bash
cd android/BritStoreApp
# Windows:
gradlew.bat assembleDebug
# Linux/Mac:
./gradlew assembleDebug
```

## Configuration
Edit `MainActivity.java` and change the `STORE_URL` constant to point to your actual store URL. Default is `https://ascentraconsulting.co.uk`.

## CI/CD
For GitHub Actions, use the existing workflow at `.github/workflows/build-and-upload.yml` — it builds a signed APK and uploads it via the API.
