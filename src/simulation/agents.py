"""Agent definitions for the contagion simulation."""

import numpy as np
from typing import Dict, List, Optional, Any
from loguru import logger


class BaseAgent:
    """Base agent class for Mesa 3.x compatibility."""

    def __init__(self, unique_id: str, model: "DeFiEnvironment"):
        self.unique_id = unique_id
        self.model = model

    def step(self):
        """Override in subclass."""
        pass


class StablecoinAgent(BaseAgent):
    """Agent representing a stablecoin in the simulation."""

    def __init__(
        self,
        unique_id: str,
        model: "DeFiEnvironment",
        **kwargs
    ):
        """
        Initialize stablecoin agent.

        Args:
            unique_id: Stablecoin symbol
            model: Parent model
            **kwargs: Additional properties
        """
        super().__init__(unique_id, model)
        self.symbol = unique_id
        self.price = 1.0
        self.market_cap = kwargs.get("market_cap", 1e9)
        self.collateral = kwargs.get("collateral", [])
        self.collateral_ratio = kwargs.get("collateral_ratio", 1.0)
        self.is_algorithmic = kwargs.get("is_algorithmic", False)
        self.stablecoin_type = kwargs.get("stablecoin_type", "fiat-backed")

        # State variables
        self.is_depegged = False
        self.depeg_severity = 0.0
        self.confidence = 1.0
        self.trading_volume = kwargs.get("trading_volume", 0.0)

        # Tracking
        self.price_history = [1.0]
        self.confidence_history = [1.0]
        self.triggered_cascade = False

    def step(self):
        """Execute one step of the simulation."""
        # Check collateral health
        collateral_health = self._calculate_collateral_health()

        # Confidence drops if collateral is unhealthy
        if collateral_health < 0.95:
            confidence_drop = self.model.config.get("confidence_decay_rate", 0.1)
            self.confidence *= (1 - confidence_drop * (1 - collateral_health))

        # Apply market sentiment effects
        self._apply_market_sentiment()

        # Price follows confidence with noise
        noise_std = self.model.config.get("noise_std", 0.01)
        noise = np.random.normal(0, noise_std)
        self.price = max(0.01, self.confidence + noise)

        # Update depeg status
        self.depeg_severity = abs(1.0 - self.price)
        self.is_depegged = self.depeg_severity > self.model.depeg_threshold

        # Algorithmic stablecoins have death spiral risk
        if self.is_algorithmic and self.is_depegged:
            death_spiral_factor = self.model.config.get("algorithmic_death_spiral_factor", 0.9)
            self.price *= death_spiral_factor
            self.confidence *= death_spiral_factor

        # Track history
        self.price_history.append(self.price)
        self.confidence_history.append(self.confidence)

        # Log significant events
        if self.is_depegged and not self.triggered_cascade:
            logger.info(f"Step {self.model.step_count}: {self.symbol} depegged at ${self.price:.4f}")
            self.triggered_cascade = True

    def _calculate_collateral_health(self) -> float:
        """
        Calculate health of collateral backing this stablecoin.

        Returns:
            Health score between 0 and 1
        """
        if not self.collateral:
            return 1.0

        health_sum = 0
        for collateral_symbol in self.collateral:
            collateral_agent = self.model.get_agent_by_id(collateral_symbol)
            if collateral_agent and hasattr(collateral_agent, 'price'):
                health_sum += collateral_agent.price
            else:
                health_sum += 1.0

        return health_sum / len(self.collateral)

    def _apply_market_sentiment(self):
        """Apply market-wide sentiment effects to confidence."""
        # If other stablecoins are depegging, confidence drops
        depegged_count = sum(
            1 for agent in self.model.schedule.agents
            if isinstance(agent, StablecoinAgent)
            and agent.is_depegged
            and agent.unique_id != self.unique_id
        )

        if depegged_count > 0:
            sentiment_impact = 0.02 * depegged_count
            self.confidence *= (1 - sentiment_impact)

    def trigger_depeg(self, severity: float = 0.1):
        """
        Externally trigger a depeg event.

        Args:
            severity: Severity of initial depeg (0-1)
        """
        self.confidence = 1.0 - severity
        self.price = self.confidence
        self.is_depegged = True
        self.triggered_cascade = True
        logger.info(f"Triggered depeg for {self.symbol} at severity {severity}")

    def recover(self, recovery_rate: float = 0.1):
        """
        Attempt to recover from depeg.

        Args:
            recovery_rate: Rate of confidence recovery
        """
        if self.confidence < 1.0:
            self.confidence = min(1.0, self.confidence + recovery_rate)

    def get_state(self) -> Dict[str, Any]:
        """Get current state of the agent."""
        return {
            "symbol": self.symbol,
            "price": self.price,
            "confidence": self.confidence,
            "is_depegged": self.is_depegged,
            "depeg_severity": self.depeg_severity,
            "market_cap": self.market_cap
        }


