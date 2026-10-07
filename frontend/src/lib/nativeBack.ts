"use client";

import { Capacitor } from "@capacitor/core";
import type { Panel, SettingsSection, Tab } from "@/stores/ui";
import { useUi } from "@/stores/ui";

export type BackStep = "close-dialog" | "close-panel" | "close-settings-section" | "go-to-chats" | "close-chat" | "exit";

interface BackState {
  dialogOpen: boolean;
  panel: Panel;
  settingsSection: SettingsSection | null;
  tab: Tab;
  selectedId: number | null;
}

/** What Android's back button should do: close the innermost open thing, and exit from the chat list. */
export function backStep(s: BackState): BackStep {
  if (s.dialogOpen) return "close-dialog";
  if (s.panel) return "close-panel";
  if (s.tab === "settings" && s.settingsSection) return "close-settings-section";
  if (s.tab !== "chats") return "go-to-chats";
  if (s.selectedId !== null) return "close-chat";
  return "exit";
}

/** Wires the hardware back button in the Android app. A no-op in the browser. */
export async function installNativeBackButton(): Promise<() => void> {
  if (!Capacitor.isNativePlatform()) return () => {};
  const { App } = await import("@capacitor/app");
  const handle = await App.addListener("backButton", () => {
    const ui = useUi.getState();
    const step = backStep({
      dialogOpen: !!document.querySelector('[role="dialog"]'),
      panel: ui.panel,
      settingsSection: ui.settingsSection,
      tab: ui.tab,
      selectedId: ui.selectedId,
    });
    switch (step) {
      case "close-dialog": // modals close on Escape
        document.dispatchEvent(new KeyboardEvent("keydown", { key: "Escape", bubbles: true }));
        return;
      case "close-panel":
        return ui.closePanel();
      case "close-settings-section":
        return ui.openSettings(null);
      case "go-to-chats":
        return ui.setTab("chats");
      case "close-chat":
        return ui.select(null);
      case "exit":
        return void App.exitApp();
    }
  });
  return () => void handle.remove();
}
