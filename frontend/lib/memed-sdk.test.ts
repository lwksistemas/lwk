import { describe, expect, it, vi } from "vitest";
import {
  isMemedMessageReady,
  isMemedV4Boot,
  MEMED_V4_BOOT_KEY,
  withTimeout,
} from "./memed-sdk";

describe("withTimeout", () => {
  it("resolve quando a promise termina a tempo", async () => {
    await expect(withTimeout(Promise.resolve("ok"), 50, "teste")).resolves.toBe("ok");
  });

  it("rejeita se a promise da Memed não responder", async () => {
    vi.useFakeTimers();
    const pending = withTimeout(new Promise(() => {}), 40, "Memed: travou");
    const assertion = expect(pending).rejects.toThrow(/Memed: travou/);
    await vi.advanceTimersByTimeAsync(40);
    await assertion;
    vi.useRealTimers();
  });
});

describe("detecção V4", () => {
  it("reconhece o boot do widget V4", () => {
    const win = { [MEMED_V4_BOOT_KEY]: { teardown() {} } } as unknown as Window;
    expect(isMemedV4Boot(win)).toBe(true);
    expect(isMemedV4Boot({} as Window)).toBe(false);
  });

  it("reconhece MEMED_READY do iframe", () => {
    expect(isMemedMessageReady({ type: "MEMED_READY" })).toBe(true);
    expect(isMemedMessageReady({ type: "COMMAND_RESULT" })).toBe(false);
    expect(isMemedMessageReady(null)).toBe(false);
  });
});
