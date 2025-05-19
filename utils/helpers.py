import math

class Helpers:
    @staticmethod
    def get_level_from_xp(xp):
        """Calculate level from XP amount
        
        Args:
            xp: The total XP amount
            
        Returns:
            int: The calculated level
        """
        # Level calculation formula: level = sqrt(xp / 100)
        return int(math.sqrt(xp / 100))
    
    @staticmethod
    def get_xp_for_level(level):
        """Calculate XP required for a specific level
        
        Args:
            level: The level to calculate XP for
            
        Returns:
            int: The XP required to reach this level
        """
        # XP calculation formula: xp = level^2 * 100
        return int(level ** 2 * 100)