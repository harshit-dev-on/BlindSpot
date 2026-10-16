"""Data models for AI-generated user personas, test tasks, and execution plans."""

from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class PersonaTask(BaseModel):
    """A realistic testing task assigned to an AI persona."""

    id: str = Field(
        ...,
        description="Unique task identifier (e.g. 'task_persona_1_1')",
    )
    objective: str = Field(
        ...,
        description="Clear, specific user objective (e.g. 'Locate customer support hours from the footer')",
    )
    starting_conditions: str = Field(
        default="Starts on target webpage",
        description="Initial state or page where the persona begins this task",
    )
    success_criteria: List[str] = Field(
        ...,
        description="Concrete conditions that indicate the task was completed successfully",
    )
    evidence_to_collect: List[str] = Field(
        ...,
        description="Observable artifacts or findings to collect (e.g. screenshot of policy, text of contact number)",
    )
    is_verified: bool = Field(
        default=True,
        description="Whether this task relies strictly on verified features observed on the website",
    )
    uncertainty_notes: Optional[str] = Field(
        default=None,
        description="Notes explaining any assumed or unverified website capabilities",
    )


class Persona(BaseModel):
    """A realistic, non-stereotypical simulated user persona."""

    id: str = Field(
        ...,
        description="Unique persona identifier (e.g. 'persona_1')",
    )
    name: str = Field(
        ...,
        description="Persona name and brief archetype (e.g. 'Jordan - First-Time Mobile Shopper')",
    )
    description: str = Field(
        ...,
        description="Concise description of the persona's background, context, and motivations",
    )
    experience_level: str = Field(
        ...,
        description="Web and technical proficiency level (e.g. 'Novice', 'Intermediate', 'Advanced')",
    )
    goals: List[str] = Field(
        ...,
        description="Primary user goals when visiting this website",
    )
    likely_difficulties: List[str] = Field(
        ...,
        description="Potential UX friction points, confusion areas, or barriers this user might encounter",
    )
    accessibility_needs: Optional[str] = Field(
        default="Standard desktop browsing",
        description="Relevant accessibility or browsing considerations (e.g. 'Screen reader', 'Keyboard-only', 'Low-vision / zoom', 'Mobile browser')",
    )
    tasks: List[PersonaTask] = Field(
        ...,
        description="Between 2 and 4 realistic testing tasks assigned to this persona",
    )

    @field_validator("tasks")
    @classmethod
    def validate_task_count(cls, v: List[PersonaTask]) -> List[PersonaTask]:
        if not v:
            raise ValueError("Each persona must have at least 1 assigned task.")
        return v


class PersonaPlanPayload(BaseModel):
    """Structured JSON payload returned directly by the AI model."""

    website_summary: str = Field(
        ...,
        description="Brief AI synthesis of observed website purpose, capabilities, and primary user flows",
    )
    personas: List[Persona] = Field(
        ...,
        description="List of diverse, task-relevant simulated user personas",
    )


class PersonaPlan(BaseModel):
    """Consolidated test plan containing website understanding and generated personas."""

    website_url: str = Field(..., description="Target website URL inspected")
    context: str = Field(..., description="User-supplied context and audience description")
    website_summary: str = Field(
        ...,
        description="AI synthesis of observed website purpose, capabilities, and primary user flows",
    )
    personas: List[Persona] = Field(
        ...,
        description="List of diverse, task-relevant user personas",
    )
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO 8601 UTC timestamp of plan generation",
    )
    model_used: Optional[str] = Field(default=None, description="Model identifier used for generation")
    provider_used: Optional[str] = Field(default=None, description="Provider used for generation")
    plan_file_path: Optional[str] = Field(default=None, description="File path where this plan is saved")

    @property
    def total_tasks(self) -> int:
        """Total number of tasks across all personas."""
        return sum(len(p.tasks) for p in self.personas)

    @property
    def total_unverified_tasks(self) -> int:
        """Number of tasks that rely on unverified website features."""
        return sum(1 for p in self.personas for t in p.tasks if not t.is_verified)
