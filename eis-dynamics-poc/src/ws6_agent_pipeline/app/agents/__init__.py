"""
Agents for the Agent Pipeline.

Provides Bronze, Silver, Gold, and Router agents for medallion architecture processing.
"""

from .bronze_agent import BronzeAgent, bronze_agent
from .gold_agent import GoldAgent, gold_agent
from .router_agent import RouterAgent, router_agent
from .silver_agent import SilverAgent, silver_agent

__all__ = [
    "RouterAgent",
    "router_agent",
    "BronzeAgent",
    "bronze_agent",
    "SilverAgent",
    "silver_agent",
    "GoldAgent",
    "gold_agent",
]
