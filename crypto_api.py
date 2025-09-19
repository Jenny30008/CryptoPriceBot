import httpx
import json
import time
import asyncio
from typing import Optional, Dict, List, Tuple

# Import cache settings from config
from config import CACHE_DURATION, TOP_COINS_CACHE_DURATION

# Cache for coin list to avoid repeated API calls
COIN_LIST_CACHE = None
COIN_LIST_CACHE_TIMESTAMP = 0

# Cache for top coins (market data changes frequently)
TOP_COINS_CACHE = None
TOP_COINS_CACHE_TIMESTAMP = 0


async def get_all_coins() -> List[Dict]:
    """
    Fetch all available coins from CoinGecko API with caching
    Returns list of coin dictionaries with id, symbol, name
    """
    global COIN_LIST_CACHE, COIN_LIST_CACHE_TIMESTAMP

    current_time = time.time()

    # Return cached data if still valid
    if COIN_LIST_CACHE and (current_time - COIN_LIST_CACHE_TIMESTAMP) < CACHE_DURATION:
        return COIN_LIST_CACHE

    try:
        url = "https://api.coingecko.com/api/v3/coins/list"
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url)
            response.raise_for_status()

            COIN_LIST_CACHE = response.json()
            COIN_LIST_CACHE_TIMESTAMP = current_time
            return COIN_LIST_CACHE
    except Exception as e:
        print(f"Error fetching coin list: {e}")
        return COIN_LIST_CACHE or []


async def search_coins(query: str, limit: int = 10) -> List[Dict]:
    """
    Search for coins by name or symbol
    Returns list of matching coins with popular coins prioritized
    """
    all_coins = await get_all_coins()
    if not all_coins:
        return []

    query_lower = query.lower()
    exact_matches = []
    partial_matches = []

    # Well-known coin mappings for better search results
    well_known_mappings = {
        'bitcoin': 'bitcoin',
        'btc': 'bitcoin',
        'ethereum': 'ethereum',
        'eth': 'ethereum',
        'cardano': 'cardano',
        'ada': 'cardano',
        'dogecoin': 'dogecoin',
        'doge': 'dogecoin',
        'ripple': 'ripple',
        'xrp': 'ripple',
        'litecoin': 'litecoin',
        'ltc': 'litecoin',
        'solana': 'solana',
        'sol': 'solana',
        'binance': 'binancecoin',
        'bnb': 'binancecoin',
        'polygon': 'matic-network',
        'matic': 'matic-network',
        'chainlink': 'chainlink',
        'link': 'chainlink',
        'uniswap': 'uniswap',
        'uni': 'uniswap',
        'aave': 'aave',
        'compound': 'compound-governance-token',
        'comp': 'compound-governance-token',
        'sushi': 'sushi',
        'yearn': 'yearn-finance',
        'yfi': 'yearn-finance',
        'curve': 'curve-dao-token',
        'crv': 'curve-dao-token',
        'balancer': 'balancer',
        'bal': 'balancer',
        'shiba': 'shiba-inu',
        'shib': 'shiba-inu'
    }

    # Check well-known mappings first
    if query_lower in well_known_mappings:
        target_id = well_known_mappings[query_lower]
        for coin in all_coins:
            if coin.get('id') == target_id:
                return [coin] + [c for c in all_coins if c.get('id') != target_id and (
                        query_lower in c.get('name', '').lower() or
                        query_lower in c.get('symbol', '').lower()
                )][:limit - 1]

    for coin in all_coins:
        coin_name = coin.get('name', '').lower()
        coin_symbol = coin.get('symbol', '').lower()
        coin_id = coin.get('id', '').lower()

        # Check for exact matches first (highest priority)
        if (coin_symbol == query_lower or
                coin_id == query_lower or
                coin_name == query_lower):
            exact_matches.append(coin)
        # Check for word-based partial matches (medium priority)
        elif (query_lower in coin_name.split() or
              query_lower in coin_symbol.split() or
              query_lower in coin_id.split() or
              any(word.startswith(query_lower) for word in coin_name.split()) or
              any(word.startswith(query_lower) for word in coin_id.split())):
            partial_matches.append(coin)
        # Check for substring matches (lower priority, but still useful for rare coins)
        elif (query_lower in coin_name or
              query_lower in coin_symbol or
              query_lower in coin_id):
            partial_matches.append(coin)

    # Sort all matches by popularity score (highest first)
    all_matches = exact_matches + partial_matches

    # Calculate popularity scores for all matches
    popularity_scores = []
    for coin in all_matches:
        score = await get_coin_popularity_score(coin)
        popularity_scores.append((coin, score))

    # Sort by score and return coins
    popularity_scores.sort(key=lambda x: x[1], reverse=True)
    sorted_coins = [coin for coin, score in popularity_scores]

    return sorted_coins[:limit]


async def get_coin_by_id(coin_id: str) -> Optional[Dict]:
    """
    Get coin information by CoinGecko ID
    """
    all_coins = await get_all_coins()
    for coin in all_coins:
        if coin.get('id') == coin_id:
            return coin
    return None


