import { describe, expect, it } from "vitest";
import { CURATED_FACTS, cleanFact } from "../src/facts";

describe("cleanFact", () => {
  it("keeps decimals and abbreviations intact", () => {
    expect(cleanFact("Krugerrands contain 91.67% gold and come in sizes down to 1/10 oz.")).toBe(
      "Krugerrands contain 91.67% gold and come in sizes down to 1/10 oz.",
    );
  });

  it("strips markdown, quotes and extra whitespace", () => {
    expect(cleanFact('  "**The Krugerrand**   was first minted in 1967."\n')).toBe("The Krugerrand was first minted in 1967.");
  });

  it("cuts a long answer at the last sentence end that fits", () => {
    const first = "The Krugerrand was the first modern gold bullion coin, launched in 1967.";
    const text = cleanFact(`${first} ${"More detail. ".repeat(60)}`)!;
    expect(text.startsWith(first)).toBe(true);
    expect(text.length).toBeLessThanOrEqual(600);
    expect(text.endsWith(".")).toBe(true);
  });

  it("rejects answers that are too short or have no sentence end to cut at", () => {
    expect(cleanFact("Gold.")).toBeNull();
    expect(cleanFact("x".repeat(700))).toBeNull();
  });

  it("accepts every curated fact unchanged", () => {
    for (const fact of CURATED_FACTS) expect(cleanFact(fact)).toBe(fact);
  });
});
