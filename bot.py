"""
Discord bot for gold prices, krugerrand rates, and random facts.
Works both as a standalone bot and as an AWS Lambda function.
"""
import os
import json
import random
import requests
from typing import Optional
from dotenv import load_dotenv
import discord
from discord import app_commands
from discord.ext import commands

# Load environment variables from .env file
load_dotenv()

# Debug: Check if Hugging Face API key is loaded (don't print the actual key)
hf_key_check = os.getenv("HUGGINGFACE_API_KEY")
if hf_key_check:
    print("✓ Hugging Face API key loaded successfully")
else:
    print("⚠ Warning: HUGGINGFACE_API_KEY not found in environment")

# Gold price API (single source)
# FreeGoldAPI (free, no API key, reliable)
FREEGOLD_API_URL = "https://freegoldapi.com/data/latest.json"


def get_gold_price() -> Optional[dict]:
    """
    Fetch current gold price per ounce.
    Returns dict with price and currency, or None if error.
    Uses FreeGoldAPI as the single source of truth.
    """
    try:
        response = requests.get(FREEGOLD_API_URL, timeout=10, headers={
            "User-Agent": "KrugerrandBot/1.0"
        })
        if response.status_code == 200:
            data = response.json()
            # FreeGoldAPI returns an array of records; use the latest (last) entry
            if isinstance(data, list) and len(data) > 0:
                latest = data[-1]

                price: Optional[float] = None

                if isinstance(latest, dict):
                    # Typical FreeGoldAPI schema: {"date": "...", "price": <number>, "source": "..."}
                    val = latest.get("price")

                    # Handle simple numeric or single-element list
                    if isinstance(val, (int, float)):
                        price = float(val)
                    elif isinstance(val, list) and len(val) > 0 and isinstance(val[0], (int, float)):
                        price = float(val[0])

                    # As a fallback, scan for a reasonable numeric value in the dict
                    if price is None:
                        for v in latest.values():
                            if isinstance(v, (int, float)) and 100 <= v <= 10000:
                                price = float(v)
                                break

                elif isinstance(latest, (int, float)):
                    price = float(latest)

                # Basic sanity-check on gold price range in USD/oz
                if price is not None and 100 <= price <= 10000:
                    return {
                        "price": price,
                        "currency": "USD",
                        "unit": "per ounce",
                    }
    except Exception as e:
        print(f"Error fetching gold price from FreeGoldAPI: {e}")
    
    return None


def calculate_krugerrand_price(gold_price_per_oz: float) -> dict:
    """
    Calculate krugerrand price based on gold price.
    Krugerrands are 1 oz of gold, but typically trade at a small premium.
    """
    # Krugerrands typically trade at 2-5% premium over spot gold
    premium = 0.03  # 3% premium
    krugerrand_price = gold_price_per_oz * (1 + premium)
    
    return {
        "spot_gold": gold_price_per_oz,
        "krugerrand_price": krugerrand_price,
        "premium": premium * 100,
        "currency": "USD"
    }


