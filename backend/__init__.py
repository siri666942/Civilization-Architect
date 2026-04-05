"""
智械星海：戴森球拓荒者 - 后端核心模块

基于大语言模型（LLM）的多智能体社会动力学博弈模拟器
"""

__version__ = "0.1.0"

from backend.models import (
    Agent, Personality, AgentState, ArchitectureType, TraitorBehavior, EnergyAllocation,
    ArchitectureConfig, ArchitectureFactory, ArchitectureAnalyzer, create_architecture
)
from backend.core import (
    GodAgent, initialize_agents,
    MacroVariableCalculator, ProductionCalculator, calculate_all_macro_variables,
    GameEngine, Civilization, GameState, TraitorEvent
)
from backend.common.config import GameConfig, default_config

__all__ = [
    # Models
    'Agent', 'Personality', 'AgentState', 'ArchitectureType', 'TraitorBehavior', 'EnergyAllocation',
    'ArchitectureConfig', 'ArchitectureFactory', 'ArchitectureAnalyzer', 'create_architecture',
    # Core
    'GodAgent', 'initialize_agents',
    'MacroVariableCalculator', 'ProductionCalculator', 'calculate_all_macro_variables',
    'GameEngine', 'Civilization', 'GameState', 'TraitorEvent',
    # Config
    'GameConfig', 'default_config'
]