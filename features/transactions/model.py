from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Transaction:
    trans_type: str
    category: str
    amount: float
    description: str = ""
    date: str = field(
        default_factory=lambda: datetime.now().strftime("%Y-%m-%d")
    )
    id: Optional[int] = None