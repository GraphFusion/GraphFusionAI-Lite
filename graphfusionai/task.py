from typing import Dict, Any

class Task:
    """
    Represents a unit of work to be performed by an agent.
    
    Attributes:
        task_id: Unique identifier for the task
        task_type: Type/category of task
        parameters: Input parameters for the task
        dependencies: List of task IDs this task depends on
        priority: Priority level (1-5, 5 highest)
        status: Current status (pending, in_progress, completed, failed)
    """
    
    def __init__(self, task_id: str, task_type: str, parameters: Dict[str, Any], 
                 dependencies: List[str] = None, priority: int = 3):
        self.task_id = task_id
        self.task_type = task_type
        self.parameters = parameters
        self.dependencies = dependencies or []
        self.priority = priority
        self.status = "pending"

    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary representation"""
        return {
            "task_id": self.task_id,
            "type": self.task_type,
            "parameters": self.parameters,
            "dependencies": self.dependencies,
            "priority": self.priority,
            "status": self.status
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'Task':
        """Create task from dictionary representation"""
        return Task(
            task_id=data["task_id"],
            task_type=data["type"],
            parameters=data["parameters"],
            dependencies=data.get("dependencies", []),
            priority=data.get("priority", 3)
        )
