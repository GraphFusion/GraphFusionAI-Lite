import json
from typing import Any, Dict, Optional

class StateManager:
    """Advanced state management with versioning and branching"""
    
    def __init__(self, initial_state: Optional[Dict[str, Any]] = None):
        self.current_state = initial_state or {}
        self.state_history = []
        self.branches = {'main': self.current_state}
        
    def update_state(self, new_state: Dict[str, Any], branch: str = 'main') -> None:
        """Update state with conflict resolution"""
        if branch not in self.branches:
            self.branches[branch] = {}
            
        # Merge states with conflict resolution
        for key, value in new_state.items():
            if key in self.branches[branch] and isinstance(value, dict):
                self.branches[branch][key].update(value)
            else:
                self.branches[branch][key] = value
        
        # Save state snapshot
        self.state_history.append({
            'branch': branch,
            'state': json.loads(json.dumps(self.branches[branch]))
        })
    
    def create_branch(self, source_branch: str, new_branch: str) -> None:
        """Create a new state branch"""
        if source_branch in self.branches:
            self.branches[new_branch] = json.loads(json.dumps(self.branches[source_branch]))
    
    def merge_branch(self, source_branch: str, target_branch: str = 'main') -> None:
        """Merge branches with automatic conflict resolution"""
        if source_branch in self.branches and target_branch in self.branches:
            self.update_state(self.branches[source_branch], target_branch)

    def get_state(self, branch: str = 'main') -> Dict[str, Any]:
        """Retrieve current state for a branch"""
        return self.branches.get(branch, {})

    def rollback_state(self, steps: int = 1, branch: str = 'main') -> None:
        """Revert to a previous state"""
        if branch in self.branches and steps <= len(self.state_history):
            self.branches[branch] = self.state_history[-steps]['state']
