from dataclasses import dataclass, field


@dataclass
class TaskItem:
    kind: str
    payload: dict


@dataclass
class WorkflowState:
    thread_id: str | None
    user_message: str
    user_location: str
    thread_context: str = ""
    planner_summary: str = ""
    tasks: list[TaskItem] = field(default_factory=list)
    tool_calls: list[str] = field(default_factory=list)
    tool_outputs: dict[str, str] = field(default_factory=dict)
    final_answer: str = ""