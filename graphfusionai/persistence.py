import sqlite3
import json
from typing import Optional
from dataclasses import dataclass
import time

@dataclass
class AgentState:
    agent_id: str
    status: str  # 'active', 'idle', 'busy', 'error'
    capabilities: list  # list of capability names
    memory: dict  # dict of key-value pairs
    last_updated: float  # timestamp

class AgentStateDB:
    def __init__(self, db_path: str = 'agent_states.db'):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self._create_table()
    
    def _create_table(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS agent_states (
                agent_id TEXT PRIMARY KEY,
                status TEXT,
                capabilities TEXT,  
                memory TEXT,        
                last_updated REAL
            )
        ''')
        self.conn.commit()
    
    def save_state(self, state: AgentState):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO agent_states 
            (agent_id, status, capabilities, memory, last_updated)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            state.agent_id,
            state.status,
            json.dumps(state.capabilities),
            json.dumps(state.memory),
            state.last_updated
        ))
        self.conn.commit()
    
    def load_state(self, agent_id: str) -> Optional[AgentState]:
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT status, capabilities, memory, last_updated
            FROM agent_states WHERE agent_id = ?
        ''', (agent_id,))
        row = cursor.fetchone()
        if row:
            return AgentState(
                agent_id=agent_id,
                status=row[0],
                capabilities=json.loads(row[1]),
                memory=json.loads(row[2]),
                last_updated=row[3]
            )
        return None
    
    def close(self):
        self.conn.close()
