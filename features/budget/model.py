from dataclasses import dataclass
from typing import Optional


@dataclass
class Budget:
    category: str
    monthly_limit: float
    month: str  # Format: "YYYY-MM"
    id: Optional[int] = None