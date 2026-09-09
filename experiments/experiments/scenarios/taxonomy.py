from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ScenarioDefinition:
    name: str
    fault_family: str
    primary_cause: str
    description: str


SCENARIOS = {
    "normal": ScenarioDefinition("normal", "none", "none", "Normal operational variation."),
    "traffic_spike": ScenarioDefinition("traffic_spike", "demand", "traffic_surge", "Demand rises without an injected service fault."),
    "latency_increase": ScenarioDefinition("latency_increase", "service", "service_delay", "Response latency rises independently of demand."),
    "database_slowdown": ScenarioDefinition("database_slowdown", "database", "database_slowdown", "Database latency propagates to response latency and errors."),
    "error_burst_5xx": ScenarioDefinition("error_burst_5xx", "application", "application_error_burst", "5xx errors rise independently of demand."),
}

ESSENTIAL_SCENARIOS = tuple(name for name in SCENARIOS if name != "normal")
