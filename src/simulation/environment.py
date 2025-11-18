"""DeFi environment for contagion simulation."""

import numpy as np
from typing import Dict, List, Optional, Any
from loguru import logger

from .agents import StablecoinAgent, ProtocolAgent, LiquidatorAgent, ArbitragerAgent


class SimpleScheduler:
    """Simple scheduler for Mesa 3.x compatibility."""

    def __init__(self, model):
        self.model = model
        self._agents = []
        self.steps = 0

    def add(self, agent):
        """Add an agent to the scheduler."""
        self._agents.append(agent)

    @property
    def agents(self):
        """Return list of agents."""
        return self._agents

    def step(self):
        """Execute step for all agents."""
        for agent in self._agents:
            agent.step()
        self.steps += 1


class SimpleDataCollector:
    """Simple data collector for Mesa 3.x compatibility."""

    def __init__(self, model_reporters: Dict = None, agent_reporters: Dict = None):
        self.model_reporters = model_reporters or {}
        self.agent_reporters = agent_reporters or {}
        self._model_data = {name: [] for name in self.model_reporters}
        self._agent_data = []

    def collect(self, model):
        """Collect data from model and agents."""
        # Collect model-level data
        for name, reporter in self.model_reporters.items():
            self._model_data[name].append(reporter())

        # Collect agent-level data
        step_data = []
        for agent in model.schedule.agents:
            agent_record = {"Step": model.step_count, "AgentID": agent.unique_id}
            for name, reporter in self.agent_reporters.items():
                agent_record[name] = reporter(agent)
            step_data.append(agent_record)
        self._agent_data.extend(step_data)

    def get_model_vars_dataframe(self):
        """Return model data as DataFrame."""
        import pandas as pd
        return pd.DataFrame(self._model_data)

    def get_agent_vars_dataframe(self):
        """Return agent data as DataFrame."""
        import pandas as pd
        if not self._agent_data:
            return pd.DataFrame()
        return pd.DataFrame(self._agent_data)


