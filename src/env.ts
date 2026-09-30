export interface Env {
  DISCORD_APPLICATION_ID: string;
  DISCORD_PUBLIC_KEY: string;
  /** Optional. Without it /krugerrandfact answers from the built-in fact list. */
  HUGGINGFACE_API_KEY?: string;
}
