import json
import random
import time
import uuid
from datetime import datetime, timezone


class Observability:
    def __init__(self, total_steps, trace_file="trace.jsonl"):
        self.trace_id = str(uuid.uuid4())
        self.total_steps = total_steps
        self.completed_steps = 0
        self.run_start = time.time()
        self.agent_start_times = {}
        self.completed_agents = []
        self.trace_file = trace_file

        open(self.trace_file, "w").close()

    def now(self):
        return datetime.now(timezone.utc).isoformat()

    def emit(self, event):
        event["timestamp"] = self.now()
        event["trace_id"] = self.trace_id

        print(json.dumps(event))

        with open(self.trace_file, "a") as f:
            f.write(json.dumps(event) + "\n")

    def pipeline_percent(self):
        return round((self.completed_steps / self.total_steps) * 100, 2)

    def throughput(self):
        elapsed = time.time() - self.run_start
        return round(self.completed_steps / elapsed, 2) if elapsed > 0 else 0

    def agent_started(self, agent_name, span_id):
        self.agent_start_times[agent_name] = time.time()

        self.emit({
            "event": "agent_started",
            "span_id": span_id,
            "agent": agent_name,
            "pipeline_percent_complete": self.pipeline_percent(),
            "throughput_steps_per_sec": self.throughput()
        })

    def agent_progress(self, agent_name, span_id, step, total_steps):
        self.completed_steps += 1

        progress_percent = round((step / total_steps) * 100, 2)

        self.emit({
            "event": "agent_progress",
            "span_id": span_id,
            "agent": agent_name,
            "agent_step": step,
            "agent_total_steps": total_steps,
            "agent_percent_complete": progress_percent,
            "pipeline_percent_complete": self.pipeline_percent(),
            "throughput_steps_per_sec": self.throughput()
        })

    def agent_completed(self, agent_name, span_id):
        duration = round(time.time() - self.agent_start_times[agent_name], 3)
        self.completed_agents.append(agent_name)

        self.emit({
            "event": "agent_completed",
            "span_id": span_id,
            "agent": agent_name,
            "agent_duration_seconds": duration,
            "pipeline_percent_complete": self.pipeline_percent(),
            "throughput_steps_per_sec": self.throughput()
        })

    def agent_failed(self, agent_name, span_id, step, error):
        self.emit({
            "event": "agent_failed",
            "span_id": span_id,
            "agent": agent_name,
            "failed_step": step,
            "error_message": str(error),
            "pipeline_percent_complete": self.pipeline_percent(),
            "throughput_steps_per_sec": self.throughput()
        })

    def run_summary(self, status, failed_agent=None):
        total_duration = round(time.time() - self.run_start, 3)

        self.emit({
            "event": "run_summary",
            "span_id": None,
            "status": status,
            "total_duration_seconds": total_duration,
            "agents_completed": self.completed_agents,
            "failed_agent": failed_agent,
            "pipeline_percent_complete": self.pipeline_percent(),
            "throughput_steps_per_sec": self.throughput()
        })


class Agent:
    def __init__(self, name, steps, fail_at_step=None):
        self.name = name
        self.steps = steps
        self.fail_at_step = fail_at_step
        self.span_id = str(uuid.uuid4())

    def should_emit_progress(self, step):
        # Emit progress roughly at 25%, 50%, 75%, and 100%
        checkpoints = {
            max(1, round(self.steps * 0.25)),
            max(1, round(self.steps * 0.50)),
            max(1, round(self.steps * 0.75)),
            self.steps
        }
        return step in checkpoints

    def run(self, observer):
        observer.agent_started(self.name, self.span_id)

        for step in range(1, self.steps + 1):
            time.sleep(random.uniform(0.05, 0.2))

            if self.fail_at_step and step == self.fail_at_step:
                raise RuntimeError(f"{self.name} failed at step {step}")

            if self.should_emit_progress(step):
                observer.agent_progress(
                    self.name,
                    self.span_id,
                    step,
                    self.steps
                )

        observer.agent_completed(self.name, self.span_id)


class Orchestrator:
    def __init__(self, agents):
        self.agents = agents
        self.total_steps = sum(agent.steps for agent in agents)
        self.observer = Observability(self.total_steps)

    def run(self):
        failed_agent = None

        try:
            for agent in self.agents:
                try:
                    agent.run(self.observer)
                except Exception as e:
                    failed_agent = agent.name

                    failed_step = agent.fail_at_step if agent.fail_at_step else "unknown"

                    self.observer.agent_failed(
                        agent.name,
                        agent.span_id,
                        failed_step,
                        e
                    )
                    self.observer.run_summary(
                        status="failed",
                        failed_agent=failed_agent
                    )
                    return

            self.observer.run_summary(
                status="success",
                failed_agent=None
            )

        except Exception as e:
            self.observer.run_summary(
                status="failed",
                failed_agent=str(e)
            )


def read_trace_file(filename="trace.jsonl"):
    print("\n--- Per Agent Timeline ---")

    with open(filename, "r") as f:
        for line in f:
            event = json.loads(line)

            if event["event"] in [
                "agent_started",
                "agent_progress",
                "agent_completed",
                "agent_failed"
            ]:
                print(
                    f"{event['timestamp']} | "
                    f"{event['event']} | "
                    f"{event['agent']} | "
                    f"pipeline={event['pipeline_percent_complete']}%"
                )


def main():
    agents = [
        Agent("Planner", 3),
        Agent("Researcher", 6),
        Agent("Writer", 4),
        Agent("Reviewer", 2)

        # Failure testing:
        # Agent("Writer", 4, fail_at_step=3),
    ]

    orchestrator = Orchestrator(agents)
    orchestrator.run()

    read_trace_file()


if __name__ == "__main__":
    main()