class DeFiEnvironment:
    """
    DeFi environment model for simulating stablecoin depeg contagion.

    This model simulates the interaction between stablecoins, DeFi protocols,
    liquidators, and arbitragers during a depeg event.
    """

    def __init__(
        self,
        stablecoins: List[Dict],
        protocols: List[Dict],
        config: Optional[Dict] = None,
        include_liquidators: bool = True,
        include_arbitragers: bool = True,
        seed: Optional[int] = None
    ):
        """
        Initialize DeFi environment.

        Args:
            stablecoins: List of stablecoin configurations
            protocols: List of protocol configurations
            config: Simulation configuration parameters
            include_liquidators: Whether to include liquidator agents
            include_arbitragers: Whether to include arbitrager agents
            seed: Random seed for reproducibility
        """

        if seed is not None:
            np.random.seed(seed)

        # Configuration
        self.config = config or {}
        self.depeg_threshold = self.config.get("depeg_threshold", 0.02)
        self.max_steps = self.config.get("max_steps", 100)

        # Scheduler (Mesa 3.x compatible)
        self.schedule = SimpleScheduler(self)

        # State
        self.running = True
        self.step_count = 0

        # Agent tracking
        self.stablecoin_agents: Dict[str, StablecoinAgent] = {}
        self.protocol_agents: Dict[str, ProtocolAgent] = {}
        self.other_agents: List[Any] = []

        # Create stablecoin agents
        for sc_config in stablecoins:
            agent = StablecoinAgent(
                unique_id=sc_config["symbol"],
                model=self,
                **sc_config
            )
            self.schedule.add(agent)
            self.stablecoin_agents[sc_config["symbol"]] = agent

        # Create protocol agents
        for proto_config in protocols:
            agent = ProtocolAgent(
                unique_id=proto_config["name"],
                model=self,
                **proto_config
            )
            self.schedule.add(agent)
            self.protocol_agents[proto_config["name"]] = agent

        # Add liquidators
        if include_liquidators:
            for i in range(self.config.get("num_liquidators", 3)):
                agent = LiquidatorAgent(
                    unique_id=f"liquidator_{i}",
                    model=self,
                    capital=self.config.get("liquidator_capital", 1e8)
                )
                self.schedule.add(agent)
                self.other_agents.append(agent)

        # Add arbitragers
        if include_arbitragers:
            for i in range(self.config.get("num_arbitragers", 5)):
                agent = ArbitragerAgent(
                    unique_id=f"arbitrager_{i}",
                    model=self,
                    capital=self.config.get("arbitrager_capital", 1e7),
                    peg_support_strength=self.config.get("peg_support_strength", 0.01)
                )
                self.schedule.add(agent)
                self.other_agents.append(agent)

        # Data collector
        self.datacollector = SimpleDataCollector(
            model_reporters={
                "Total_TVL_Lost": self._total_tvl_lost,
                "Depegged_Stablecoins": self._count_depegged,
                "Distressed_Protocols": self._count_distressed,
                "Average_Stablecoin_Price": self._avg_stablecoin_price,
                "Total_TVL": self._total_tvl,
                "Contagion_Index": self._contagion_index,
            },
            agent_reporters={
                "Price": lambda a: getattr(a, "price", None),
                "TVL": lambda a: getattr(a, "tvl", None),
                "Is_Depegged": lambda a: getattr(a, "is_depegged", None),
                "Is_Distressed": lambda a: getattr(a, "is_distressed", None),
                "Confidence": lambda a: getattr(a, "confidence", None),
            }
        )

        logger.info(
            f"Initialized DeFi environment with {len(stablecoins)} stablecoins, "
            f"{len(protocols)} protocols"
        )

    def get_agent_by_id(self, unique_id: str) -> Optional[Any]:
        """
        Get agent by unique ID.

        Args:
            unique_id: Agent identifier

        Returns:
            Agent or None if not found
        """
        if unique_id in self.stablecoin_agents:
            return self.stablecoin_agents[unique_id]
        if unique_id in self.protocol_agents:
            return self.protocol_agents[unique_id]
        for agent in self.other_agents:
            if agent.unique_id == unique_id:
                return agent
        return None

    def trigger_depeg(self, stablecoin: str, severity: float = 0.1):
        """
        Trigger a depeg event for a stablecoin.

        Args:
            stablecoin: Stablecoin symbol to depeg
            severity: Severity of depeg (0-1)
        """
        agent = self.stablecoin_agents.get(stablecoin)
        if agent:
            agent.trigger_depeg(severity)
            logger.info(f"Triggered {stablecoin} depeg at {severity*100:.1f}% severity")
        else:
            logger.warning(f"Stablecoin {stablecoin} not found in environment")

    def step(self):
        """Execute one step of the model."""
        self.datacollector.collect(self)
        self.schedule.step()
        self.step_count += 1

        # Check for cascade completion (no more depegs propagating)
        if self._count_depegged() == 0 and self.step_count > 5:
            logger.info(f"Cascade completed at step {self.step_count}")
            self.running = False

        # Check max steps
        if self.step_count >= self.max_steps:
            logger.info(f"Max steps ({self.max_steps}) reached")
            self.running = False

    def run_simulation(self, max_steps: Optional[int] = None) -> Dict[str, Any]:
        """
        Run full simulation and return results.

        Args:
            max_steps: Maximum steps to run (overrides config)

        Returns:
            Simulation results dictionary
        """
        steps_to_run = max_steps or self.max_steps

        for _ in range(steps_to_run):
            if not self.running:
                break
            self.step()

        return self.get_results()

    def get_results(self) -> Dict[str, Any]:
        """
        Get simulation results.

        Returns:
            Results dictionary with metrics and history
        """
        return {
            "steps": self.step_count,
            "total_tvl_lost": self._total_tvl_lost(),
            "depegged_stablecoins": self._count_depegged(),
            "distressed_protocols": self._count_distressed(),
            "final_avg_price": self._avg_stablecoin_price(),
            "contagion_index": self._contagion_index(),
            "history": self.datacollector.get_model_vars_dataframe(),
            "agent_history": self.datacollector.get_agent_vars_dataframe(),
            "stablecoin_final_states": self._get_stablecoin_states(),
            "protocol_final_states": self._get_protocol_states()
        }

    def _get_stablecoin_states(self) -> List[Dict]:
        """Get final state of all stablecoins."""
        return [agent.get_state() for agent in self.stablecoin_agents.values()]

    def _get_protocol_states(self) -> List[Dict]:
        """Get final state of all protocols."""
        return [agent.get_state() for agent in self.protocol_agents.values()]

    def _total_tvl_lost(self) -> float:
        """Calculate total TVL lost across all protocols."""
        return sum(
            agent.tvl_lost
            for agent in self.protocol_agents.values()
        )

    def _total_tvl(self) -> float:
        """Calculate current total TVL."""
        return sum(
            agent.tvl
            for agent in self.protocol_agents.values()
        )

    def _count_depegged(self) -> int:
        """Count currently depegged stablecoins."""
        return sum(
            1 for agent in self.stablecoin_agents.values()
            if agent.is_depegged
        )

    def _count_distressed(self) -> int:
        """Count distressed protocols."""
        return sum(
            1 for agent in self.protocol_agents.values()
            if agent.is_distressed
        )

    def _avg_stablecoin_price(self) -> float:
        """Calculate average stablecoin price."""
        prices = [agent.price for agent in self.stablecoin_agents.values()]
        return np.mean(prices) if prices else 1.0

    def _contagion_index(self) -> float:
        """
        Calculate contagion index (0-1).

        Higher values indicate more severe contagion.
        """
        depegged_ratio = self._count_depegged() / max(len(self.stablecoin_agents), 1)
        distressed_ratio = self._count_distressed() / max(len(self.protocol_agents), 1)
        tvl_loss_ratio = self._total_tvl_lost() / max(self._total_tvl() + self._total_tvl_lost(), 1)

        return (depegged_ratio + distressed_ratio + tvl_loss_ratio) / 3

    def get_cascade_timeline(self) -> List[Dict]:
        """
        Get timeline of cascade events.

        Returns:
            List of events with timestamps
        """
        events = []

        for symbol, agent in self.stablecoin_agents.items():
            if agent.triggered_cascade:
                # Find when it depegged
                for i, price in enumerate(agent.price_history):
                    if abs(price - 1.0) > self.depeg_threshold:
                        events.append({
                            "step": i,
                            "type": "depeg",
                            "entity": symbol,
                            "value": price
                        })
                        break

        for name, agent in self.protocol_agents.items():
            if agent.distress_step is not None:
                events.append({
                    "step": agent.distress_step,
                    "type": "distress",
                    "entity": name,
                    "value": agent.tvl_lost
                })

        return sorted(events, key=lambda x: x["step"])

    def reset(self):
        """Reset the environment to initial state."""
        self.step_count = 0
        self.running = True

        for agent in self.stablecoin_agents.values():
            agent.price = 1.0
            agent.confidence = 1.0
            agent.is_depegged = False
            agent.depeg_severity = 0.0
            agent.triggered_cascade = False
            agent.price_history = [1.0]
            agent.confidence_history = [1.0]

        for agent in self.protocol_agents.values():
            agent.tvl = agent.initial_tvl
            agent.tvl_lost = 0.0
            agent.is_distressed = False
            agent.health_factor = 1.0
            agent.distress_step = None
            agent.tvl_history = [agent.tvl]

        logger.info("Environment reset to initial state")
