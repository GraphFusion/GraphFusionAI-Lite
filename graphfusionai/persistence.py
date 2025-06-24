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

@dataclass
class TeamState:
    team_id: str
    agent_ids: list  # list of agent IDs
    task_queue: list  # list of pending tasks
    last_updated: float  # timestamp

class TeamStateDB:
    def __init__(self, db_path: str = 'team_states.db'):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self._create_table()
    
    def _create_table(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS team_states (
                team_id TEXT PRIMARY KEY,
                agent_ids TEXT,  
                task_queue TEXT,        
                last_updated REAL
            )
        ''')
        self.conn.commit()
    
    def save_state(self, state: TeamState):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO team_states 
            (team_id, agent_ids, task_queue, last_updated)
            VALUES (?, ?, ?, ?)
        ''', (
            state.team_id,
            json.dumps(state.agent_ids),
            json.dumps(state.task_queue),
            state.last_updated
        ))
        self.conn.commit()
    
    def load_state(self, team_id: str) -> Optional[TeamState]:
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT agent_ids, task_queue, last_updated
            FROM team_states WHERE team_id = ?
        ''', (team_id,))
        row = cursor.fetchone()
        if row:
            return TeamState(
                team_id=team_id,
                agent_ids=json.loads(row[0]),
                task_queue=json.loads(row[1]),
                last_updated=row[2]
            )
        return None
    
    def close(self):
        self.conn.close()