async def get_coin_popularity_score(coin: Dict) -> int:
    """
    Calculate popularity score for a coin based on various factors
    Higher score = more popular coin
    """
    score = 0
    coin_id = coin.get('id', '').lower()
    coin_name = coin.get('name', '').lower()
    symbol = coin.get('symbol', '').lower()

    # Check if it's in top 100 by market cap
    try:
        top_coins = await get_top_coins(100)
        top_coin_ids = [c['id'] for c in top_coins]
        if coin_id in top_coin_ids:
            score += 1000 - top_coin_ids.index(coin_id)
    except:
        pass

    # Get top 20 coins dynamically (always up-to-date)
    try:
        top_20_coins = await get_top_coins(20)
        if top_20_coins:  # Check if we got data
            top_20_ids = [c['id'] for c in top_20_coins]
            if coin_id in top_20_ids:
                score += 500  # Bonus for being in top 20
    except:
        pass

    # Bonus for coins with short, common symbols
    if len(symbol) <= 4 and symbol.isalpha():
        score += 100

    # Bonus for coins with common English words in name
    common_words = ['coin', 'token', 'protocol', 'network', 'chain', 'defi', 'dao', 'swap', 'dex']
    if any(word in coin_name for word in common_words):
        score += 50

    # Bonus for coins with simple, memorable names
    if len(coin_name.split()) == 1 and len(coin_name) <= 15:
        score += 30

    # Penalty for testnet, wrapped, or synthetic tokens
    if any(word in coin_id for word in ['testnet', 'wrapped', 'synthetic', 'mock', 'test']):
        score -= 200

    # Penalty for very long or complex names
    if len(coin_name) > 30 or len(coin_name.split()) > 3:
        score -= 50

    # Penalty for coins with numbers in symbol (usually less popular)
    if any(char.isdigit() for char in symbol):
        score -= 20

    # Ensure minimum score for any valid coin
    return max(score, 1)


async def get_coin_by_symbol(symbol: str) -> Optional[Dict]:
    """
    Get coin information by symbol (e.g., 'btc', 'eth')
    Prioritizes popular coins over less common ones
    """
    all_coins = await get_all_coins()
    symbol_lower = symbol.lower()

    # First, try to find exact matches with well-known symbols
    well_known_symbols = {
        'btc': 'bitcoin',
        'eth': 'ethereum',
        'ada': 'cardano',
        'doge': 'dogecoin',
        'xrp': 'ripple',
        'ltc': 'litecoin',
        'bch': 'bitcoin-cash',
        'bnb': 'binancecoin',
        'sol': 'solana',
        'matic': 'matic-network',
        'avax': 'avalanche-2',
        'dot': 'polkadot',
        'link': 'chainlink',
        'uni': 'uniswap',
        'atom': 'cosmos',
        'shib': 'shiba-inu',
        'aave': 'aave',
        'comp': 'compound-governance-token',
        'sushi': 'sushi',
        'yfi': 'yearn-finance',
        'crv': 'curve-dao-token',
        'bal': 'balancer'
    }

    # If it's a well-known symbol, prioritize the main coin
    if symbol_lower in well_known_symbols:
        main_coin_id = well_known_symbols[symbol_lower]
        for coin in all_coins:
            if coin.get('id') == main_coin_id:
                return coin

    # Find all coins with matching symbol
    matching_coins = []
    for coin in all_coins:
        if coin.get('symbol', '').lower() == symbol_lower:
            matching_coins.append(coin)

    if not matching_coins:
        return None

    # If only one match, return it
    if len(matching_coins) == 1:
        return matching_coins[0]

    # If multiple matches, return the most popular one
    best_coin = None
    best_score = -1

    for coin in matching_coins:
        score = await get_coin_popularity_score(coin)
        if score > best_score:
            best_score = score
            best_coin = coin

    return best_coin


async def get_price(coin_id: str, currency: str = 'usd') -> Optional[float]:
    """
    Get the current price of a coin in specified currency using CoinGecko API
    NOTE: Prices are NOT cached to ensure real-time accuracy
    """
    if not coin_id:
        return None

    url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies={currency.lower()}"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()

            if coin_id in data and currency.lower() in data[coin_id]:
                return data[coin_id][currency.lower()]
            return None
    except Exception as e:
        print(f"Error fetching price for {coin_id} in {currency}: {e}")
        return None


async def get_multiple_prices(coin_ids: List[str], currency: str = 'usd') -> Dict[str, float]:
    """
    Get prices for multiple coins at once (more efficient than individual calls)
    NOTE: Prices are NOT cached to ensure real-time accuracy
    """
    if not coin_ids:
        return {}

    # CoinGecko API supports up to 250 coins per request
    coin_ids_str = ','.join(coin_ids[:250])
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_ids_str}&vs_currencies={currency.lower()}"

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()

            prices = {}
            for coin_id in coin_ids:
                if coin_id in data and currency.lower() in data[coin_id]:
                    prices[coin_id] = data[coin_id][currency.lower()]
            return prices
    except Exception as e:
        print(f"Error fetching multiple prices in {currency}: {e}")
        return {}


