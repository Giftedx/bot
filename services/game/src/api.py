from typing import Optional, Dict, Any, List
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from datetime import datetime

from .service import GameService
from .models import (
    GameState, Position, CombatStats, Equipment, InventoryItem,
    BankItem, Skills, ActionResult, SkillType, QuestStatus
)

# Pydantic models for API
class ActionRequest(BaseModel):
    action: str
    params: Optional[Dict[str, Any]] = None

class ActionResponse(BaseModel):
    success: bool
    message: str
    experience_gained: Optional[Dict[str, int]] = None
    items_gained: Optional[List[Dict[str, Any]]] = None
    items_lost: Optional[List[Dict[str, Any]]] = None
    state_updates: Optional[Dict[str, Any]] = None

class PositionUpdate(BaseModel):
    x: int
    y: int
    z: Optional[int] = 0
    region_id: Optional[int] = None

class SkillUpdate(BaseModel):
    skill: str
    level: int
    experience: int

# Create FastAPI app
app = FastAPI(title="Game Service API")

# Service instance will be injected
game_service: GameService = None

def init_api(service: GameService):
    """Initialize the API with service instance"""
    global game_service
    game_service = service

async def get_current_user(token: str) -> str:
    """Get current user from token - this would use the identity service"""
    # TODO: Implement token validation
    return token

@app.get("/state", response_model=Dict[str, Any])
async def get_state(current_user: str = Depends(get_current_user)):
    """Get current game state"""
    state = await game_service.get_game_state(current_user)
    if not state:
        raise HTTPException(
            status_code=404,
            detail="Game state not found"
        )
    return state.__dict__

@app.post("/action", response_model=ActionResponse)
async def perform_action(
    action_request: ActionRequest,
    current_user: str = Depends(get_current_user)
):
    """Perform a game action"""
    result = await game_service.perform_action(
        current_user,
        action_request.action,
        action_request.params
    )
    
    return ActionResponse(
        success=result.success,
        message=result.message,
        experience_gained={k.value: v for k, v in (result.experience_gained or {}).items()},
        items_gained=[item.__dict__ for item in (result.items_gained or [])],
        items_lost=[item.__dict__ for item in (result.items_lost or [])],
        state_updates=result.state_updates
    )

@app.put("/position", response_model=ActionResponse)
async def update_position(
    position: PositionUpdate,
    current_user: str = Depends(get_current_user)
):
    """Update player position"""
    result = await game_service.perform_action(
        current_user,
        "move_to",
        {"position": position.dict()}
    )
    
    return ActionResponse(
        success=result.success,
        message=result.message,
        state_updates=result.state_updates
    )

@app.post("/combat/attack", response_model=ActionResponse)
async def perform_attack(
    target: Dict[str, Any],
    current_user: str = Depends(get_current_user)
):
    """Perform combat attack"""
    result = await game_service.perform_action(
        current_user,
        "combat_attack",
        {"target": target}
    )
    
    return ActionResponse(
        success=result.success,
        message=result.message,
        experience_gained={k.value: v for k, v in (result.experience_gained or {}).items()},
        state_updates=result.state_updates
    )

@app.post("/skill/{skill_name}", response_model=ActionResponse)
async def perform_skill_action(
    skill_name: str,
    action_params: Dict[str, Any],
    current_user: str = Depends(get_current_user)
):
    """Perform skill action"""
    result = await game_service.perform_action(
        current_user,
        f"skill_{skill_name}",
        action_params
    )
    
    return ActionResponse(
        success=result.success,
        message=result.message,
        experience_gained={k.value: v for k, v in (result.experience_gained or {}).items()},
        items_gained=[item.__dict__ for item in (result.items_gained or [])],
        state_updates=result.state_updates
    )

@app.post("/item/equip", response_model=ActionResponse)
async def equip_item(
    item: Dict[str, Any],
    current_user: str = Depends(get_current_user)
):
    """Equip an item"""
    result = await game_service.perform_action(
        current_user,
        "item_equip",
        {"item": item}
    )
    
    return ActionResponse(
        success=result.success,
        message=result.message,
        state_updates=result.state_updates
    )

@app.post("/item/unequip", response_model=ActionResponse)
async def unequip_item(
    item: Dict[str, Any],
    current_user: str = Depends(get_current_user)
):
    """Unequip an item"""
    result = await game_service.perform_action(
        current_user,
        "item_unequip",
        {"item": item}
    )
    
    return ActionResponse(
        success=result.success,
        message=result.message,
        state_updates=result.state_updates
    )

@app.get("/skills", response_model=Dict[str, Dict[str, int]])
async def get_skills(current_user: str = Depends(get_current_user)):
    """Get skill levels and experience"""
    state = await game_service.get_game_state(current_user)
    if not state:
        raise HTTPException(
            status_code=404,
            detail="Game state not found"
        )
        
    return {
        "levels": {k.value: v for k, v in state.skills.levels.items()},
        "experience": {k.value: v for k, v in state.skills.experience.items()}
    }

@app.get("/inventory", response_model=List[Dict[str, Any]])
async def get_inventory(current_user: str = Depends(get_current_user)):
    """Get inventory contents"""
    state = await game_service.get_game_state(current_user)
    if not state:
        raise HTTPException(
            status_code=404,
            detail="Game state not found"
        )
        
    return [item.__dict__ for item in state.inventory]

@app.get("/equipment", response_model=Dict[str, Optional[str]])
async def get_equipment(current_user: str = Depends(get_current_user)):
    """Get equipped items"""
    state = await game_service.get_game_state(current_user)
    if not state:
        raise HTTPException(
            status_code=404,
            detail="Game state not found"
        )
        
    return state.equipment.__dict__

@app.get("/bank", response_model=List[Dict[str, Any]])
async def get_bank(current_user: str = Depends(get_current_user)):
    """Get bank contents"""
    state = await game_service.get_game_state(current_user)
    if not state:
        raise HTTPException(
            status_code=404,
            detail="Game state not found"
        )
        
    return [item.__dict__ for item in state.bank]

@app.get("/quests", response_model=Dict[str, str])
async def get_quest_progress(current_user: str = Depends(get_current_user)):
    """Get quest progress"""
    state = await game_service.get_game_state(current_user)
    if not state:
        raise HTTPException(
            status_code=404,
            detail="Game state not found"
        )
        
    return {k: v.value for k, v in state.quest_progress.items()}

@app.get("/achievements", response_model=Dict[str, bool])
async def get_achievements(current_user: str = Depends(get_current_user)):
    """Get achievement progress"""
    state = await game_service.get_game_state(current_user)
    if not state:
        raise HTTPException(
            status_code=404,
            detail="Game state not found"
        )
        
    return state.achievement_progress

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    status = await game_service.health_check()
    return {
        "status": status.status,
        "version": status.version,
        "uptime": status.uptime,
        "last_check": status.last_check
    } 