import { describe, expect, it } from "vitest";
import { backStep } from "./nativeBack";

const base = { dialogOpen: false, panel: null, settingsSection: null, tab: "chats", selectedId: null } as const;

describe("Android back button", () => {
  it("closes the innermost thing first", () => {
    expect(backStep({ ...base, dialogOpen: true, panel: "new-chat", selectedId: 3 })).toBe("close-dialog");
    expect(backStep({ ...base, panel: "conversation-settings", selectedId: 3 })).toBe("close-panel");
    expect(backStep({ ...base, tab: "settings", settingsSection: "profile" })).toBe("close-settings-section");
    expect(backStep({ ...base, tab: "settings" })).toBe("go-to-chats");
    expect(backStep({ ...base, tab: "calls" })).toBe("go-to-chats");
    expect(backStep({ ...base, selectedId: 3 })).toBe("close-chat");
  });

  it("exits from the chat list", () => {
    expect(backStep(base)).toBe("exit");
  });
});
