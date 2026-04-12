"""Prompt templates for the Logic Graph chatbot.

All prompts are written in Spanish for the Colombian psychoeducation context.
"""

from logic_graph.prompts.agent import AGENT_SYSTEM_PROMPT
from logic_graph.prompts.crisis import CRISIS_SYSTEM_PROMPT
from logic_graph.prompts.crisis_agent import CRISIS_AGENT_SYSTEM_PROMPT
from logic_graph.prompts.hallucination import HALLUCINATION_SYSTEM_PROMPT
from logic_graph.prompts.memory import (
    CUMULATIVE_SUMMARY_SYSTEM_PROMPT,
    METADATA_EXTRACTION_SYSTEM_PROMPT,
)

__all__ = [
    "AGENT_SYSTEM_PROMPT",
    "CRISIS_AGENT_SYSTEM_PROMPT",
    "CRISIS_SYSTEM_PROMPT",
    "CUMULATIVE_SUMMARY_SYSTEM_PROMPT",
    "HALLUCINATION_SYSTEM_PROMPT",
    "METADATA_EXTRACTION_SYSTEM_PROMPT",
]
