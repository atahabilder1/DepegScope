"""Tests for simulation modules."""

import pytest

from src.simulation.environment import DeFiEnvironment
from src.simulation.scenarios import (
    DepegScenario, ScenarioRunner,
    PREDEFINED_SCENARIOS, get_scenario, list_scenarios
)
from src.simulation.agents import StablecoinAgent, ProtocolAgent


class TestDeFiEnvironment:
    """Tests for DeFiEnvironment class."""

    def test_environment_creation(
        self, simulation_stablecoins, simulation_protocols, default_simulation_config
    ):
        """Test environment creation."""
        env = DeFiEnvironment(
            stablecoins=simulation_stablecoins,
            protocols=simulation_protocols,
            config=default_simulation_config,
            seed=42
        )

        assert env is not None
        assert len(env.schedule.agents) > 0

    def test_trigger_depeg(
        self, simulation_stablecoins, simulation_protocols, default_simulation_config
    ):
        """Test triggering a depeg event."""
        env = DeFiEnvironment(
            stablecoins=simulation_stablecoins,
            protocols=simulation_protocols,
            config=default_simulation_config,
            seed=42
        )

        env.trigger_depeg("USDC", severity=0.10)

        # Check that the stablecoin's price was affected
        usdc_agent = None
        for agent in env.schedule.agents:
            if isinstance(agent, StablecoinAgent) and agent.symbol == "USDC":
                usdc_agent = agent
                break

        assert usdc_agent is not None
        assert usdc_agent.price < 1.0

    def test_run_simulation(
        self, simulation_stablecoins, simulation_protocols, default_simulation_config
    ):
        """Test running a full simulation."""
        env = DeFiEnvironment(
            stablecoins=simulation_stablecoins,
            protocols=simulation_protocols,
            config=default_simulation_config,
            seed=42
        )

        env.trigger_depeg("USDC", severity=0.10)
        results = env.run_simulation()

        assert isinstance(results, dict)
        assert "steps" in results
        assert "total_tvl_lost" in results
        assert "depegged_stablecoins" in results
        assert "distressed_protocols" in results
        assert "contagion_index" in results

        assert results["steps"] > 0
        assert results["total_tvl_lost"] >= 0

    def test_simulation_step(
        self, simulation_stablecoins, simulation_protocols, default_simulation_config
    ):
        """Test individual simulation step."""
        env = DeFiEnvironment(
            stablecoins=simulation_stablecoins,
            protocols=simulation_protocols,
            config=default_simulation_config,
            seed=42
        )

        env.trigger_depeg("USDC", severity=0.10)
        initial_step = env.schedule.steps

        env.step()

        assert env.schedule.steps == initial_step + 1

    def test_get_current_state(
        self, simulation_stablecoins, simulation_protocols, default_simulation_config
    ):
        """Test getting current state snapshot."""
        env = DeFiEnvironment(
            stablecoins=simulation_stablecoins,
            protocols=simulation_protocols,
            config=default_simulation_config,
            seed=42
        )

        state = env.get_current_state()

        assert isinstance(state, dict)
        assert "stablecoin_prices" in state
        assert "protocol_tvls" in state

    def test_reproducibility_with_seed(
        self, simulation_stablecoins, simulation_protocols, default_simulation_config
    ):
        """Test that same seed produces same results."""
        env1 = DeFiEnvironment(
            stablecoins=simulation_stablecoins,
            protocols=simulation_protocols,
            config=default_simulation_config,
            seed=42
        )
        env1.trigger_depeg("USDC", severity=0.10)
        results1 = env1.run_simulation()

        env2 = DeFiEnvironment(
            stablecoins=simulation_stablecoins,
            protocols=simulation_protocols,
            config=default_simulation_config,
            seed=42
        )
        env2.trigger_depeg("USDC", severity=0.10)
        results2 = env2.run_simulation()

        assert results1["steps"] == results2["steps"]
        assert results1["total_tvl_lost"] == results2["total_tvl_lost"]


class TestDepegScenario:
    """Tests for DepegScenario class."""

    def test_scenario_creation(self):
        """Test creating a custom scenario."""
        scenario = DepegScenario(
            name="test_scenario",
            description="A test scenario",
            trigger_stablecoin="USDC",
            initial_severity=0.10
        )

        assert scenario.name == "test_scenario"
        assert scenario.trigger_stablecoin == "USDC"
        assert scenario.initial_severity == 0.10

    def test_scenario_with_config_overrides(self):
        """Test scenario with custom config."""
        scenario = DepegScenario(
            name="custom",
            description="Custom config",
            trigger_stablecoin="USDT",
            initial_severity=0.20,
            config_overrides={"confidence_decay_rate": 0.2}
        )

        assert scenario.config_overrides["confidence_decay_rate"] == 0.2


