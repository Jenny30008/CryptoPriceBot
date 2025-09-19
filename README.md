# CryptoPriceBot

<div align="center">

**Python 3.11+** • **Telegram Bot** • **CoinGecko API** • **MIT License**

A comprehensive cryptocurrency price bot for Telegram. Get real-time prices for all cryptocurrencies available on CoinGecko!

</div>

> ⚠️ **Note**: This bot uses CoinGecko's free API tier with rate limits (30 calls/minute, 10K/month). Perfect for personal use and small projects!

---

## 📌 Features

<details open>
<summary><strong>Core Features</strong></summary>

- 🔍 **Universal Support**: Access to all cryptocurrencies on CoinGecko (10,000+ coins)
- 💰 **Multi-Currency Prices**: Get prices in 100+ fiat currencies (USD, EUR, GBP, JPY, RUB, etc.)
- 🔎 **Smart Search**: Search by coin name, symbol, or ID with intelligent prioritization
- 📊 **Top Coins**: View top cryptocurrencies by market cap
- 💵 **Multiple Prices**: Get prices for multiple coins at once in any currency
- 🔔 **Personal Price Alerts**: Subscribe to alerts for specific coins with custom thresholds (0.1% - 50%)
- 💾 **Persistent Storage**: User settings and subscriptions are saved between bot restarts
- 🎯 **Interactive UI**: Inline keyboards for easy navigation (Telegram)
- 📱 **Telegram Integration**: Native Telegram bot with interactive commands
- 🌍 **International Support**: Currency symbols and formatting for global users

</details>

---

## 🚀 Getting Started

<details>
<summary><strong>Prerequisites</strong></summary>

- Python 3.11 or higher
- Telegram Bot Token (from [@BotFather](https://t.me/botfather))
- CoinGecko API access (free)

</details>

<details>
<summary><strong>Installation Steps</strong></summary>

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Jenny30008/CryptoPriceBot.git
   cd CryptoPriceBot
   ```

2. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure your bot:**
   - Copy `config_example.py` to `config.py`
   - Add your Telegram Bot Token:
     ```python
     TELEGRAM_API_TOKEN = "your_bot_token_here"
     ```

4. **Run the bot:**
   ```bash
   python main.py
   ```
</details>

---

## 🎮 Commands

<details>
<summary><strong>Basic Commands</strong></summary>

- `/start` - Welcome message and bot introduction
- `/price bitcoin` - Get Bitcoin price in USD
- `/price ethereum eur` - Get Ethereum price in EUR
- `/search btc` - Search for cryptocurrencies
- `/top` - View top cryptocurrencies by market cap
- `/currencies` - List supported fiat currencies

</details>

<details>
<summary><strong>Alert Management</strong></summary>

- `/subscribe` - Subscribe to price alerts
- `/addcoin bitcoin` - Add Bitcoin to monitoring
- `/mycoins` - View your monitored coins
- `/settings` - Manage alert preferences
- `/unsubscribe` - Stop receiving alerts

</details>

<details>
<summary><strong>Admin Commands</strong></summary>

- `/backup` - Create data backup (admin only)
- `/restore` - Restore from backup (admin only)

</details>

---

## 📖 Usage Examples

<details>
<summary><strong>Price Lookup</strong></summary>

```
/price bitcoin
/price ethereum eur
/prices btc eth ada
```
</details>

<details>
<summary><strong>Multi-Currency Support</strong></summary>

```
/price bitcoin usd
/price ethereum eur
/price cardano rub
/currencies
```
</details>

<details>
<summary><strong>Alert System</strong></summary>

```
/subscribe
/addcoin bitcoin
/addcoin ethereum
/mycoins
/settings
```
</details>

---

## 🔧 Technical Details

<details>
<summary><strong>Technologies Used</strong></summary>

- **Python 3.11+** - Core programming language
- **python-telegram-bot** - Telegram Bot API wrapper
- **httpx** - Async HTTP client for API calls
- **asyncio** - Asynchronous programming
- **JSON** - Data persistence

</details>

<details>
<summary><strong>API Integration</strong></summary>

- **CoinGecko API** - Cryptocurrency data source
- **Rate Limiting** - 30 calls/minute (free tier)
- **Error Handling** - Robust error management

</details>

<details>
<summary><strong>Performance</strong></summary>

- **Async Operations** - Non-blocking API calls
- **Efficient Monitoring** - 5-minute price checks
- **Memory Optimized** - Lightweight data storage

</details>

---

## 📁 Project Structure

```
CryptoPriceBot/
├── main.py                  # Main entry point
├── crypto_api.py            # CoinGecko API integration
├── telegram_bot.py          # Telegram bot implementation
├── alerts.py                # Price alert system
├── user_storage.py          # Persistent data storage
├── config.py                # Configuration settings
├── requirements.txt         # Python dependencies
├── user_data.json           # User data storage (auto-created)
└── README.md               # This file
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.