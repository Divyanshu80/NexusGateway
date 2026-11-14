from typing import Tuple
from app.core.config import TeamConfig, settings

class BudgetTrackerService:
    def calculate_request_cost(self, model: str, prompt_tokens: int, completion_tokens: int) -> float:
        pricing = settings.pricing.get(model)
        if not pricing:
            # Default fallback pricing ($0.001 / 1k tokens)
            input_rate = 0.001
            output_rate = 0.002
        else:
            input_rate = pricing.input_cost_per_1k
            output_rate = pricing.output_cost_per_1k

        cost = ((prompt_tokens / 1000.0) * input_rate) + ((completion_tokens / 1000.0) * output_rate)
        return round(cost, 6)

    def check_budget(self, team: TeamConfig) -> Tuple[bool, bool, str]:
        """
        Returns (allowed: bool, warning_triggered: bool, message: str)
        """
        if team.monthly_budget_usd <= 0:
            return True, False, "Unlimited budget"

        usage_pct = (team.current_spend_usd / team.monthly_budget_usd) * 100.0
        
        if usage_pct >= 100.0:
            return False, True, f"Budget Exceeded: Spend ${team.current_spend_usd:.2f} reached monthly limit ${team.monthly_budget_usd:.2f}"
        elif usage_pct >= 80.0:
            return True, True, f"Budget Warning: Spend ${team.current_spend_usd:.2f} is at {usage_pct:.1f}% of ${team.monthly_budget_usd:.2f} budget"
        
        return True, False, "Budget OK"

    def record_spending(self, team_id: str, cost_usd: float):
        for t in settings.teams.values():
            if t.id == team_id or t.api_key == team_id:
                t.current_spend_usd = round(t.current_spend_usd + cost_usd, 6)
                break

budget_tracker = BudgetTrackerService()
