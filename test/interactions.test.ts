import { afterEach, beforeAll, describe, expect, it, vi } from "vitest";
import worker from "../src/index";
import { createTestBot, stubFetch, type TestBot } from "./helpers/discord";

let bot: TestBot;

beforeAll(async () => {
  bot = await createTestBot();
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("interactions endpoint", () => {
  it("answers Discord's PING with PONG", async () => {
    const res = await bot.send({ id: "1", type: 1 });
    expect(res.status).toBe(200);
    expect(await res.json()).toEqual({ type: 1 });
  });

  it("rejects a tampered body", async () => {
    const res = await bot.send({ id: "2", type: 1 }, { tamper: true });
    expect(res.status).toBe(401);
  });

  it("rejects missing signature headers", async () => {
    const res = await worker.fetch(new Request("https://bot.example/interactions", { method: "POST", body: "{}" }), bot.env, bot.ctx);
    expect(res.status).toBe(401);
  });

  it("rejects a malformed signature", async () => {
    const req = new Request("https://bot.example/interactions", {
      method: "POST",
      headers: { "X-Signature-Ed25519": "not-hex", "X-Signature-Timestamp": "1" },
      body: "{}",
    });
    expect((await worker.fetch(req, bot.env, bot.ctx)).status).toBe(401);
  });

  it("serves a health check on GET /", async () => {
    const res = await worker.fetch(new Request("https://bot.example/"), bot.env, bot.ctx);
    expect(res.status).toBe(200);
  });

  it("returns 404 for other paths", async () => {
    const res = await worker.fetch(new Request("https://bot.example/nope", { method: "POST" }), bot.env, bot.ctx);
    expect(res.status).toBe(404);
  });

  it("answers an unknown command privately without calling out", async () => {
    const net = stubFetch([]);
    const res = await bot.command("nope");
    expect(res.type).toBe(4);
    expect(res.data?.flags).toBe(64);
    expect(net.calls).toHaveLength(0);
  });

  it("defers a known command, then edits the reply through the interaction webhook", async () => {
    const net = stubFetch([["gold-api.com", () => Response.json({ price: 4155.2, updatedAt: "2026-09-30T23:34:18Z" })]]);
    const res = await bot.command("goldprice");
    expect(res.type).toBe(5);
    const edit = net.calls.at(-1)!;
    expect(edit.method).toBe("PATCH");
    expect(edit.url).toBe("https://discord.com/api/v10/webhooks/123/tok/messages/@original");
  });
});
