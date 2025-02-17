from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Depends, Request
from pydantic import BaseModel
import nacl.signing
import nacl.exceptions

from .service import DiscordService
from .models import Interaction, InteractionResponse, ERROR_EMBED

# Pydantic models for API
class WebhookBody(BaseModel):
    """Discord webhook body"""
    type: int
    token: str
    data: Optional[Dict[str, Any]] = None
    member: Optional[Dict[str, Any]] = None
    guild_id: Optional[str] = None
    channel_id: Optional[str] = None

# Create FastAPI app
app = FastAPI(title="Discord Service API")

# Service instance will be injected
discord_service: DiscordService = None
public_key: str = None

def init_api(service: DiscordService, discord_public_key: str):
    """Initialize the API with service instance"""
    global discord_service, public_key
    discord_service = service
    public_key = discord_public_key

def verify_signature(signature: str, timestamp: str, body: str) -> bool:
    """Verify Discord webhook signature"""
    try:
        verify_key = nacl.signing.VerifyKey(bytes.fromhex(public_key))
        verify_key.verify(
            f"{timestamp}{body}".encode(),
            bytes.fromhex(signature)
        )
        return True
    except nacl.exceptions.BadSignatureError:
        return False

@app.post("/webhook")
async def discord_webhook(
    request: Request,
    body: WebhookBody
):
    """Handle Discord webhook"""
    # Verify signature
    signature = request.headers.get("X-Signature-Ed25519")
    timestamp = request.headers.get("X-Signature-Timestamp")
    raw_body = await request.body()
    
    if not signature or not timestamp or not verify_signature(
        signature, timestamp, raw_body.decode()
    ):
        raise HTTPException(status_code=401, detail="Invalid signature")
    
    # Handle PING
    if body.type == 1:
        return {"type": 1}
    
    # Convert to our interaction model
    interaction = Interaction(
        id=body.token,
        type=body.type,
        data=body.data or {},
        guild_id=body.guild_id,
        channel_id=body.channel_id,
        member=body.member
    )
    
    try:
        # Get command handler
        command_name = interaction.data.get("name")
        if not command_name:
            return InteractionResponse(
                type=4,
                data={"embeds": [ERROR_EMBED.__dict__]}
            ).__dict__
            
        handler = discord_service.command_handlers.get(command_name)
        if not handler:
            return InteractionResponse(
                type=4,
                data={"embeds": [ERROR_EMBED.__dict__]}
            ).__dict__
            
        # Execute handler
        result = await handler(interaction)
        
        # Convert result to response
        if isinstance(result, str):
            return InteractionResponse(
                type=4,
                data={"content": result}
            ).__dict__
        else:
            return InteractionResponse(
                type=4,
                data={"embeds": [result.__dict__]}
            ).__dict__
            
    except Exception as e:
        discord_service.logger.error(f"Error handling webhook: {e}")
        return InteractionResponse(
            type=4,
            data={"embeds": [ERROR_EMBED.__dict__]}
        ).__dict__

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    status = await discord_service.health_check()
    return {
        "status": status.status,
        "version": status.version,
        "uptime": status.uptime,
        "last_check": status.last_check
    } 