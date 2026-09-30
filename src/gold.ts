// Live spot gold price in USD per troy ounce.
//
// The Python bot used FreeGoldAPI's latest.json, which is a historical series
// that stopped updating, so it kept reporting a months-old price. These two
// sources are live quotes and need no API key; the second is a fallback.

export interface GoldPrice {
  /** USD per troy ounce. */
  price: number;
  /** ISO time of the quote. */
  updatedAt: string;
  source: string;
}

interface Source {
  name: string;
  url: string;
  parse(data: unknown): { price: number; updatedAt: string } | null;
}

const SOURCES: Source[] = [
  {
    name: "gold-api.com",
    url: "https://api.gold-api.com/price/XAU",
    parse(data) {
      const d = data as { price?: unknown; updatedAt?: unknown };
      if (typeof d.price !== "number") return null;
      return { price: d.price, updatedAt: typeof d.updatedAt === "string" ? d.updatedAt : new Date().toISOString() };
    },
  },
  {
    name: "Swissquote",
    url: "https://forex-data-feed.swissquote.com/public-quotes/bboquotes/instrument/XAU/USD",
    parse(data) {
      // One entry per trading platform, each with bid/ask per spread profile. Use the first mid price.
      const quote = (data as { ts?: number; spreadProfilePrices?: { bid?: number; ask?: number }[] }[])[0];
      const prices = quote?.spreadProfilePrices?.[0];
      if (typeof prices?.bid !== "number" || typeof prices.ask !== "number") return null;
      return {
        price: (prices.bid + prices.ask) / 2,
        updatedAt: new Date(quote?.ts ?? Date.now()).toISOString(),
      };
    },
  },
];

/** Gold has never traded outside this range; anything else is a bad response. */
const MIN_PRICE = 100;
const MAX_PRICE = 100_000;
const TIMEOUT_MS = 5_000;

/** Returns the first source's price that looks sane, or null if all of them fail. */
export async function getGoldPrice(): Promise<GoldPrice | null> {
  for (const source of SOURCES) {
    try {
      const res = await fetch(source.url, {
        headers: { "User-Agent": "KrugerrandBot/2.0", Accept: "application/json" },
        signal: AbortSignal.timeout(TIMEOUT_MS),
      });
      if (!res.ok) {
        console.error(`${source.name} returned ${res.status}`);
        continue;
      }
      const quote = source.parse(await res.json());
      if (quote && Number.isFinite(quote.price) && quote.price >= MIN_PRICE && quote.price <= MAX_PRICE) {
        return { ...quote, source: source.name };
      }
      console.error(`${source.name} returned an unusable price`, quote);
    } catch (err) {
      console.error(`${source.name} request failed`, err);
    }
  }
  return null;
}

/** Typical dealer premium for a 1 oz Krugerrand over spot. */
export const KRUGERRAND_PREMIUM = 0.03;

/** A 1 oz Krugerrand holds exactly one troy ounce of fine gold (it weighs 33.93 g at 22 karat). */
export function krugerrandPrice(spot: number): number {
  return spot * (1 + KRUGERRAND_PREMIUM);
}
