import uuid
from typing import List
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from app.core.config import settings, TeamConfig
from app.schemas.gateway import TeamResponse

router = APIRouter(prefix="/v1/teams", tags=["Team & Budget Admin"])

class CreateTeamRequest(BaseModel):
    name: str
    rpm_limit: int = 60
    tpm_limit: int = 100000
    monthly_budget_usd: float = 100.0
    priority: int = 2

class UpdateBudgetRequest(BaseModel):
    monthly_budget_usd: float

@router.get("", response_model=List[TeamResponse])
async def list_teams():
    res = []
    for team in settings.teams.values():
        used_pct = (team.current_spend_usd / team.monthly_budget_usd * 100.0) if team.monthly_budget_usd > 0 else 0.0
        res.append(
            TeamResponse(
                id=team.id,
                name=team.name,
                api_key=team.api_key,
                rpm_limit=team.rpm_limit,
                tpm_limit=team.tpm_limit,
                monthly_budget_usd=team.monthly_budget_usd,
                current_spend_usd=round(team.current_spend_usd, 4),
                budget_used_percentage=round(used_pct, 1),
                allowed_tiers=team.allowed_tiers,
                priority=team.priority
            )
        )
    return res

@router.post("", response_model=TeamResponse)
async def create_team(req: CreateTeamRequest):
    new_id = f"team-{uuid.uuid4().hex[:6]}"
    new_key = f"sk-{new_id}-key"
    
    new_team = TeamConfig(
        id=new_id,
        name=req.name,
        api_key=new_key,
        rpm_limit=req.rpm_limit,
        tpm_limit=req.tpm_limit,
        monthly_budget_usd=req.monthly_budget_usd,
        current_spend_usd=0.0,
        priority=req.priority
    )
    settings.teams[new_key] = new_team
    
    return TeamResponse(
        id=new_team.id,
        name=new_team.name,
        api_key=new_team.api_key,
        rpm_limit=new_team.rpm_limit,
        tpm_limit=new_team.tpm_limit,
        monthly_budget_usd=new_team.monthly_budget_usd,
        current_spend_usd=0.0,
        budget_used_percentage=0.0,
        allowed_tiers=new_team.allowed_tiers,
        priority=new_team.priority
    )

@router.patch("/{team_id}/budget", response_model=TeamResponse)
async def update_team_budget(team_id: str, req: UpdateBudgetRequest):
    found_team = None
    for team in settings.teams.values():
        if team.id == team_id or team.api_key == team_id:
            found_team = team
            break
            
    if not found_team:
        raise HTTPException(status_code=404, detail="Team not found")

    found_team.monthly_budget_usd = req.monthly_budget_usd
    used_pct = (found_team.current_spend_usd / found_team.monthly_budget_usd * 100.0) if found_team.monthly_budget_usd > 0 else 0.0

    return TeamResponse(
        id=found_team.id,
        name=found_team.name,
        api_key=found_team.api_key,
        rpm_limit=found_team.rpm_limit,
        tpm_limit=found_team.tpm_limit,
        monthly_budget_usd=found_team.monthly_budget_usd,
        current_spend_usd=round(found_team.current_spend_usd, 4),
        budget_used_percentage=round(used_pct, 1),
        allowed_tiers=found_team.allowed_tiers,
        priority=found_team.priority
    )
