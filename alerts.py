import time
import schedule
import asyncio
from crypto_api import get_top_coins, get_multiple_prices, get_all_coins
from user_storage import get_storage

from config import ALERT_THRESHOLD

# Initialize persistent storage
storage = get_storage()

# Load data from persistent storage on startup
subscribers = storage.load_subscribers()
last_prices = storage.load_last_prices()
user_alert_thresholds = storage.load_user_thresholds()
user_coin_subscriptions = storage.load_user_coin_subscriptions()


def get_user_monitored_coins(user_id):
    """
    Get list of coins to monitor for a specific user
    Returns only user's personal coin subscriptions (no default top coins)
    """
    if user_id in user_coin_subscriptions and user_coin_subscriptions[user_id]:
        return user_coin_subscriptions[user_id]
    else:
        return []  # No coins to monitor if user hasn't added any


def add_coin_to_user_subscription(user_id, coin_id):
    """Add a coin to user's personal subscription list"""
    if user_id not in user_coin_subscriptions:
        user_coin_subscriptions[user_id] = []

    if coin_id not in user_coin_subscriptions[user_id]:
        user_coin_subscriptions[user_id].append(coin_id)
        storage.save_user_coin_subscriptions(user_id, user_coin_subscriptions[user_id])
        return True
    return False


def remove_coin_from_user_subscription(user_id, coin_id):
    """Remove a coin from user's personal subscription list"""
    if user_id in user_coin_subscriptions and coin_id in user_coin_subscriptions[user_id]:
        user_coin_subscriptions[user_id].remove(coin_id)
        storage.save_user_coin_subscriptions(user_id, user_coin_subscriptions[user_id])
        return True
    return False


def clear_user_coin_subscriptions(user_id):
    """Clear all user's personal coin subscriptions"""
    if user_id in user_coin_subscriptions:
        user_coin_subscriptions[user_id] = []
        storage.save_user_coin_subscriptions(user_id, user_coin_subscriptions[user_id])
        return True
    return False


def add_subscriber(chat_id):
    """Add a new subscriber"""
    if chat_id not in subscribers:
        subscribers.append(chat_id)
        storage.save_subscribers(subscribers)
        return True
    return False


def remove_subscriber(chat_id):
    """Remove a subscriber"""
    if chat_id in subscribers:
        subscribers.remove(chat_id)
        if chat_id in user_alert_thresholds:
            del user_alert_thresholds[chat_id]
        if chat_id in user_coin_subscriptions:
            del user_coin_subscriptions[chat_id]
        storage.save_subscribers(subscribers)
        for chat_id, threshold in user_alert_thresholds.items():
            storage.save_user_threshold(chat_id, threshold)
        for chat_id, coin_ids in user_coin_subscriptions.items():
            storage.save_user_coin_subscriptions(chat_id, coin_ids)
        return True
    return False


def set_user_alert_threshold(chat_id, threshold):
    """Set alert threshold for a user"""
    user_alert_thresholds[chat_id] = threshold
    storage.save_user_threshold(chat_id, threshold)
    return True


def print_user_statistics():
    """Print current user statistics on startup"""
    print("\n" + "=" * 60)
    print("📊 CURRENT USER STATISTICS")
    print("=" * 60)

    # Total subscribers
    total_subscribers = len(subscribers)
    print(f"👥 Total subscribers: {total_subscribers}")

    if total_subscribers == 0:
        print("ℹ️  No users subscribed yet")
        print("=" * 60)
        return

    # Users with custom thresholds
    custom_thresholds = len(user_alert_thresholds)
    default_thresholds = total_subscribers - custom_thresholds
    print(f"⚙️  Custom thresholds: {custom_thresholds}")
    print(f"📊 Default thresholds: {default_thresholds}")

    # Users with coin subscriptions
    users_with_coins = len([uid for uid in user_coin_subscriptions if user_coin_subscriptions[uid]])
    users_without_coins = total_subscribers - users_with_coins
    print(f"🪙 Users with coin subscriptions: {users_with_coins}")
    print(f"📭 Users without coin subscriptions: {users_without_coins}")

    # Total coins being monitored
    all_coins = set()
    for coin_list in user_coin_subscriptions.values():
        all_coins.update(coin_list)
    total_coins = len(all_coins)
    print(f"🔍 Total unique coins being monitored: {total_coins}")

    # Detailed user breakdown
    print(f"\n📋 DETAILED USER BREAKDOWN:")
    print("-" * 60)

    for i, chat_id in enumerate(subscribers, 1):
        threshold = user_alert_thresholds.get(chat_id, ALERT_THRESHOLD)
        user_coins = user_coin_subscriptions.get(chat_id, [])
        coin_count = len(user_coins)

        print(f"{i:2d}. User {chat_id}")
        print(f"    📊 Threshold: {threshold}%")
        print(f"    🪙 Coins: {coin_count} ({', '.join(user_coins[:3])}{'...' if coin_count > 3 else ''})")
        print()

    print("=" * 60)


