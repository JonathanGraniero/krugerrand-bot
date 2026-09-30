// Outgoing calls to Discord's REST API (finishing deferred replies).
// https://discord.com/developers/docs/reference

const API = "https://discord.com/api/v10";

export interface Embed {
  title?: string;
  description?: string;
  color?: number;
  timestamp?: string;
  fields?: { name: string; value: string; inline?: boolean }[];
  footer?: { text: string };
}

export interface MessageBody {
  content?: string;
  embeds?: Embed[];
}

/** Replaces the "thinking…" placeholder of a deferred interaction reply. */
export async function editOriginalResponse(appId: string, interactionToken: string, body: MessageBody): Promise<void> {
  const res = await fetch(`${API}/webhooks/${appId}/${interactionToken}/messages/@original`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) console.error(`editOriginalResponse failed (${res.status}): ${await res.text()}`);
}