async def get_krugerrand_fact() -> Optional[str]:
    """
    Fetch a random Krugerrand fact from Hugging Face Responses API.
    Uses the new router.huggingface.co/v1/responses endpoint.
    Returns the fact text or None if error.
    """
    # Get Hugging Face API key from environment
    hf_api_key = os.getenv("HUGGINGFACE_API_KEY")
    
    if not hf_api_key:
        print("⚠ Warning: HUGGINGFACE_API_KEY not set, using fallback facts")
        print("   Make sure you've added HUGGINGFACE_API_KEY=your_key to your .env file and restarted the bot")
    else:
        print(f"✓ Using Hugging Face API key (length: {len(hf_api_key)} chars)")
    
    # Vary the prompt each time to get different facts - many different angles
    prompt_variations = [
        "Tell me an interesting fact about South African Krugerrand gold coins.",
        "What is a unique fact about Krugerrands?",
        "Share a fascinating detail about Krugerrand coins.",
        "Give me a fact about the Krugerrand.",
        "What makes Krugerrands special?",
        "Tell me something interesting about Krugerrand bullion coins.",
        "What is a historical fact about Krugerrands?",
        "Share a detail about the design of Krugerrand coins.",
        "What is interesting about how Krugerrands are made?",
        "Tell me about the value and pricing of Krugerrands.",
        "What makes Krugerrands different from other gold coins?",
        "Share a fact about Krugerrand coin sizes and weights.",
        "What is notable about the metal composition of Krugerrands?",
        "Tell me about the history of Krugerrand production.",
        "What is a fact about Krugerrand's international impact?",
        "Share something about the symbolism on Krugerrand coins.",
        "What is interesting about Krugerrand's legal status?",
        "Tell me a fact about Krugerrand's role in gold investment.",
        "What makes the Krugerrand design unique?",
        "Share a detail about Krugerrand's market performance.",
        "What is a fact about Krugerrand coin specifications?",
        "Tell me about Krugerrand's relationship to South African currency.",
        "What is interesting about Krugerrand's global popularity?",
        "Share a fact about Krugerrand coin collecting.",
    ]
    
    # Vary the instructions to change tone and style
    instruction_variations = [
        "You are a helpful assistant that provides interesting facts.",
        "You are a knowledgeable numismatist sharing fascinating coin facts.",
        "You are an expert on precious metals providing educational information.",
        "You are a historian specializing in gold coins and bullion.",
        "You are a financial advisor explaining investment coins.",
        "You are a coin collector sharing interesting details.",
        "You are an expert on South African currency and gold coins.",
        "Provide concise, interesting facts about gold coins.",
        "Share fascinating historical and technical details about coins.",
    ]
    
    # Try Hugging Face Responses API
    if hf_api_key:
        try:
            # Use Inference Provider models (not basic Hugging Face models)
            # These models are available through the Responses API
            # Randomly select a model to try first for more variation
            models_to_try = [
                "openai/gpt-oss-120b:groq",
                "moonshotai/Kimi-K2-Instruct-0905:groq",
                "Qwen/Qwen2.5-7B-Instruct",
            ]
            
            # Randomly shuffle models to try different ones first
            random.shuffle(models_to_try)
            
            api_url = "https://router.huggingface.co/v1/responses"
            headers = {
                "Authorization": f"Bearer {hf_api_key}",
                "Content-Type": "application/json",
            }
            
            # Create varied prompt and instructions
            prompt = random.choice(prompt_variations)
            instructions = random.choice(instruction_variations)
            
            # Vary temperature and other parameters for more randomness
            temperature = random.uniform(0.7, 1.2)
            top_p = random.uniform(0.85, 0.99)
            
            for model_name in models_to_try:
                try:
                    print(f"Trying model {model_name} with Responses API...")
                    
                    # Use the Responses API format from the documentation
                    # Include temperature and top_p for more variation
                    request_data = {
                        "model": model_name,
                        "instructions": instructions,
                        "input": prompt,
                        "temperature": temperature,
                        "top_p": top_p,
                    }
                    
                    response = requests.post(
                        api_url,
                        json=request_data,
                        timeout=30,
                        headers=headers
                    )
                    
                    print(f"Response status: {response.status_code}")
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        # Check for errors first
                        if data.get("status") == "failed":
                            error = data.get("error", {})
                            error_msg = error.get("message", "Unknown error")
                            print(f"✗ Model {model_name} failed: {error_msg}")
                            continue
                        
                        # Debug: print the full response structure
                        print(f"Response status field: {data.get('status')}")
                        print(f"Output array length: {len(data.get('output', []))}")
                        if data.get("output"):
                            print(f"First output item: {data['output'][0] if len(data['output']) > 0 else 'empty'}")
                        
                        # Extract text from output array (Responses API format)
                        output_text = ""
                        output = data.get("output", [])
                        
                        if isinstance(output, list) and len(output) > 0:
                            # Look through output items
                            for item in output:
                                if isinstance(item, dict):
                                    item_type = item.get("type", "")
                                    
                                    # Handle message type with content array
                                    if item_type == "message":
                                        content = item.get("content", [])
                                        if isinstance(content, list):
                                            # Content is a list of content items
                                            for content_item in content:
                                                if isinstance(content_item, dict):
                                                    if content_item.get("type") == "output_text":
                                                        text = content_item.get("text", "")
                                                        if text:
                                                            output_text = text
                                                            print(f"✓ Extracted text from message content: {text[:80]}...")
                                                            break
                                    # Handle reasoning type (skip, we want the actual output)
                                    elif item_type == "reasoning":
                                        continue
                                    # Handle direct output_text items
                                    elif item_type == "output_text":
                                        text = item.get("text", "")
                                        if text:
                                            output_text = text
                                            print(f"✓ Extracted text from output_text item: {text[:80]}...")
                        
                        # Fallback: try output_text field directly
                        if not output_text:
                            output_text = data.get("output_text", "")
                            if output_text:
                                print(f"Found output_text field directly: {output_text[:50]}")
                        
                        print(f"Final extracted output_text length: {len(output_text)}")
                        
                        if output_text and len(output_text) > 15:
                            # Clean up the response
                            fact = output_text.strip()
                            # Take first sentence if multiple sentences
                            if "." in fact:
                                sentences = fact.split(".")
                                fact = sentences[0].strip()
                                if fact:
                                    fact += "."
                            
                            if fact and len(fact) > 15:
                                print(f"✓ AI generated fact: {fact[:50]}...")
                                return fact
                        else:
                            print(f"⚠ No valid output_text found (length: {len(output_text)})")
                    else:
                        error_data = response.text
                        print(f"✗ API error {response.status_code}: {error_data[:300]}")
                        
                except Exception as e:
                    print(f"✗ Error with model {model_name}: {e}")
                    continue
                    
        except Exception as e:
            print(f"✗ Error with Hugging Face API: {e}")
            import traceback
            traceback.print_exc()
    
    # Last resort: Return a varied fact from a curated list
    # This ensures users get different facts even if AI fails
    # Using a larger pool of facts for more variety
    fallback_facts = [
        "The South African Krugerrand was first minted in 1967 and was the world's first modern gold bullion coin.",
        "Krugerrands are named after Paul Kruger, former President of the South African Republic, whose face appears on the coin.",
        "The reverse side of the Krugerrand features a springbok antelope, South Africa's national animal.",
        "Krugerrands contain 91.67% gold and 8.33% copper, making them 22 karat gold coins that are more durable than pure gold.",
        "Despite being legal tender in South Africa, Krugerrands are primarily held as investments rather than used for transactions.",
        "Over 50 million ounces of gold have been minted into Krugerrands since their introduction in 1967.",
        "Krugerrands were banned from import into the United States from 1985 to 1991 due to apartheid sanctions.",
        "The coin's design has remained largely unchanged since 1967, making it one of the most recognizable gold coins worldwide.",
        "Krugerrands are available in four sizes: 1 oz, 1/2 oz, 1/4 oz, and 1/10 oz, with the 1 oz coin being the most popular.",
        "The copper content in Krugerrands gives them a distinctive reddish-gold color compared to pure gold coins.",
        "Krugerrands are produced by the South African Mint and are backed by the South African government.",
        "The Krugerrand helped popularize gold investment coins worldwide and inspired many similar coins from other countries.",
        "Krugerrands were the first gold coin to be denominated by weight rather than face value.",
        "The springbok on the reverse of the Krugerrand is a symbol of South Africa's natural heritage.",
        "Krugerrands have a diameter of 32.77mm and a thickness of 2.84mm for the standard 1 oz coin.",
        "The coin's name combines 'Kruger' (the former president) with 'rand' (South Africa's currency unit).",
    ]
    
    # Ensure truly random selection
    selected_fact = random.choice(fallback_facts)
    print(f"Selected fallback fact (AI APIs unavailable): {selected_fact[:50]}...")
    return selected_fact