async def get_supported_currencies() -> List[str]:
    """
    Get list of supported fiat currencies from CoinGecko API
    """
    try:
        url = "https://api.coingecko.com/api/v3/simple/supported_vs_currencies"
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.json()
    except Exception as e:
        print(f"Error fetching supported currencies: {e}")
        # Return common currencies as fallback
        return ['usd', 'eur', 'gbp', 'jpy', 'cad', 'aud', 'chf', 'cny', 'rub', 'inr', 'brl', 'krw', 'mxn', 'sek', 'nok',
                'dkk', 'pln', 'czk', 'huf', 'try', 'zar', 'thb', 'sgd', 'hkd', 'nzd', 'php', 'myr', 'idr', 'vnd', 'uah',
                'bgn', 'hrk', 'ron', 'rsd', 'isk', 'lkr', 'bdt', 'pkr', 'npr', 'lkr', 'mmk', 'khr', 'lak', 'mnt', 'kzt',
                'uzs', 'tjs', 'tmt', 'afn', 'amd', 'azn', 'gel', 'kgs', 'mwk', 'zmw', 'bwp', 'szl', 'lsl', 'nad', 'etb',
                'kes', 'ugx', 'tzs', 'rwf', 'bif', 'djf', 'kmf', 'mga', 'mur', 'sc', 'mvr', 'npr', 'pkr', 'lkr', 'bdt',
                'afn', 'amd', 'azn', 'gel', 'kgs', 'tjs', 'tmt', 'uzs', 'kzt', 'mnt', 'khr', 'lak', 'mmk', 'npr', 'pkr',
                'lkr', 'bdt', 'afn', 'amd', 'azn', 'gel', 'kgs', 'tjs', 'tmt', 'uzs', 'kzt', 'mnt', 'khr', 'lak', 'mmk']


def get_currency_symbol(currency: str) -> str:
    """
    Get currency symbol for display
    """
    currency_symbols = {
        'usd': '$',
        'eur': '€',
        'gbp': '£',
        'jpy': '¥',
        'cad': 'C$',
        'aud': 'A$',
        'chf': 'CHF',
        'cny': '¥',
        'rub': '₽',
        'inr': '₹',
        'brl': 'R$',
        'krw': '₩',
        'mxn': '$',
        'sek': 'kr',
        'nok': 'kr',
        'dkk': 'kr',
        'pln': 'zł',
        'czk': 'Kč',
        'huf': 'Ft',
        'try': '₺',
        'zar': 'R',
        'thb': '฿',
        'sgd': 'S$',
        'hkd': 'HK$',
        'nzd': 'NZ$',
        'php': '₱',
        'myr': 'RM',
        'idr': 'Rp',
        'vnd': '₫',
        'uah': '₴',
        'bgn': 'лв',
        'hrk': 'kn',
        'ron': 'lei',
        'rsd': 'дин',
        'isk': 'kr',
        'lkr': '₨',
        'bdt': '৳',
        'pkr': '₨',
        'npr': '₨',
        'mmk': 'K',
        'khr': '៛',
        'lak': '₭',
        'mnt': '₮',
        'kzt': '₸',
        'uzs': 'сўм',
        'tjs': 'SM',
        'tmt': 'T',
        'afn': '؋',
        'amd': '֏',
        'azn': '₼',
        'gel': '₾',
        'kgs': 'сом',
        'mwk': 'MK',
        'zmw': 'ZK',
        'bwp': 'P',
        'szl': 'L',
        'lsl': 'L',
        'nad': 'N$',
        'etb': 'Br',
        'kes': 'KSh',
        'ugx': 'USh',
        'tzs': 'TSh',
        'rwf': 'RF',
        'bif': 'FBu',
        'djf': 'Fdj',
        'kmf': 'CF',
        'mga': 'Ar',
        'mur': '₨',
        'sc': '₨',
        'mvr': 'ރ'
    }
    return currency_symbols.get(currency.lower(), currency.upper())


async def get_top_coins(limit: int = 100) -> List[Dict]:
    """
    Get top coins by market cap with short-term caching
    """
    global TOP_COINS_CACHE, TOP_COINS_CACHE_TIMESTAMP

    current_time = time.time()

    # Return cached data if still valid and limit matches
    if (TOP_COINS_CACHE and
            (current_time - TOP_COINS_CACHE_TIMESTAMP) < TOP_COINS_CACHE_DURATION and
            len(TOP_COINS_CACHE) >= limit):
        return TOP_COINS_CACHE[:limit]

    try:
        url = f"https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page={limit}&page=1"
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url)
            response.raise_for_status()

            TOP_COINS_CACHE = response.json()
            TOP_COINS_CACHE_TIMESTAMP = current_time
            return TOP_COINS_CACHE
    except Exception as e:
        print(f"Error fetching top coins: {e}")
        return TOP_COINS_CACHE or []