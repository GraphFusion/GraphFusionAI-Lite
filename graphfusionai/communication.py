from typing import Dict, Any

class Message:
    """
    Represents a communication between agents.
    
    Attributes:
        sender_id: ID of the sending agent
        recipient_id: ID of the receiving agent
        content: Message content
        timestamp: Time of message creation
    """
    
    def __init__(self, sender_id: str, recipient_id: str, content: Dict[str, Any]):
        self.sender_id = sender_id
        self.recipient_id = recipient_id
        self.content = content
        self.timestamp = time.time()

    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary representation"""
        return {
            "sender": self.sender_id,
            "recipient": self.recipient_id,
            "content": self.content,
            "timestamp": self.timestamp
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'Message':
        """Create message from dictionary representation"""
        return Message(
            sender_id=data["sender"],
            recipient_id=data["recipient"],
            content=data["content"],
            timestamp=data["timestamp"]
        )
