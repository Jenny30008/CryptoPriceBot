import threading
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
from crypto_api import (
    get_price, get_coin_by_symbol, get_coin_by_id,
    search_coins, get_top_coins, get_multiple_prices,
    get_supported_currencies, get_currency_symbol
)
from alerts import (
    start_alerts, start_alerts_async, subscribers,
    add_coin_to_user_subscription, remove_coin_from_user_subscription,
    clear_user_coin_subscriptions, get_user_monitored_coins,
    add_subscriber, remove_subscriber, set_user_alert_threshold
)
from user_storage import get_storage

# Import configuration
from config import TELEGRAM_API_TOKEN, ALERT_THRESHOLD

# Telegram bot configuration
API_TOKEN = TELEGRAM_API_TOKEN


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Welcome message and bot introduction"""
    chat_id = update.effective_chat.id
    username = update.effective_user.username
    print(f"📱 /start received from {username} ({chat_id})")

    welcome_text = (
        "🤖 *CryptoPriceBot*\n\n"
        "Real-time crypto prices from CoinGecko!\n"
        "18,000+ cryptocurrencies supported 🚀\n\n"
        "💡 *Quick Start:*\n"
        "• `/price btc` - Get Bitcoin price\n"
        "• `/search doge` - Find Dogecoin\n"
        "• `/addcoin eth` - Add Ethereum to alerts\n\n"
        "📋 Use `/help` for all commands"
    )

    await update.message.reply_text(welcome_text, parse_mode='Markdown')


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show detailed help information"""
    help_text = (
        "📋 *Complete Command Reference*\n\n"
        "🔍 *Price Commands:*\n"
        "• `/price <coin>` - Get current price in USD\n"
        "• `/price <coin> <currency>` - Get price in specific currency\n"
        "• `/prices <coin1> <coin2> ...` - Multiple prices in USD (max 10)\n"
        "• `/prices <coin1> <coin2> <currency>` - Multiple prices in specific currency\n"
        "• `/currencies` - Show supported currencies\n\n"
        "🔎 *Search Commands:*\n"
        "• `/search <query>` - Search by name or symbol\n"
        "• `/top [limit]` - Top coins by market cap (max 50)\n\n"
        "🔔 *Alert Commands:*\n"
        "• `/subscribe [threshold]` - Subscribe to price alerts\n"
        "• `/unsubscribe` - Unsubscribe from alerts\n"
        "• `/settings` - Show your alert settings\n\n"
        "🪙 *Personal Coin Alerts:*\n"
        "• `/addcoin <coin>` - Add coin to personal alerts\n"
        "• `/removecoin <coin>` - Remove coin from personal alerts\n"
        "• `/mycoins` - Show your personal coin subscriptions\n"
        "• `/clearcoins` - Clear all personal subscriptions\n\n"
        "ℹ️ *Other Commands:*\n"
        "• `/start` - Welcome message\n"
        "• `/help` - This help message\n\n"
        "💡 *Usage Tips:*\n"
        "• Use coin names, symbols, or IDs\n"
        "• Search is case-insensitive\n"
        "• Threshold range: 0.1% - 50%\n"
        "• Supports 18,000+ cryptocurrencies\n\n"
        "🎯 *Examples:*\n"
        "`/price btc` `/price ethereum eur` `/search doge`\n"
        "`/top 20` `/subscribe 2.5` `/prices btc eth rub`\n"
        "`/currencies` `/price doge jpy`"
    )

    await update.message.reply_text(help_text, parse_mode='Markdown')


