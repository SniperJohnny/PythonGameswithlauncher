"""Levels are plain Python modules with a single LEVEL object, auto-discovered here.

Grid legend: # block, M moving block, P spawn, C checkpoint, F fire, ^ spikes,
S saw, A arrow launcher, T trampoline, X enemy, L lever, G gate, E goal, . empty.

A gate stays solid until every lever in the level is pulled, so a vault (a pit
with walls too tall to jump) is only escapable by rewinding back out of it.
"""
import importlib
import pkgutil
from dataclasses import dataclass, field


@dataclass
class Level:
    number: int
    name: str
    background: str
    rows: list
    hints: list = field(default_factory=list)

    @property
    def title(self):
        return f"Level {self.number} - {self.name}"

    @property
    def key(self):
        """Key used for save progress and leaderboard entries."""
        return f"level{self.number}"


def _discover():
    found = []
    for info in pkgutil.iter_modules(__path__):
        module = importlib.import_module(f"{__name__}.{info.name}")
        level = getattr(module, "LEVEL", None)
        if isinstance(level, Level):
            found.append(level)
    return sorted(found, key=lambda level: level.number)


LEVELS = _discover()
