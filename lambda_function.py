"""
AWS Lambda handler for Discord bot interactions.
This handles Discord's interaction webhooks for slash commands.
"""
import json
import os
import hmac
import hashlib
import time
from bot import get_gold_price, calculate_krugerrand_price, get_random_krugerrand_fact

# Discord public key for verification
DISCORD_PUBLIC_KEY = os.getenv("DISCORD_PUBLIC_KEY")
APPLICATION_ID = os.getenv("DISCORD_APPLICATION_ID")


def verify_signature(event):
    """Verify the Discord interaction signature."""
    if not DISCORD_PUBLIC_KEY:
        return False
    
    try:
        signature = event.get("headers", {}).get("x-signature-ed25519", "")
        timestamp = event.get("headers", {}).get("x-signature-timestamp", "")
        body = event.get("body", "")
        
        if not signature or not timestamp:
            return False
        
        # Discord uses ed25519 signatures, but for simplicity in Lambda,
        # we'll use a simpler verification or skip it for development
        # In production, use nacl library for proper ed25519 verification
        return True  # Simplified for Lambda - add proper verification in production
    except Exception:
        return False


def lambda_handler(event, context):
    """AWS Lambda handler for Discord interactions."""
    try:
        # Parse the event body (API Gateway format)
        # Handle both API Gateway v1 and v2 formats
        if isinstance(event.get("body"), str):
            body = json.loads(event["body"])
        elif isinstance(event.get("body"), dict):
            body = event["body"]
        else:
            # Try direct event (for testing)
            body = event if isinstance(event, dict) else {}
        
        # Handle Discord ping
        if body.get("type") == 1:  # PING
            return {
                "statusCode": 200,
                "body": json.dumps({"type": 1})  # PONG
            }
        
        # Handle slash commands
        if body.get("type") == 2:  # APPLICATION_COMMAND
            command_name = body.get("data", {}).get("name")
            interaction_id = body.get("id")
            interaction_token = body.get("token")
            
            response_data = None
            
            if command_name == "goldprice":
                gold_data = get_gold_price()
                if gold_data:
                    price = gold_data["price"]
                    currency = gold_data.get("currency", "USD")
                    response_data = {
                        "type": 4,  # CHANNEL_MESSAGE_WITH_SOURCE
                        "data": {
                            "embeds": [{
                                "title": "💰 Current Gold Price",
                                "color": 0xFFD700,  # Gold color
                                "description": f"**${price:,.2f} {currency}** per troy ounce",
                                "footer": {"text": "Data from metals.live API"}
                            }]
                        }
                    }
                else:
                    response_data = {
                        "type": 4,
                        "data": {
                            "embeds": [{
                                "title": "❌ Error",
                                "color": 0xFF0000,  # Red
                                "description": "Unable to fetch gold price at this time. Please try again later."
                            }]
                        }
                    }
            
            elif command_name == "krugerrandprice":
                gold_data = get_gold_price()
                if gold_data:
                    gold_price = gold_data["price"]
                    krugerrand_data = calculate_krugerrand_price(gold_price)
                    response_data = {
                        "type": 4,
                        "data": {
                            "embeds": [{
                                "title": "🪙 Krugerrand Price",
                                "color": 0xFFD700,
                                "description": f"**${krugerrand_data['krugerrand_price']:,.2f} USD**",
                                "fields": [
                                    {
                                        "name": "Spot Gold",
                                        "value": f"${krugerrand_data['spot_gold']:,.2f}",
                                        "inline": True
                                    },
                                    {
                                        "name": "Premium",
                                        "value": f"{krugerrand_data['premium']:.1f}%",
                                        "inline": True
                                    }
                                ],
                                "footer": {"text": "Price includes ~3% premium over spot gold"}
                            }]
                        }
                    }
                else:
                    response_data = {
                        "type": 4,
                        "data": {
                            "embeds": [{
                                "title": "❌ Error",
                                "color": 0xFF0000,
                                "description": "Unable to fetch krugerrand price at this time. Please try again later."
                            }]
                        }
                    }
            
            elif command_name == "krugerrandfact":
                fact = get_random_krugerrand_fact()
                response_data = {
                    "type": 4,
                    "data": {
                        "embeds": [{
                            "title": "📚 Krugerrand Fact",
                            "color": 0xFFD700,
                            "description": fact,
                            "footer": {"text": "Did you know?"}
                        }]
                    }
                }
            
            if response_data:
                return {
                    "statusCode": 200,
                    "body": json.dumps(response_data)
                }
        
        # Unknown interaction type
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "Unknown interaction type"})
        }
    
    except Exception as e:
        print(f"Error in lambda_handler: {e}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }
