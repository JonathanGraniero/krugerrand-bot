// Builds requests signed the same way Discord signs them, so tests exercise
// the real signature check instead of bypassing it.
import { vi } from "vitest";
import worker from "../../src/index";
import type { Env } from "../../src/env";
import type { Embed, MessageBody } from "../../src/discord/api";

const toHex = (buf: ArrayBuffer) => Buffer.from(buf).toString("hex");

type Route = [urlContains: string, respond: (req: Request) => Response | Promise<Response>];

export interface FakeNetwork {
  /** Every outgoing request, in order. */
  calls: Request[];
  /** Bodies sent to Discord to replace deferred "thinking…" replies. */
  edits: MessageBody[];
}

/**
 * Replaces global fetch: Discord webhook edits are recorded, other URLs are
 * answered by the first route whose text they contain, and anything else throws.
 */
export function stubFetch(routes: Route[]): FakeNetwork {
  const net: FakeNetwork = { calls: [], edits: [] };
  vi.stubGlobal("fetch", async (input: RequestInfo | URL, init?: RequestInit) => {
    const req = new Request(input, init);
    net.calls.push(req.clone());
    if (req.url.startsWith("https://discord.com/api/v10/webhooks/")) {
      net.edits.push((await req.json()) as MessageBody);
      return Response.json({});
    }
    const route = routes.find(([match]) => req.url.includes(match));
    if (!route) throw new Error(`Unexpected fetch: ${req.url}`);
    return route[1](req);
  });
  return net;
}

export interface TestBot {
  env: Env;
  ctx: ExecutionContext;
  send(payload: unknown, opts?: { tamper?: boolean }): Promise<Response>;
  /** Runs a slash command, lets the deferred work finish, and returns the immediate response. */
  command(name: string): Promise<{ type: number; data?: { content?: string; flags?: number } }>;
}

export async function createTestBot(overrides: Partial<Env> = {}): Promise<TestBot> {
  const keys = (await crypto.subtle.generateKey({ name: "Ed25519" }, true, ["sign", "verify"])) as CryptoKeyPair;
  const env: Env = {
    DISCORD_APPLICATION_ID: "123",
    DISCORD_PUBLIC_KEY: toHex((await crypto.subtle.exportKey("raw", keys.publicKey)) as ArrayBuffer),
    ...overrides,
  };

  const pending: Promise<unknown>[] = [];
  const ctx = {
    waitUntil: (p: Promise<unknown>) => void pending.push(p),
    passThroughOnException: () => {},
  } as unknown as ExecutionContext;

  async function send(payload: unknown, opts: { tamper?: boolean } = {}) {
    const body = JSON.stringify(payload);
    const timestamp = String(Math.floor(Date.now() / 1000));
    const sig = await crypto.subtle.sign("Ed25519", keys.privateKey, new TextEncoder().encode(timestamp + body));
    const req = new Request("https://bot.example/interactions", {
      method: "POST",
      headers: { "X-Signature-Ed25519": toHex(sig), "X-Signature-Timestamp": timestamp },
      body: opts.tamper ? body.replace("}", ',"x":1}') : body,
    });
    return worker.fetch(req, env, ctx);
  }

  return {
    env,
    ctx,
    send,
    async command(name) {
      const res = await send({ id: "1", application_id: env.DISCORD_APPLICATION_ID, token: "tok", type: 2, data: { name } });
      const json = (await res.json()) as Awaited<ReturnType<TestBot["command"]>>;
      while (pending.length > 0) await Promise.all(pending.splice(0));
      return json;
    },
  };
}

/** The single embed of the last deferred reply. */
export function lastEmbed(net: FakeNetwork): Embed {
  const embed = net.edits.at(-1)?.embeds?.[0];
  if (!embed) throw new Error("No reply was posted");
  return embed;
}
