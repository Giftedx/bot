"""NPC data manager for handling NPC-related data."""

from typing import Dict, List, Optional
from .data_manager import DataManager

class NPCManager(DataManager):
    """Manages NPC data and interactions."""
    
    def __init__(self, data_dir: str = "src/osrs/data"):
        """Initialize the NPC manager.
        
        Args:
            data_dir: Directory containing data files.
        """
        super().__init__(data_dir)
        self.NPC_FILE = "npcs.json"
        
    def get_npc(self, npc_id: str) -> Dict:
        """Get NPC data by ID.
        
        Args:
            npc_id: The ID of the NPC.
            
        Returns:
            Dict containing NPC data.
            
        Raises:
            KeyError: If NPC doesn't exist.
        """
        return self.get_data(self.NPC_FILE, npc_id)
        
    def get_npcs_by_location(self, location: str) -> List[Dict]:
        """Get all NPCs in a specific location.
        
        Args:
            location: Location to search for NPCs.
            
        Returns:
            List of NPC data dictionaries.
        """
        npcs = []
        all_npcs = self.get_data(self.NPC_FILE)
        
        for npc_id, npc_data in all_npcs.items():
            if npc_data.get("location") == location:
                npcs.append(npc_data)
                
        return npcs
        
    def get_dialogue(self, npc_id: str, dialogue_key: str) -> Optional[str]:
        """Get specific dialogue for an NPC.
        
        Args:
            npc_id: The ID of the NPC.
            dialogue_key: The specific dialogue key to retrieve.
            
        Returns:
            The dialogue string or None if not found.
        """
        npc = self.get_npc(npc_id)
        dialogue = npc.get("dialogue", {})
        
        if dialogue_key in dialogue:
            return dialogue[dialogue_key]
        elif dialogue_key in dialogue.get("responses", {}):
            return dialogue["responses"][dialogue_key]
            
        return None
        
    def is_slayer_master(self, npc_id: str) -> bool:
        """Check if an NPC is a slayer master.
        
        Args:
            npc_id: The ID of the NPC.
            
        Returns:
            True if the NPC is a slayer master.
        """
        npc = self.get_npc(npc_id)
        return "slayer_master" in npc 