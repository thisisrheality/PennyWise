from dataclasses import dataclass

@dataclass
class SavingsGoal:
    title: str
    target_amount: float
    current_amount: float = 0.0
    id: int | None = None

    def __post_init__(self) -> None:
        self.title = self.title.strip().title()
        if not self.title:
            raise ValueError("Goal title is required.")
        if self.target_amount <= 0:
            raise ValueError("Target amount must be greater than zero.")
        if self.current_amount < 0:
            raise ValueError("Current amount cannot be negative.")