// Builds the Android app: static export with the API URL baked in → Capacitor sync → Gradle debug APK.
// Output: frontend/SignalClone.apk (git-ignored).
//
//   npm run android:apk                                   # uses the deployed API below
//   NEXT_PUBLIC_API_URL=https://my-api.onrender.com npm run android:apk
//
// Needs the Android SDK (ANDROID_HOME, or Android Studio's default location) and JDK 21 (JAVA_HOME).
import { execSync } from "node:child_process";
import { copyFileSync, existsSync } from "node:fs";
import { homedir } from "node:os";
import { join } from "node:path";
import { fileURLToPath } from "node:url";

const DEFAULT_API = "https://signal-clone-asm20-api.onrender.com";
const root = fileURLToPath(new URL("..", import.meta.url));
const env = { ...process.env, NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || DEFAULT_API };

if (!env.ANDROID_HOME) {
  const guess =
    process.platform === "win32"
      ? join(process.env.LOCALAPPDATA ?? "", "Android", "Sdk")
      : join(homedir(), process.platform === "darwin" ? "Library/Android/sdk" : "Android/Sdk");
  if (existsSync(guess)) env.ANDROID_HOME = guess;
}

const run = (cmd, cwd = root) => {
  console.log(`\n> ${cmd}`);
  execSync(cmd, { cwd, env, stdio: "inherit" });
};

console.log(`Building the Android app against ${env.NEXT_PUBLIC_API_URL}`);
run("npm run build");
run("npx cap sync android");
const androidDir = join(root, "android");
run(`"${join(androidDir, process.platform === "win32" ? "gradlew.bat" : "gradlew")}" assembleDebug`, androidDir);

const apk = join(root, "android", "app", "build", "outputs", "apk", "debug", "app-debug.apk");
copyFileSync(apk, join(root, "SignalClone.apk"));
console.log(`\nAPK ready: ${join(root, "SignalClone.apk")}`);
