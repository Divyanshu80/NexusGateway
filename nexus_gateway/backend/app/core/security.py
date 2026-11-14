from typing import Optional
from fastapi import Header, HTTPException, status
from app.core.config import settings, TeamConfig

async def get_current_team(
    authorization: Optional[str] = Header(None),
    x_api_key: Optional[str] = Header(None)
) -> TeamConfig:
    api_key = None
    if authorization and authorization.startswith("Bearer "):
        api_key = authorization.replace("Bearer ", "").strip()
    elif x_api_key:
        api_key = x_api_key.strip()
    
    # Fallback default key if testing locally without headers
    if not api_key:
        api_key = "sk-team-alpha-key"
    
    team = settings.teams.get(api_key)
    if not team:
        # Check by team ID search
        for t in settings.teams.values():
            if t.api_key == api_key or t.id == api_key:
                return t
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Team API Key provided to NexusGateway."
        )
    return team
