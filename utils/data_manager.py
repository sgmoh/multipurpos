import json
import os
import logging
import asyncio

logger = logging.getLogger('discord_bot')

class DataManager:
    def __init__(self, file_path):
        """Initialize the data manager with a file path.
        
        Args:
            file_path (str): Path to the JSON file for data storage
        """
        self.file_path = file_path
        self.data = {}
        self.lock = asyncio.Lock()
        
        # Ensure the directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # Load existing data or create a new file
        self._load_data()
    
    def _load_data(self):
        """Load data from the JSON file."""
        try:
            if os.path.exists(self.file_path):
                with open(self.file_path, 'r') as f:
                    self.data = json.load(f)
            else:
                # Create the file with empty data
                self._save_data()
        except Exception as e:
            logger.error(f"Failed to load data from {self.file_path}: {e}")
            # If loading fails, start with empty data
            self.data = {}
    
    def _save_data(self):
        """Save data to the JSON file."""
        try:
            with open(self.file_path, 'w') as f:
                json.dump(self.data, f, indent=4)
        except Exception as e:
            logger.error(f"Failed to save data to {self.file_path}: {e}")
    
    async def get(self, key, default=None):
        """Get a value from the data dictionary.
        
        Args:
            key: The key to look up
            default: The default value to return if key is not found
            
        Returns:
            The value associated with the key, or default if not found
        """
        async with self.lock:
            return self.data.get(str(key), default)
    
    async def set(self, key, value):
        """Set a value in the data dictionary.
        
        Args:
            key: The key to set
            value: The value to associate with the key
        """
        async with self.lock:
            self.data[str(key)] = value
            self._save_data()
    
    async def delete(self, key):
        """Delete a key from the data dictionary.
        
        Args:
            key: The key to delete
            
        Returns:
            bool: True if the key was deleted, False otherwise
        """
        async with self.lock:
            if str(key) in self.data:
                del self.data[str(key)]
                self._save_data()
                return True
            return False
    
    async def increment(self, key, amount=1, default=0):
        """Increment a numeric value in the data dictionary.
        
        Args:
            key: The key to increment
            amount: The amount to increment by
            default: The default value if key doesn't exist
            
        Returns:
            The new value after incrementing
        """
        async with self.lock:
            current = self.data.get(str(key), default)
            new_value = current + amount
            self.data[str(key)] = new_value
            self._save_data()
            return new_value
    
    async def get_all(self):
        """Get all data.
        
        Returns:
            dict: A copy of the entire data dictionary
        """
        async with self.lock:
            return self.data.copy()
