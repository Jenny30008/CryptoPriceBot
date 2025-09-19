import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
import threading


class UserStorage:
    """Persistent storage for user data using JSON files"""

    def __init__(self, storage_path: str = "user_data"):
        """Initialize JSON storage with specified path"""
        self.storage_path = storage_path
        self.lock = threading.Lock()
        self._init_json_storage()

    def _init_json_storage(self):
        """Initialize JSON storage"""
        self.json_file = f"{self.storage_path}.json"
        self._ensure_json_file_exists()

    def _ensure_json_file_exists(self):
        """Create JSON file if it doesn't exist"""
        if not os.path.exists(self.json_file):
            default_data = {
                "subscribers": [],
                "user_alert_thresholds": {},
                "user_coin_subscriptions": {},
                "last_prices": {},
                "metadata": {
                    "created_at": datetime.now().isoformat(),
                    "last_updated": datetime.now().isoformat()
                }
            }
            with open(self.json_file, 'w', encoding='utf-8') as f:
                json.dump(default_data, f, indent=2, ensure_ascii=False)

    def save_subscribers(self, subscribers: List[int]) -> bool:
        """Save subscribers list"""
        with self.lock:
            try:
                return self._save_subscribers_json(subscribers)
            except Exception as e:
                print(f"Error saving subscribers: {e}")
                return False

    def load_subscribers(self) -> List[int]:
        """Load subscribers list"""
        with self.lock:
            try:
                return self._load_subscribers_json()
            except Exception as e:
                print(f"Error loading subscribers: {e}")
                return []

    def save_user_threshold(self, chat_id: int, threshold: float) -> bool:
        """Save user alert threshold"""
        with self.lock:
            try:
                return self._save_user_threshold_json(chat_id, threshold)
            except Exception as e:
                print(f"Error saving threshold for user {chat_id}: {e}")
                return False

    def load_user_thresholds(self) -> Dict[int, float]:
        """Load user alert thresholds"""
        with self.lock:
            try:
                return self._load_user_thresholds_json()
            except Exception as e:
                print(f"Error loading user thresholds: {e}")
                return {}

    def save_user_coin_subscriptions(self, chat_id: int, coin_ids: List[str]) -> bool:
        """Save user coin subscriptions"""
        with self.lock:
            try:
                return self._save_user_coin_subscriptions_json(chat_id, coin_ids)
            except Exception as e:
                print(f"Error saving coin subscriptions for user {chat_id}: {e}")
                return False

    def load_user_coin_subscriptions(self) -> Dict[int, List[str]]:
        """Load user coin subscriptions"""
        with self.lock:
            try:
                return self._load_user_coin_subscriptions_json()
            except Exception as e:
                print(f"Error loading coin subscriptions: {e}")
                return {}

    def save_last_prices(self, last_prices: Dict[str, float]) -> bool:
        """Save last prices"""
        with self.lock:
            try:
                return self._save_last_prices_json(last_prices)
            except Exception as e:
                print(f"Error saving last prices: {e}")
                return False

    def load_last_prices(self) -> Dict[str, float]:
        """Load last prices"""
        with self.lock:
            try:
                return self._load_last_prices_json()
            except Exception as e:
                print(f"Error loading last prices: {e}")
                return {}

    def add_coin_to_user(self, chat_id: int, coin_id: str) -> bool:
        """Add coin to user"""
        with self.lock:
            try:
                return self._add_coin_to_user_json(chat_id, coin_id)
            except Exception as e:
                print(f"Error adding coin {coin_id} to user {chat_id}: {e}")
                return False

    def remove_coin_from_user(self, chat_id: int, coin_id: str) -> bool:
        """Remove coin from user"""
        with self.lock:
            try:
                return self._remove_coin_from_user_json(chat_id, coin_id)
            except Exception as e:
                print(f"Error removing coin {coin_id} from user {chat_id}: {e}")
                return False

    def clear_user_coins(self, chat_id: int) -> bool:
        """Clear all user coins"""
        with self.lock:
            try:
                return self._clear_user_coins_json(chat_id)
            except Exception as e:
                print(f"Error clearing coins for user {chat_id}: {e}")
                return False

    def get_user_coins(self, chat_id: int) -> List[str]:
        """Get user coins"""
        with self.lock:
            try:
                return self._get_user_coins_json(chat_id)
            except Exception as e:
                print(f"Error getting coins for user {chat_id}: {e}")
                return []

    def backup_data(self, backup_path: str = None) -> bool:
        """Create data backup"""
        if backup_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"backup_{timestamp}.json"

        try:
            import shutil
            shutil.copy2(self.json_file, backup_path)
            return True
        except Exception as e:
            print(f"Error creating backup: {e}")
            return False

    def restore_data(self, backup_path: str) -> bool:
        """Restore data from backup"""
        try:
            with open(backup_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            self.save_subscribers(data.get("subscribers", []))
            for chat_id, threshold in data.get("user_alert_thresholds", {}).items():
                self.save_user_threshold(int(chat_id), threshold)
            for chat_id, coin_ids in data.get("user_coin_subscriptions", {}).items():
                self.save_user_coin_subscriptions(int(chat_id), coin_ids)
            self.save_last_prices(data.get("last_prices", {}))

            return True
        except Exception as e:
            print(f"Error restoring data: {e}")
            return False

    # JSON methods
    def _save_subscribers_json(self, subscribers: List[int]) -> bool:
        data = self._load_json_data()
        data["subscribers"] = subscribers
        data["metadata"]["last_updated"] = datetime.now().isoformat()
        return self._save_json_data(data)

    def _load_subscribers_json(self) -> List[int]:
        data = self._load_json_data()
        return data.get("subscribers", [])

    def _save_user_threshold_json(self, chat_id: int, threshold: float) -> bool:
        data = self._load_json_data()
        data["user_alert_thresholds"][str(chat_id)] = threshold
        data["metadata"]["last_updated"] = datetime.now().isoformat()
        return self._save_json_data(data)

    def _load_user_thresholds_json(self) -> Dict[int, float]:
        data = self._load_json_data()
        return {int(k): v for k, v in data.get("user_alert_thresholds", {}).items()}

    def _save_user_coin_subscriptions_json(self, chat_id: int, coin_ids: List[str]) -> bool:
        data = self._load_json_data()
        data["user_coin_subscriptions"][str(chat_id)] = coin_ids
        data["metadata"]["last_updated"] = datetime.now().isoformat()
        return self._save_json_data(data)

    def _load_user_coin_subscriptions_json(self) -> Dict[int, List[str]]:
        data = self._load_json_data()
        return {int(k): v for k, v in data.get("user_coin_subscriptions", {}).items()}

    def _save_last_prices_json(self, last_prices: Dict[str, float]) -> bool:
        data = self._load_json_data()
        data["last_prices"] = last_prices
        data["metadata"]["last_updated"] = datetime.now().isoformat()
        return self._save_json_data(data)

    def _load_last_prices_json(self) -> Dict[str, float]:
        data = self._load_json_data()
        return data.get("last_prices", {})

    def _add_coin_to_user_json(self, chat_id: int, coin_id: str) -> bool:
        data = self._load_json_data()
        chat_id_str = str(chat_id)
        if chat_id_str not in data["user_coin_subscriptions"]:
            data["user_coin_subscriptions"][chat_id_str] = []
        if coin_id not in data["user_coin_subscriptions"][chat_id_str]:
            data["user_coin_subscriptions"][chat_id_str].append(coin_id)
            data["metadata"]["last_updated"] = datetime.now().isoformat()
            return self._save_json_data(data)
        return False

    def _remove_coin_from_user_json(self, chat_id: int, coin_id: str) -> bool:
        data = self._load_json_data()
        chat_id_str = str(chat_id)
        if chat_id_str in data["user_coin_subscriptions"] and coin_id in data["user_coin_subscriptions"][chat_id_str]:
            data["user_coin_subscriptions"][chat_id_str].remove(coin_id)
            data["metadata"]["last_updated"] = datetime.now().isoformat()
            return self._save_json_data(data)
        return False

    def _clear_user_coins_json(self, chat_id: int) -> bool:
        data = self._load_json_data()
        chat_id_str = str(chat_id)
        if chat_id_str in data["user_coin_subscriptions"]:
            data["user_coin_subscriptions"][chat_id_str] = []
            data["metadata"]["last_updated"] = datetime.now().isoformat()
            return self._save_json_data(data)
        return False

    def _get_user_coins_json(self, chat_id: int) -> List[str]:
        data = self._load_json_data()
        return data.get("user_coin_subscriptions", {}).get(str(chat_id), [])

    def _load_json_data(self) -> Dict[str, Any]:
        with open(self.json_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _save_json_data(self, data: Dict[str, Any]) -> bool:
        with open(self.json_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True


# Global storage instance
storage = None


def get_storage() -> UserStorage:
    """Get global storage instance"""
    global storage
    if storage is None:
        try:
            from config import STORAGE_PATH
            storage = UserStorage(storage_path=STORAGE_PATH)
        except ImportError:
            storage = UserStorage(storage_path="user_data")
    return storage


def init_storage(storage_path: str = "user_data"):
    """Initialize storage with specified parameters"""
    global storage
    storage = UserStorage(storage_path=storage_path)
    return storage