class TestPredefinedScenarios:
    """Tests for predefined scenarios."""

    def test_list_scenarios(self):
        """Test listing available scenarios."""
        scenarios = list_scenarios()

        assert isinstance(scenarios, list)
        assert len(scenarios) > 0

    def test_get_scenario(self):
        """Test getting a predefined scenario."""
        scenarios = list_scenarios()
        if scenarios:
            scenario = get_scenario(scenarios[0])

            assert isinstance(scenario, DepegScenario)
            assert scenario.trigger_stablecoin is not None
            assert scenario.initial_severity > 0

    def test_predefined_scenarios_valid(self):
        """Test that all predefined scenarios are valid."""
        for name in list_scenarios():
            scenario = get_scenario(name)

            assert scenario.name == name
            assert 0 < scenario.initial_severity <= 1.0
            assert scenario.trigger_stablecoin is not None


class TestScenarioRunner:
    """Tests for ScenarioRunner class."""

    def test_runner_creation(self, simulation_stablecoins, simulation_protocols):
        """Test creating a scenario runner."""
        runner = ScenarioRunner(simulation_stablecoins, simulation_protocols)
        assert runner is not None

    def test_run_scenario(self, simulation_stablecoins, simulation_protocols):
        """Test running a single scenario."""
        runner = ScenarioRunner(simulation_stablecoins, simulation_protocols)

        scenario = DepegScenario(
            name="test",
            description="Test",
            trigger_stablecoin="USDC",
            initial_severity=0.10
        )

        results = runner.run_scenario(scenario, seed=42)

        assert isinstance(results, dict)
        assert "total_tvl_lost" in results

    def test_run_monte_carlo(self, simulation_stablecoins, simulation_protocols):
        """Test Monte Carlo simulation."""
        runner = ScenarioRunner(simulation_stablecoins, simulation_protocols)

        scenario = DepegScenario(
            name="test",
            description="Test",
            trigger_stablecoin="USDC",
            initial_severity=0.10
        )

        mc_results = runner.run_monte_carlo(scenario, n_runs=10, seed_start=0)

        assert isinstance(mc_results, dict)
        assert "tvl_loss" in mc_results
        assert "mean" in mc_results["tvl_loss"]
        assert "std" in mc_results["tvl_loss"]

    def test_compare_scenarios(self, simulation_stablecoins, simulation_protocols):
        """Test comparing multiple scenarios."""
        runner = ScenarioRunner(simulation_stablecoins, simulation_protocols)

        scenarios = [
            DepegScenario("s1", "Scenario 1", "USDC", 0.10),
            DepegScenario("s2", "Scenario 2", "USDT", 0.10),
        ]

        comparison = runner.compare_scenarios(scenarios, seed=42)

        assert isinstance(comparison, dict)
        assert len(comparison) == 2


class TestStablecoinAgent:
    """Tests for StablecoinAgent class."""

    def test_agent_creation(
        self, simulation_stablecoins, simulation_protocols, default_simulation_config
    ):
        """Test stablecoin agent creation."""
        env = DeFiEnvironment(
            stablecoins=simulation_stablecoins,
            protocols=simulation_protocols,
            config=default_simulation_config,
            seed=42
        )

        # Find a stablecoin agent
        stable_agent = None
        for agent in env.schedule.agents:
            if isinstance(agent, StablecoinAgent):
                stable_agent = agent
                break

        assert stable_agent is not None
        assert hasattr(stable_agent, "price")
        assert hasattr(stable_agent, "confidence")
        assert hasattr(stable_agent, "is_depegged")

    def test_agent_depeg_state(
        self, simulation_stablecoins, simulation_protocols, default_simulation_config
    ):
        """Test agent depeg state tracking."""
        env = DeFiEnvironment(
            stablecoins=simulation_stablecoins,
            protocols=simulation_protocols,
            config=default_simulation_config,
            seed=42
        )

        # Trigger severe depeg
        env.trigger_depeg("USDC", severity=0.50)

        # Find USDC agent
        usdc_agent = None
        for agent in env.schedule.agents:
            if isinstance(agent, StablecoinAgent) and agent.symbol == "USDC":
                usdc_agent = agent
                break

        assert usdc_agent is not None
        assert usdc_agent.price < 1.0


class TestProtocolAgent:
    """Tests for ProtocolAgent class."""

    def test_agent_creation(
        self, simulation_stablecoins, simulation_protocols, default_simulation_config
    ):
        """Test protocol agent creation."""
        env = DeFiEnvironment(
            stablecoins=simulation_stablecoins,
            protocols=simulation_protocols,
            config=default_simulation_config,
            seed=42
        )

        # Find a protocol agent
        proto_agent = None
        for agent in env.schedule.agents:
            if isinstance(agent, ProtocolAgent):
                proto_agent = agent
                break

        assert proto_agent is not None
        assert hasattr(proto_agent, "tvl")
        assert hasattr(proto_agent, "is_distressed")
