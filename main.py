# CryptoPriceBot - Main entry point
# Telegram bot for cryptocurrency prices

def run_telegram():
    """Run Telegram bot"""
    try:
        from telegram_bot import run_telegram_bot
        from alerts import print_user_statistics
        print("🤖 Starting Telegram bot...")

        # Show user statistics before starting
        print_user_statistics()

        run_telegram_bot()
    except Exception as e:
        print(f"❌ Telegram bot error: {e}")


if __name__ == "__main__":
    print("🚀 Starting CryptoPriceBot...")
    print("=" * 50)
    run_telegram()