async def check_prices(bot):
    """
    Check prices for monitored coins and send alerts for significant changes
    """
    # Get all unique coins that need to be monitored from all subscribers
    all_monitored_coins = set()

    # Add coins for each subscriber
    for chat_id in subscribers:
        user_coins = get_user_monitored_coins(chat_id)
        all_monitored_coins.update(user_coins)

    monitored_coins = list(all_monitored_coins)

    if not monitored_coins:
        print("No personal coin subscriptions to monitor")
        return

    # Get prices for all monitored coins at once (more efficient)
    current_prices = await get_multiple_prices(monitored_coins)

    for coin_id in monitored_coins:
        current_price = current_prices.get(coin_id)
        if current_price is None:
            continue

        last_price = last_prices.get(coin_id)
        if last_price:
            # Calculate percentage change
            change = abs((current_price - last_price) / last_price) * 100

            # Send alerts only to subscribers who are monitoring this specific coin
            for chat_id in subscribers:
                user_coins = get_user_monitored_coins(chat_id)

                # Only send alert if user is monitoring this specific coin
                if coin_id in user_coins:
                    # Get user's custom threshold or use default
                    user_threshold = user_alert_thresholds.get(chat_id, ALERT_THRESHOLD)

                    if change >= user_threshold:
                        # Determine if price went up or down
                        direction = "📈" if current_price > last_price else "📉"

                        # Get coin name for better message
                        from crypto_api import get_coin_by_id
                        coin_info = await get_coin_by_id(coin_id)
                        coin_name = coin_info['name'] if coin_info else coin_id

                        # Format price properly
                        if current_price < 0.01:
                            price_display = f"${current_price:.6f}".rstrip('0').rstrip('.')
                        elif current_price < 1:
                            price_display = f"${current_price:.4f}".rstrip('0').rstrip('.')
                        else:
                            price_display = f"${current_price:,.2f}"

                        if last_price < 0.01:
                            last_price_display = f"${last_price:.6f}".rstrip('0').rstrip('.')
                        elif last_price < 1:
                            last_price_display = f"${last_price:.4f}".rstrip('0').rstrip('.')
                        else:
                            last_price_display = f"${last_price:,.2f}"

                        message = (
                            f"⚠️ *Price Alert* ⚠️\n\n"
                            f"{direction} *{coin_name}* price changed by *{change:.2f}%*\n"
                            f"📊 *Your threshold:* {user_threshold}%\n\n"
                            f"💰 **Current Price:** {price_display}\n"
                            f"📈 **Previous Price:** {last_price_display}\n"
                            f"🔄 **Change:** {direction} {change:.2f}%"
                        )

                        try:
                            # Send message using asyncio.ensure_future
                            import asyncio
                            asyncio.ensure_future(
                                bot.send_message(chat_id=chat_id, text=message, parse_mode='Markdown'))
                            print(f"🚨 Alert sent to user {chat_id} for {coin_name}")
                        except Exception as e:
                            print(f"❌ Failed to send alert to user {chat_id}: {e}")

        # Update last known price
        last_prices[coin_id] = current_price

    storage.save_last_prices(last_prices)


def start_alerts(bot):
    """
    Start the price alert monitoring system
    Monitors personal coin subscriptions and sends alerts for significant changes
    """
    print(f"🔔 Starting price alert monitoring system...")
    print(f"📊 Monitoring: Personal coin subscriptions only")
    print(f"⚡ Alert threshold: {ALERT_THRESHOLD}% price change")

    # Check prices every 5 minutes
    schedule.every(5).minutes.do(lambda: asyncio.run(check_prices(bot)))

    while True:
        schedule.run_pending()
        time.sleep(1)


async def start_alerts_async(bot):
    """
    Start the price alert monitoring system asynchronously
    """
    print(f"🔔 Starting price alert monitoring system...")
    print(f"📊 Monitoring: Personal coin subscriptions only")
    print(f"⚡ Alert threshold: {ALERT_THRESHOLD}% price change")

    # Check prices every 5 minutes
    while True:
        try:
            await check_prices(bot)
        except Exception as e:
            print(f"❌ Error in price check: {e}")

        # Wait 5 minutes
        await asyncio.sleep(300)  # 300 seconds = 5 minutes
