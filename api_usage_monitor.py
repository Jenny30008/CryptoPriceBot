#!/usr/bin/env python3
"""
API Usage Monitor for CryptoPriceBot
Shows current API usage and rate limit status
"""

import time
import requests
from datetime import datetime, timedelta


def check_api_status():
    """Check CoinGecko API status and rate limits"""
    print("🔍 CoinGecko API Status Check")
    print("=" * 40)

    try:
        # Test API call
        url = "https://api.coingecko.com/api/v3/ping"
        response = requests.get(url, timeout=10)

        if response.status_code == 200:
            print("✅ API Status: Online")

            # Check rate limit headers
            rate_limit = response.headers.get('X-RateLimit-Limit')
            rate_remaining = response.headers.get('X-RateLimit-Remaining')
            rate_reset = response.headers.get('X-RateLimit-Reset')

            if rate_limit:
                print(f"📊 Rate Limit: {rate_limit} calls/minute")
            if rate_remaining:
                print(f"🔄 Remaining: {rate_remaining} calls")
            if rate_reset:
                reset_time = datetime.fromtimestamp(int(rate_reset))
                print(f"⏰ Reset Time: {reset_time.strftime('%H:%M:%S')}")

            # Test price endpoint
            price_url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"
            price_response = requests.get(price_url, timeout=10)

            if price_response.status_code == 200:
                print("✅ Price API: Working")
                data = price_response.json()
                if 'bitcoin' in data:
                    print(f"💰 Bitcoin Price: ${data['bitcoin']['usd']:,.2f}")
            else:
                print(f"❌ Price API Error: {price_response.status_code}")

        else:
            print(f"❌ API Status: Error {response.status_code}")

    except Exception as e:
        print(f"❌ Connection Error: {e}")

    print("\n📋 Free Tier Limits:")
    print("• 30 calls per minute")
    print("• 10,000 calls per month")
    print("• Perfect for personal use")

    print("\n💡 Tips to stay within limits:")
    print("• Bot checks prices every 5 minutes")
    print("• Uses caching to reduce API calls")
    print("• Batches multiple requests when possible")


if __name__ == "__main__":
    check_api_status()
