// Krugerrand facts: generated through Hugging Face's inference router when a
// key is set, otherwise (or when every model fails) picked from a curated list.

export interface Fact {
  text: string;
  ai: boolean;
}

const API_URL = "https://router.huggingface.co/v1/chat/completions";
/**
 * Tried in order until one answers: the same model on Groq, then on whichever
 * provider the router picks. Smaller models got basic facts wrong (the mint,
 * the coin's weight), so there is no fallback to one.
 */
const MODELS = ["openai/gpt-oss-120b:groq", "openai/gpt-oss-120b"];
/** Per model. Discord gives a deferred reply 15 minutes, but people won't wait that long. */
const TIMEOUT_MS = 8_000;
const MIN_LENGTH = 20;
const MAX_LENGTH = 600;

const PROMPTS = [
  "Tell me an interesting fact about South African Krugerrand gold coins.",
  "What is a unique fact about Krugerrands?",
  "Share a fascinating detail about Krugerrand coins.",
  "What makes Krugerrands special?",
  "What is a historical fact about Krugerrands?",
  "Share a detail about the design of Krugerrand coins.",
  "What is interesting about how Krugerrands are made?",
  "What makes Krugerrands different from other gold coins?",
  "Share a fact about Krugerrand coin sizes and weights.",
  "What is notable about the metal composition of Krugerrands?",
  "Tell me about the history of Krugerrand production.",
  "What is a fact about the Krugerrand's international impact?",
  "Share something about the symbolism on Krugerrand coins.",
  "What is interesting about the Krugerrand's legal status?",
  "Tell me a fact about the Krugerrand's role in gold investment.",
  "Tell me about the Krugerrand's relationship to South African currency.",
  "Share a fact about Krugerrand coin collecting.",
];

const PERSONAS = [
  "You are a knowledgeable numismatist sharing fascinating coin facts.",
  "You are an expert on precious metals providing educational information.",
  "You are a historian specializing in gold coins and bullion.",
  "You are a coin collector sharing interesting details.",
  "You are an expert on South African currency and gold coins.",
];

const FORMAT =
  "Reply with a single accurate fact in one or two sentences. No preamble, no markdown, no questions back.";

export const CURATED_FACTS = [
  "The South African Krugerrand was first minted in 1967 and was the world's first modern gold bullion coin.",
  "Krugerrands are named after Paul Kruger, former President of the South African Republic, whose face appears on the coin.",
  "The reverse of the Krugerrand shows a springbok antelope, South Africa's national animal.",
  "Krugerrands are 22 karat gold: 91.67% gold and 8.33% copper, which makes them harder to scratch than pure gold coins.",
  "A 1 oz Krugerrand weighs 33.93 g, so that it holds exactly one troy ounce of fine gold.",
  "Although they are legal tender in South Africa, Krugerrands carry no face value; their value is their gold content.",
  "More than 50 million ounces of gold have been sold as Krugerrands since 1967.",
  "The United States banned Krugerrand imports from 1985 to 1991 as part of its sanctions against apartheid.",
  "The coin's design has barely changed since 1967, making it one of the most recognizable gold coins in the world.",
  "Fractional Krugerrands of 1/2, 1/4 and 1/10 oz were introduced in 1980, alongside the original 1 oz coin.",
  "The copper in Krugerrands gives them a warmer, more orange tone than 24 karat coins like the Canadian Maple Leaf.",
  "Krugerrands are struck by the South African Mint from gold blanks refined by the Rand Refinery.",
  "The Krugerrand's success prompted other countries to launch bullion coins, including the Canadian Maple Leaf in 1979 and the American Gold Eagle in 1986.",
  "The springbok on the reverse was designed by Coert Steynberg, and Paul Kruger's portrait on the obverse by Tommy Sasseen.",
  "A 1 oz Krugerrand is 32.77 mm across and 2.84 mm thick.",
  "The name combines 'Kruger', after Paul Kruger, with 'rand', South Africa's currency.",
];

const pick = <T>(items: readonly T[]): T => items[Math.floor(Math.random() * items.length)]!;

/** Never throws: falls back to a curated fact. */
export async function getKrugerrandFact(apiKey: string | undefined): Promise<Fact> {
  if (apiKey) {
    for (const model of MODELS) {
      const text = await askModel(apiKey, model);
      if (text) return { text, ai: true };
    }
  }
  return { text: pick(CURATED_FACTS), ai: false };
}

async function askModel(apiKey: string, model: string): Promise<string | null> {
  try {
    const res = await fetch(API_URL, {
      method: "POST",
      headers: { Authorization: `Bearer ${apiKey}`, "Content-Type": "application/json" },
      body: JSON.stringify({
        model,
        messages: [
          { role: "system", content: `${pick(PERSONAS)} ${FORMAT}` },
          { role: "user", content: pick(PROMPTS) },
        ],
        // Reasoning models spend part of this budget thinking before they answer.
        max_tokens: 400,
        temperature: 0.7 + Math.random() * 0.4,
      }),
      signal: AbortSignal.timeout(TIMEOUT_MS),
    });
    if (!res.ok) {
      console.error(`${model} returned ${res.status}: ${(await res.text()).slice(0, 300)}`);
      return null;
    }
    const data = (await res.json()) as { choices?: { message?: { content?: unknown } }[] };
    const content = data.choices?.[0]?.message?.content;
    return typeof content === "string" ? cleanFact(content) : null;
  } catch (err) {
    console.error(`${model} request failed`, err);
    return null;
  }
}

/**
 * Tidies a model's answer, or returns null if it isn't usable. Long answers are
 * cut at a sentence end; a "." only ends a sentence when whitespace follows, so
 * "91.67%" and "1/10 oz." stay intact.
 */
export function cleanFact(raw: string): string | null {
  let text = raw
    .replace(/\*\*|__|`/g, "")
    .replace(/\s+/g, " ")
    .trim()
    .replace(/^["“](.*)["”]$/, "$1")
    .trim();
  if (text.length > MAX_LENGTH) {
    const ends = [...text.slice(0, MAX_LENGTH + 1).matchAll(/[.!?](?=\s)/g)];
    const last = ends.at(-1);
    if (!last || last.index < MIN_LENGTH) return null;
    text = text.slice(0, last.index + 1);
  }
  return text.length >= MIN_LENGTH ? text : null;
}
