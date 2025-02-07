import logging
import time

class AgentMonitor:
    """
    Monitors agent performance, task execution, and detects anomalies.
    Logs agent activities and provides basic self-healing mechanisms.
    """
    
    def __init__(self, log_file="agent_monitor.log", anomaly_threshold=3):
        """Initialize monitoring with logging and anomaly detection parameters."""
        self.anomaly_threshold = anomaly_threshold
        self.agent_failures = {}
        logging.basicConfig(filename=log_file, level=logging.INFO, format='%(asctime)s - %(message)s')

    def log_activity(self, agent_id, message):
        """Log agent activity."""
        log_message = f"Agent {agent_id}: {message}"
        logging.info(log_message)
        print(log_message)

    def detect_anomaly(self, agent_id):
        """Detect repeated failures and trigger self-healing if threshold is exceeded."""
        self.agent_failures[agent_id] = self.agent_failures.get(agent_id, 0) + 1
        if self.agent_failures[agent_id] >= self.anomaly_threshold:
            self.trigger_self_healing(agent_id)

    def trigger_self_healing(self, agent_id):
        """Reset agent state or take corrective action."""
        logging.warning(f"Triggering self-healing for {agent_id}")
        print(f"Triggering self-healing for {agent_id}")
        self.agent_failures[agent_id] = 0

# Example usage
if __name__ == "__main__":
    monitor = AgentMonitor()
    monitor.log_activity("Agent1", "Started task execution")
    monitor.detect_anomaly("Agent1")
    monitor.detect_anomaly("Agent1")
    monitor.detect_anomaly("Agent1")
