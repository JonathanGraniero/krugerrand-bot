// The subset of the Discord interactions API this bot uses.
// https://discord.com/developers/docs/interactions/receiving-and-responding

export const InteractionType = {
  PING: 1,
  APPLICATION_COMMAND: 2,
} as const;

export const InteractionResponseType = {
  PONG: 1,
  CHANNEL_MESSAGE_WITH_SOURCE: 4,
  /** "Bot is thinking…"; the real reply follows via editOriginalResponse. */
  DEFERRED_CHANNEL_MESSAGE_WITH_SOURCE: 5,
} as const;

/** Message flag: only the user who ran the command can see the reply. */
export const EPHEMERAL = 1 << 6;

export interface Interaction {
  id: string;
  application_id: string;
  /** Lets the bot edit its reply for 15 minutes after the interaction. */
  token: string;
  type: number;
  data?: {
    name: string;
  };
}

export interface InteractionResponse {
  type: number;
  data?: {
    content?: string;
    flags?: number;
  };
}