# Discord bot setup
# Using default intents - no privileged intents needed for slash commands
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    """Called when the bot is ready."""
    print(f"{bot.user} has logged in!")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"Failed to sync commands: {e}")


@bot.tree.command(name="goldprice", description="Get the current price of gold per ounce")
async def gold_price_command(interaction: discord.Interaction):
    """Slash command to get current gold price."""
    await interaction.response.defer()
    
    gold_data = get_gold_price()
    
    if gold_data:
        price = gold_data["price"]
        currency = gold_data.get("currency", "USD")
        
        embed = discord.Embed(
            title="💰 Current Gold Price",
            color=discord.Color.gold(),
            description=f"**${price:,.2f} {currency}** per troy ounce"
        )
        embed.set_footer(text="Data from FreeGoldAPI.com")
    else:
        embed = discord.Embed(
            title="❌ Error",
            color=discord.Color.red(),
            description="Unable to fetch gold price at this time. Please try again later."
        )
    
    await interaction.followup.send(embed=embed)


@bot.tree.command(name="krugerrandprice", description="Get the current price of a 1 oz Krugerrand")
async def krugerrand_price_command(interaction: discord.Interaction):
    """Slash command to get current krugerrand price."""
    await interaction.response.defer()
    
    gold_data = get_gold_price()
    
    if gold_data:
        gold_price = gold_data["price"]
        krugerrand_data = calculate_krugerrand_price(gold_price)
        
        embed = discord.Embed(
            title="🪙 Krugerrand Price",
            color=discord.Color.gold(),
            description=f"**${krugerrand_data['krugerrand_price']:,.2f} USD**"
        )
        embed.add_field(
            name="Spot Gold",
            value=f"${krugerrand_data['spot_gold']:,.2f}",
            inline=True
        )
        embed.add_field(
            name="Premium",
            value=f"{krugerrand_data['premium']:.1f}%",
            inline=True
        )
        embed.set_footer(text="Price includes ~3% premium over spot gold")
    else:
        embed = discord.Embed(
            title="❌ Error",
            color=discord.Color.red(),
            description="Unable to fetch krugerrand price at this time. Please try again later."
        )
    
    await interaction.followup.send(embed=embed)


@bot.tree.command(name="krugerrandfact", description="Get a random fact about Krugerrands")
async def krugerrand_fact_command(interaction: discord.Interaction):
    """Slash command to get a random krugerrand fact from AI."""
    await interaction.response.defer()
    
    fact = await get_krugerrand_fact()
    
    if fact:
        embed = discord.Embed(
            title="📚 Krugerrand Fact",
            color=discord.Color.gold(),
            description=fact
        )
        embed.set_footer(text="Generated by AI")
    else:
        embed = discord.Embed(
            title="❌ Error",
            color=discord.Color.red(),
            description="Unable to fetch a Krugerrand fact at this time. Please try again later."
        )
    
    await interaction.followup.send(embed=embed)


def main():
    """Main function to run the bot."""
    token = os.getenv("DISCORD_BOT_TOKEN")
    if not token:
        raise ValueError("DISCORD_BOT_TOKEN environment variable is required")
    
    bot.run(token)


if __name__ == "__main__":
    main()