class ProtocolAgent(BaseAgent):
    """Agent representing a DeFi protocol in the simulation."""

    def __init__(
        self,
        unique_id: str,
        model: "DeFiEnvironment",
        **kwargs
    ):
        """
        Initialize protocol agent.

        Args:
            unique_id: Protocol slug/name
            model: Parent model
            **kwargs: Additional properties
        """
        super().__init__(unique_id, model)
        self.name = unique_id
        self.tvl = kwargs.get("tvl", 1e8)
        self.initial_tvl = self.tvl
        self.stablecoin_exposures: Dict[str, float] = kwargs.get("exposures", {})
        self.liquidation_threshold = kwargs.get("liquidation_threshold", 0.8)
        self.category = kwargs.get("category", "other")

        # State variables
        self.is_distressed = False
        self.tvl_lost = 0.0
        self.health_factor = 1.0

        # Tracking
        self.tvl_history = [self.tvl]
        self.distress_step = None

    def step(self):
        """Execute one step of the simulation."""
        total_exposure_loss = 0.0

        # Calculate losses from depegged stablecoins
        for stablecoin, exposure in self.stablecoin_exposures.items():
            agent = self.model.get_agent_by_id(stablecoin)
            if agent and hasattr(agent, 'is_depegged') and agent.is_depegged:
                # Loss proportional to depeg severity and exposure
                loss = exposure * agent.depeg_severity
                total_exposure_loss += loss

        # Update TVL
        self.tvl_lost = total_exposure_loss
        self.tvl = max(0, self.initial_tvl - total_exposure_loss)

        # Calculate health factor
        if self.initial_tvl > 0:
            self.health_factor = self.tvl / self.initial_tvl

        # Check distress condition
        loss_ratio = total_exposure_loss / max(self.initial_tvl, 1)
        was_distressed = self.is_distressed
        self.is_distressed = loss_ratio > (1 - self.liquidation_threshold)

        # Log distress events
        if self.is_distressed and not was_distressed:
            self.distress_step = self.model.step_count
            logger.info(
                f"Step {self.model.step_count}: Protocol {self.name} distressed "
                f"(TVL lost: ${self.tvl_lost:,.0f})"
            )

        # Track history
        self.tvl_history.append(self.tvl)

    def exposure_to(self, stablecoin: str) -> float:
        """Get exposure to a specific stablecoin."""
        return self.stablecoin_exposures.get(stablecoin, 0.0)

    def exposure_ratio_to(self, stablecoin: str) -> float:
        """Get exposure ratio to a specific stablecoin."""
        if self.initial_tvl == 0:
            return 0.0
        return self.exposure_to(stablecoin) / self.initial_tvl

    def get_state(self) -> Dict[str, Any]:
        """Get current state of the agent."""
        return {
            "name": self.name,
            "tvl": self.tvl,
            "initial_tvl": self.initial_tvl,
            "tvl_lost": self.tvl_lost,
            "is_distressed": self.is_distressed,
            "health_factor": self.health_factor,
            "category": self.category
        }


class LiquidatorAgent(BaseAgent):
    """Agent representing liquidators in the market."""

    def __init__(
        self,
        unique_id: str,
        model: "DeFiEnvironment",
        **kwargs
    ):
        """
        Initialize liquidator agent.

        Args:
            unique_id: Agent identifier
            model: Parent model
            **kwargs: Additional properties
        """
        super().__init__(unique_id, model)
        self.capital = kwargs.get("capital", 1e8)
        self.liquidation_profit = 0.0
        self.liquidations_executed = 0

    def step(self):
        """Execute liquidation opportunities."""
        for agent in self.model.schedule.agents:
            if isinstance(agent, ProtocolAgent) and agent.is_distressed:
                # Simulate liquidation
                liquidation_amount = min(agent.tvl_lost * 0.1, self.capital)
                if liquidation_amount > 0:
                    # Liquidator profit (typically 5-10% of liquidation)
                    profit = liquidation_amount * 0.05
                    self.liquidation_profit += profit
                    self.liquidations_executed += 1

    def get_state(self) -> Dict[str, Any]:
        """Get current state of the agent."""
        return {
            "capital": self.capital,
            "liquidation_profit": self.liquidation_profit,
            "liquidations_executed": self.liquidations_executed
        }


class ArbitragerAgent(BaseAgent):
    """Agent representing arbitragers who help restore peg."""

    def __init__(
        self,
        unique_id: str,
        model: "DeFiEnvironment",
        **kwargs
    ):
        """
        Initialize arbitrager agent.

        Args:
            unique_id: Agent identifier
            model: Parent model
            **kwargs: Additional properties
        """
        super().__init__(unique_id, model)
        self.capital = kwargs.get("capital", 1e7)
        self.arbitrage_profit = 0.0
        self.trades_executed = 0
        self.peg_support_strength = kwargs.get("peg_support_strength", 0.01)

    def step(self):
        """Execute arbitrage opportunities to support peg."""
        for agent in self.model.schedule.agents:
            if isinstance(agent, StablecoinAgent) and agent.is_depegged:
                # Arbitragers buy below peg, sell above peg
                if agent.price < 0.99:
                    # Buy pressure helps restore peg
                    support = self.peg_support_strength * (1.0 - agent.price)
                    agent.confidence += support
                    self.trades_executed += 1
                    self.arbitrage_profit += support * self.capital * 0.01

    def get_state(self) -> Dict[str, Any]:
        """Get current state of the agent."""
        return {
            "capital": self.capital,
            "arbitrage_profit": self.arbitrage_profit,
            "trades_executed": self.trades_executed
        }