async def currencies(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show supported currencies"""
    try:
        supported_currencies = await get_supported_currencies()

        # Get common currencies for display
        common_currencies = ['usd', 'eur', 'gbp', 'jpy', 'cad', 'aud', 'chf', 'cny', 'rub', 'inr', 'brl', 'krw', 'mxn',
                             'sek', 'nok', 'dkk', 'pln', 'czk', 'huf', 'try', 'zar', 'thb', 'sgd', 'hkd', 'nzd', 'php',
                             'myr', 'idr', 'vnd', 'uah']

        # Filter to show only common currencies
        display_currencies = [curr for curr in common_currencies if curr in supported_currencies]

        currencies_text = "💱 *Supported Currencies*\n\n"
        currencies_text += "**Common Currencies:**\n"

        # Group currencies by region
        regions = {
            "Americas": ['usd', 'cad', 'aud', 'brl', 'mxn'],
            "Europe": ['eur', 'gbp', 'chf', 'sek', 'nok', 'dkk', 'pln', 'czk', 'huf', 'try', 'bgn', 'hrk', 'ron', 'rsd',
                       'isk'],
            "Asia": ['jpy', 'cny', 'krw', 'inr', 'thb', 'sgd', 'hkd', 'nzd', 'php', 'myr', 'idr', 'vnd'],
            "Others": ['rub', 'zar', 'uah']
        }

        for region, currencies in regions.items():
            available_currencies = [curr for curr in currencies if curr in supported_currencies]
            if available_currencies:
                currencies_text += f"\n**{region}:**\n"
                for curr in available_currencies:
                    symbol = get_currency_symbol(curr)
                    currencies_text += f"• {curr.upper()} {symbol}\n"

        currencies_text += f"\n**Total supported:** {len(supported_currencies)} currencies\n\n"
        currencies_text += "**Usage:**\n"
        currencies_text += "• `/price btc eur` - Bitcoin in Euros\n"
        currencies_text += "• `/prices btc eth rub` - Multiple coins in Rubles\n"
        currencies_text += "• `/price doge jpy` - Dogecoin in Yen"

        await update.message.reply_text(currencies_text, parse_mode='Markdown')

    except Exception as e:
        await update.message.reply_text(
            "❌ Error fetching supported currencies. Please try again later.",
            parse_mode='Markdown'
        )


async def price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get current price of a cryptocurrency"""
    chat_id = update.effective_chat.id
    username = update.effective_user.username
    print(f"💰 /price received from {username} ({chat_id})")

    if len(context.args) == 0:
        await update.message.reply_text(
            "❌ Please provide a coin name or symbol.\n\n"
            "Usage: `/price bitcoin` or `/price btc`\n"
            "Usage: `/price bitcoin eur` or `/price btc rub`\n"
            "Example: `/price ethereum`",
            parse_mode='Markdown'
        )
        return

    # Parse arguments: coin and optional currency
    coin_input = context.args[0].lower()
    currency = 'usd'  # Default currency

    if len(context.args) > 1:
        currency = context.args[1].lower()

    # Try to find the coin (get_coin_by_symbol now uses popularity scoring)
    coin_info = await get_coin_by_symbol(coin_input)

    if not coin_info:
        # Search for coins by name or symbol
        search_results = await search_coins(coin_input, limit=5)
        if search_results:
            # If multiple results, show options with inline keyboard
            if len(search_results) > 1:
                keyboard = []
                for i, coin in enumerate(search_results[:5], 1):
                    keyboard.append([InlineKeyboardButton(
                        f"{i}. {coin['name']} ({coin['symbol'].upper()})",
                        callback_data=f"price_{coin['id']}"
                    )])

                reply_markup = InlineKeyboardMarkup(keyboard)
                await update.message.reply_text(
                    f"🔍 *Multiple coins found for: {coin_input}*\n\n"
                    "Please select the correct coin:",
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
                return
            else:
                coin_info = search_results[0]
        else:
            await update.message.reply_text(
                f"❌ No coin found with name or symbol: `{coin_input}`\n\n"
                "Try using `/search {coin_input}` to find similar coins.",
                parse_mode='Markdown'
            )
            return

    # Get price for the found coin in specified currency
    price_value = await get_price(coin_info['id'], currency)
    if price_value is None:
        await update.message.reply_text(f"❌ Error fetching price in {currency.upper()}. Please try again later.")
        return

    # Get currency symbol
    currency_symbol = get_currency_symbol(currency)

    # Format price with proper formatting
    if price_value < 0.01:
        # For very small prices, show more decimal places
        price_display = f"{currency_symbol}{price_value:.6f}".rstrip('0').rstrip('.')
    elif price_value < 1:
        # For small prices, show 4 decimal places
        price_display = f"{currency_symbol}{price_value:.4f}".rstrip('0').rstrip('.')
    else:
        # For normal prices, show 2 decimal places with commas
        price_display = f"{currency_symbol}{price_value:,.2f}"

    price_text = (
        f"💰 *{coin_info['name']} ({coin_info['symbol'].upper()})*\n\n"
        f"💵 **Current Price:** {price_display} ({currency.upper()})\n"
        f"🆔 **Coin ID:** `{coin_info['id']}`"
    )

    await update.message.reply_text(price_text, parse_mode='Markdown')


async def search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Search for cryptocurrencies"""
    chat_id = update.effective_chat.id
    username = update.effective_user.username
    print(f"🔍 /search received from {username} ({chat_id})")

    if len(context.args) == 0:
        await update.message.reply_text(
            "❌ Please provide a search query.\n\n"
            "Usage: `/search bitcoin` or `/search btc`",
            parse_mode='Markdown'
        )
        return

    query = ' '.join(context.args)
    search_results = await search_coins(query, limit=10)

    if not search_results:
        await update.message.reply_text(f"❌ No coins found matching: `{query}`", parse_mode='Markdown')
        return

    # Create inline keyboard for search results
    keyboard = []
    for coin in search_results[:10]:
        keyboard.append([InlineKeyboardButton(
            f"{coin['name']} ({coin['symbol'].upper()})",
            callback_data=f"price_{coin['id']}"
        )])

    reply_markup = InlineKeyboardMarkup(keyboard)

    search_text = f"🔍 *Search results for: {query}*\n\nFound {len(search_results)} coins. Tap to get price:"

    await update.message.reply_text(
        search_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )


async def top(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show top cryptocurrencies by market cap"""
    limit = 10
    if len(context.args) > 0:
        try:
            limit = int(context.args[0])
            if limit > 50:
                limit = 50
        except ValueError:
            pass

    top_coins = await get_top_coins(limit)
    if not top_coins:
        await update.message.reply_text("❌ Error fetching top coins. Please try again later.")
        return

    # Create inline keyboard for top coins
    keyboard = []
    for coin in top_coins:
        keyboard.append([InlineKeyboardButton(
            f"{coin['name']} ({coin['symbol'].upper()})",
            callback_data=f"price_{coin['id']}"
        )])

    reply_markup = InlineKeyboardMarkup(keyboard)

    top_text = f"🏆 *Top {len(top_coins)} Cryptocurrencies by Market Cap*\n\nTap any coin to get its current price:"

    await update.message.reply_text(
        top_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )


async def prices(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get prices for multiple cryptocurrencies"""
    if len(context.args) == 0:
        await update.message.reply_text(
            "❌ Please provide coin names or symbols.\n\n"
            "Usage: `/prices bitcoin ethereum cardano`\n"
            "Usage: `/prices bitcoin ethereum eur` or `/prices btc eth rub`",
            parse_mode='Markdown'
        )
        return

    # Parse arguments: coins and optional currency
    coin_list = context.args[:-1] if len(context.args) > 1 else context.args
    currency = 'usd'  # Default currency

    # Check if last argument is a currency
    if len(context.args) > 1:
        last_arg = context.args[-1].lower()
        # Check if it's a valid currency (3-letter code)
        if len(last_arg) == 3 and last_arg.isalpha():
            currency = last_arg
            coin_list = context.args[:-1]

    if len(coin_list) > 10:
        await update.message.reply_text("❌ Maximum 10 coins allowed per request.")
        return

    coin_ids = []
    coin_names = []

    # Find coin IDs for each input
    for coin_input in coin_list:
        coin_info = await get_coin_by_symbol(coin_input.lower())
        if not coin_info:
            search_results = await search_coins(coin_input, limit=1)
            if search_results:
                coin_info = search_results[0]

        if coin_info:
            coin_ids.append(coin_info['id'])
            coin_names.append(f"{coin_info['name']} ({coin_info['symbol'].upper()})")
        else:
            coin_names.append(f"{coin_input} (not found)")

    if not coin_ids:
        await update.message.reply_text("❌ No valid coins found.")
        return

    # Get prices for all coins in specified currency
    prices = await get_multiple_prices(coin_ids, currency)

    # Get currency symbol
    currency_symbol = get_currency_symbol(currency)

    prices_text = f"💰 *Multiple Cryptocurrency Prices ({currency.upper()})*\n\n"
    for i, coin_id in enumerate(coin_ids):
        price = prices.get(coin_id, "N/A")
        if price != "N/A":
            # Format price with proper formatting
            if price < 0.01:
                price_display = f"{currency_symbol}{price:.6f}".rstrip('0').rstrip('.')
            elif price < 1:
                price_display = f"{currency_symbol}{price:.4f}".rstrip('0').rstrip('.')
            else:
                price_display = f"{currency_symbol}{price:,.2f}"
            prices_text += f"• {coin_names[i]}: {price_display}\n"
        else:
            prices_text += f"• {coin_names[i]}: Price unavailable\n"

    await update.message.reply_text(prices_text, parse_mode='Markdown')


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle inline keyboard button presses"""
    query = update.callback_query
    await query.answer()

    if query.data.startswith("price_"):
        coin_id = query.data[6:]  # Remove "price_" prefix
        coin_info = await get_coin_by_id(coin_id)

        if not coin_info:
            await query.edit_message_text("❌ Coin not found.")
            return

        price_value = await get_price(coin_id)
        if price_value is None:
            await query.edit_message_text("❌ Error fetching price. Please try again later.")
            return

        # Format price with proper formatting
        if price_value < 0.01:
            # For very small prices, show more decimal places
            price_display = f"${price_value:.6f}".rstrip('0').rstrip('.')
        elif price_value < 1:
            # For small prices, show 4 decimal places
            price_display = f"${price_value:.4f}".rstrip('0').rstrip('.')
        else:
            # For normal prices, show 2 decimal places with commas
            price_display = f"${price_value:,.2f}"

        price_text = (
            f"💰 *{coin_info['name']} ({coin_info['symbol'].upper()})*\n\n"
            f"💵 **Current Price:** {price_display}\n"
            f"🆔 **Coin ID:** `{coin_info['id']}`"
        )

        await query.edit_message_text(price_text, parse_mode='Markdown')

    elif query.data.startswith("add_"):
        coin_id = query.data[4:]  # Remove "add_" prefix
        coin_info = await get_coin_by_id(coin_id)

        if not coin_info:
            await query.edit_message_text("❌ Coin not found.")
            return

        # Add coin to user's subscription
        chat_id = query.from_user.id
        success = add_coin_to_user_subscription(chat_id, coin_id)

        if success:
            await query.edit_message_text(
                f"✅ Added *{coin_info['name']}* to your alert subscription!\n"
                f"🪙 You will now receive alerts for {coin_info['name']}",
                parse_mode='Markdown'
            )
        else:
            await query.edit_message_text(
                f"ℹ️ *{coin_info['name']}* is already in your alert subscription.",
                parse_mode='Markdown'
            )


async def subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Subscribe to price alerts with custom threshold"""
    chat_id = update.effective_chat.id

    # Check if user provided custom threshold
    if len(context.args) > 0:
        try:
            threshold = float(context.args[0])
            if threshold < 0.1 or threshold > 50:
                await update.message.reply_text(
                    "❌ Alert threshold must be between 0.1% and 50%.\n"
                    "Usage: `/subscribe [threshold]`\n"
                    "Example: `/subscribe 3.5`",
                    parse_mode='Markdown'
                )
                return

            # Store custom threshold for this user
            set_user_alert_threshold(chat_id, threshold)

            if chat_id not in subscribers:
                add_subscriber(chat_id)
                await update.message.reply_text(
                    f"✅ You are now subscribed to price alerts!\n"
                    f"📊 Alert threshold: {threshold}%",
                    parse_mode='Markdown'
                )
            else:
                await update.message.reply_text(
                    f"✅ Alert threshold updated!\n"
                    f"📊 New threshold: {threshold}%",
                    parse_mode='Markdown'
                )
            print(f"✅ User {chat_id} subscribed with {threshold}% threshold")
            return

        except ValueError:
            await update.message.reply_text(
                "❌ Invalid threshold format.\n"
                "Usage: `/subscribe [threshold]`\n"
                "Example: `/subscribe 3.5`",
                parse_mode='Markdown'
            )
            return

    # Default subscription
    if chat_id not in subscribers:
        add_subscriber(chat_id)
        await update.message.reply_text(
            f"✅ You are now subscribed to price alerts!\n"
            f"📊 Default threshold: {ALERT_THRESHOLD}%\n\n"
            f"💡 Add coins with `/addcoin <coin>` to start receiving alerts!\n"
            f"💡 Set custom threshold with `/subscribe 2.5`",
            parse_mode='Markdown'
        )
        print(f"✅ User {chat_id} subscribed with default threshold")
    else:
        await update.message.reply_text(
            f"ℹ️ You are already subscribed to price alerts.\n"
            f"📊 Current threshold: {ALERT_THRESHOLD}%\n\n"
            f"💡 Add coins with `/addcoin <coin>` to start receiving alerts!\n"
            f"💡 Change threshold with `/subscribe 2.5`",
            parse_mode='Markdown'
        )


async def unsubscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Unsubscribe from price alerts"""
    chat_id = update.effective_chat.id
    if chat_id in subscribers:
        remove_subscriber(chat_id)
        await update.message.reply_text("✅ You have been unsubscribed from price alerts.")
        print(f"❌ User {chat_id} unsubscribed")
    else:
        await update.message.reply_text("ℹ️ You were not subscribed to price alerts.")


async def settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show current alert settings"""
    chat_id = update.effective_chat.id
    from alerts import user_alert_thresholds

    if chat_id in subscribers:
        threshold = user_alert_thresholds.get(chat_id, ALERT_THRESHOLD)
        user_coins = get_user_monitored_coins(chat_id)
        coin_count = len(user_coins) if user_coins else 0

        settings_text = (
            f"⚙️ *Your Alert Settings*\n\n"
            f"📊 **Status:** Subscribed ✅\n"
            f"📈 **Threshold:** {threshold}%\n"
            f"🪙 **Monitored Coins:** {coin_count} personal coins\n\n"
            f"💡 *Commands:*\n"
            f"• `/addcoin <coin>` - Add coin to alerts\n"
            f"• `/mycoins` - View your coins\n"
            f"• `/subscribe [threshold]` - Change threshold\n"
            f"• `/unsubscribe` - Stop alerts"
        )
    else:
        settings_text = (
            f"⚙️ *Your Alert Settings*\n\n"
            f"📊 **Status:** Not subscribed ❌\n"
            f"📈 **Default Threshold:** {ALERT_THRESHOLD}%\n\n"
            f"💡 *Commands:*\n"
            f"• `/subscribe` - Subscribe to alerts\n"
            f"• `/addcoin <coin>` - Add coin to alerts\n"
            f"• `/mycoins` - View your coins"
        )

    await update.message.reply_text(settings_text, parse_mode='Markdown')


async def add_coin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Add a coin to personal alert subscription"""
    chat_id = update.effective_chat.id
    username = update.effective_user.username
    print(f"➕ /addcoin received from {username} ({chat_id})")

    if len(context.args) == 0:
        await update.message.reply_text(
            "❌ Please provide a coin name or symbol.\n\n"
            "Usage: `/addcoin bitcoin` or `/addcoin btc`",
            parse_mode='Markdown'
        )
        return

    coin_input = ' '.join(context.args).lower()

    # Find the coin
    coin_info = await get_coin_by_symbol(coin_input)
    if not coin_info:
        search_results = await search_coins(coin_input, limit=5)
        if search_results:
            if len(search_results) > 1:
                keyboard = []
                for i, coin in enumerate(search_results[:5], 1):
                    keyboard.append([InlineKeyboardButton(
                        f"{i}. {coin['name']} ({coin['symbol'].upper()})",
                        callback_data=f"add_{coin['id']}"
                    )])

                reply_markup = InlineKeyboardMarkup(keyboard)
                await update.message.reply_text(
                    f"🔍 *Multiple coins found for: {coin_input}*\n\n"
                    "Please select the coin to add:",
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
                return
            else:
                coin_info = search_results[0]
        else:
            await update.message.reply_text(
                f"❌ No coin found with name or symbol: `{coin_input}`",
                parse_mode='Markdown'
            )
            return

    # Add coin to user's subscription
    success = add_coin_to_user_subscription(chat_id, coin_info['id'])

    if success:
        await update.message.reply_text(
            f"✅ Added *{coin_info['name']} ({coin_info['symbol'].upper()})* to your alert subscription!\n"
            f"🪙 You will now receive alerts for {coin_info['name']}\n"
            f"🆔 **Coin ID:** `{coin_info['id']}`",
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            f"ℹ️ *{coin_info['name']} ({coin_info['symbol'].upper()})* is already in your alert subscription.",
            parse_mode='Markdown'
        )


async def remove_coin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Remove a coin from personal alert subscription"""
    chat_id = update.effective_chat.id
    username = update.effective_user.username
    print(f"➖ /removecoin received from {username} ({chat_id})")

    if len(context.args) == 0:
        await update.message.reply_text(
            "❌ Please provide a coin name or symbol.\n\n"
            "Usage: `/removecoin bitcoin` or `/removecoin btc`",
            parse_mode='Markdown'
        )
        return

    coin_input = ' '.join(context.args).lower()

    # Find the coin
    coin_info = await get_coin_by_symbol(coin_input)
    if not coin_info:
        search_results = await search_coins(coin_input, limit=1)
        if search_results:
            coin_info = search_results[0]
        else:
            await update.message.reply_text(
                f"❌ No coin found with name or symbol: `{coin_input}`",
                parse_mode='Markdown'
            )
            return

    # Remove coin from user's subscription
    success = remove_coin_from_user_subscription(chat_id, coin_info['id'])

    if success:
        await update.message.reply_text(
            f"✅ Removed *{coin_info['name']}* from your alert subscription!",
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            f"ℹ️ *{coin_info['name']}* was not in your alert subscription.",
            parse_mode='Markdown'
        )


async def my_coins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user's personal coin subscriptions"""
    chat_id = update.effective_chat.id
    username = update.effective_user.username
    print(f"📋 /mycoins received from {username} ({chat_id})")

    user_coins = get_user_monitored_coins(chat_id)

    if not user_coins:
        await update.message.reply_text(
            "📋 *Your Coin Subscriptions*\n\n"
            "You are not subscribed to any coins.\n"
            "No alerts will be sent until you add coins.\n\n"
            "💡 Use `/addcoin <coin>` to add specific coins!\n"
            "💡 Use `/subscribe` to enable alerts",
            parse_mode='Markdown'
        )
        return

    # Get coin names
    coin_names = []
    for coin_id in user_coins:
        coin_info = await get_coin_by_id(coin_id)
        if coin_info:
            coin_names.append(f"• {coin_info['name']} ({coin_info['symbol'].upper()})")
        else:
            coin_names.append(f"• {coin_id}")

    coins_text = "\n".join(coin_names[:20])  # Limit to 20 coins
    if len(coin_names) > 20:
        coins_text += f"\n... and {len(coin_names) - 20} more coins"

    await update.message.reply_text(
        f"📋 *Your Coin Subscriptions* ({len(user_coins)} coins)\n\n"
        f"{coins_text}\n\n"
        f"💡 *Commands:*\n"
        f"• `/addcoin <coin>` - Add a coin\n"
        f"• `/removecoin <coin>` - Remove a coin\n"
        f"• `/clearcoins` - Clear all subscriptions",
        parse_mode='Markdown'
    )


async def clear_coins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Clear all personal coin subscriptions"""
    chat_id = update.effective_chat.id

    success = clear_user_coin_subscriptions(chat_id)

    if success:
        await update.message.reply_text(
            "✅ Cleared all your personal coin subscriptions!\n"
            "No alerts will be sent until you add coins again.",
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            "ℹ️ You had no personal coin subscriptions to clear.",
            parse_mode='Markdown'
        )


async def backup_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Create data backup (admin only)"""
    chat_id = update.effective_chat.id
    username = update.effective_user.username
    print(f"💾 /backup received from {username} ({chat_id})")

    # Simple admin check - you can modify this
    if chat_id not in [123456789]:  # Replace with your admin chat_id
        await update.message.reply_text("❌ This command is for administrators only.")
        return

    storage = get_storage()
    success = storage.backup_data()

    if success:
        await update.message.reply_text("✅ Data backup created successfully!")
    else:
        await update.message.reply_text("❌ Failed to create backup.")


async def restore_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Restore data from backup (admin only)"""
    chat_id = update.effective_chat.id
    username = update.effective_user.username
    print(f"🔄 /restore received from {username} ({chat_id})")

    if chat_id not in [123456789]:  # Replace with your admin chat_id
        await update.message.reply_text("❌ This command is for administrators only.")
        return

    if len(context.args) == 0:
        await update.message.reply_text(
            "❌ Please provide backup file path.\n\n"
            "Usage: `/restore backup_20231201_120000.json`",
            parse_mode='Markdown'
        )
        return

    backup_path = context.args[0]
    storage = get_storage()
    success = storage.restore_data(backup_path)

    if success:
        await update.message.reply_text("✅ Data restored successfully!")
    else:
        await update.message.reply_text("❌ Failed to restore data.")


def run_telegram_bot():
    """Start the Telegram bot"""
    app = ApplicationBuilder().token(API_TOKEN).build()

    # Add command handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("price", price))
    app.add_handler(CommandHandler("search", search))
    app.add_handler(CommandHandler("top", top))
    app.add_handler(CommandHandler("prices", prices))
    app.add_handler(CommandHandler("currencies", currencies))
    app.add_handler(CommandHandler("subscribe", subscribe))
    app.add_handler(CommandHandler("unsubscribe", unsubscribe))
    app.add_handler(CommandHandler("settings", settings))
    app.add_handler(CommandHandler("addcoin", add_coin))
    app.add_handler(CommandHandler("removecoin", remove_coin))
    app.add_handler(CommandHandler("mycoins", my_coins))
    app.add_handler(CommandHandler("clearcoins", clear_coins))
    app.add_handler(CommandHandler("backup", backup_data))
    app.add_handler(CommandHandler("restore", restore_data))

    # Add callback query handler for inline keyboards
    app.add_handler(CallbackQueryHandler(button_callback))

    print("🤖 Telegram bot starting...")

    # Start price alerts in a separate thread after app is created
    def start_alerts_wrapper():
        # Wait a moment for the app to initialize
        import time
        time.sleep(2)
        # Run alerts in a new event loop
        asyncio.run(start_alerts_async(app.bot))

    threading.Thread(target=start_alerts_wrapper, daemon=True).start()

    app.run_polling()


if __name__ == "__main__":
    run_telegram_bot()
