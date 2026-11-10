"""Multi-agent research assistant — supervisor-orchestrated, offline-first."""

from .supervisor import BudgetTracker, Supervisor

__version__ = "0.2.0"
__all__ = ["Supervisor", "BudgetTracker", "__version__"]
