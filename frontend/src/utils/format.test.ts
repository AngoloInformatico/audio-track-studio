import { describe, expect, it } from "vitest";

import { formatBytes, formatTime, parseTimestamp } from "./format";

describe("formatTime", () => {
  it("formats long audio with millisecond precision", () => {
    expect(formatTime(3723.456, true)).toBe("01:02:03.456");
  });

  it("clamps invalid negative positions", () => {
    expect(formatTime(-5, false)).toBe("00:00");
  });
});

describe("formatBytes", () => {
  it("uses readable binary units", () => {
    expect(formatBytes(1_073_741_824)).toBe("1.00 GB");
  });
});

describe("parseTimestamp", () => {
  it("accepts hours, minutes and milliseconds", () => {
    expect(parseTimestamp("01:02:03.456")).toBe(3723.456);
  });

  it("accepts a raw seconds value with decimal comma", () => {
    expect(parseTimestamp("12,850")).toBe(12.85);
  });

  it("rejects invalid clock values", () => {
    expect(parseTimestamp("00:75:00")).toBeUndefined();
  });
});
