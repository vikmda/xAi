"""
ZennoPoster Optimized Server
Runs on 192.168.0.16 for network access
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from zennoposter_api import ZennoPosterAPI, ZennoMessage, ZennoResponse, ZennoStats
from advanced_ai import AdvancedAISextBot
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv
import logging
from datetime import datetime
import json
import uvicorn

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('zenno_server.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Global variables
mongo_client = None
db = None
advanced_ai = None
zenno_api = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global mongo_client, db, advanced_ai, zenno_api
    
    try:
        # MongoDB connection
        mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
        mongo_client = AsyncIOMotorClient(mongo_url)
        db = mongo_client[os.environ.get('DB_NAME', 'zenno_sexter')]
        
        # Initialize Advanced AI
        logger.info("Initializing Advanced AI system...")
        advanced_ai = AdvancedAISextBot(db)
        await advanced_ai.initialize()
        
        # Initialize ZennoPoster API
        logger.info("Initializing ZennoPoster API...")
        zenno_api = ZennoPosterAPI(db, advanced_ai)
        
        logger.info("ZennoPoster server started successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize server: {e}")
        # Continue without advanced AI if needed
        advanced_ai = None
        zenno_api = ZennoPosterAPI(db, None)
    
    yield
    
    # Shutdown
    if mongo_client:
        mongo_client.close()
    logger.info("ZennoPoster server shutdown")

# Create FastAPI app
app = FastAPI(
    title="AI Sexter Bot - ZennoPoster API",
    description="Optimized API for ZennoPoster integration",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware for network access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for ZennoPoster
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = datetime.utcnow()
    
    # Log request
    logger.info(f"Request: {request.method} {request.url} from {request.client.host}")
    
    response = await call_next(request)
    
    # Log response
    process_time = (datetime.utcnow() - start_time).total_seconds()
    logger.info(f"Response: {response.status_code} in {process_time:.2f}s")
    
    return response

# Main ZennoPoster endpoints
@app.post("/message", response_model=ZennoResponse)
async def process_message(message: ZennoMessage):
    """
    Main endpoint for ZennoPoster
    Accepts messages in format: user123|Привет красотка
    """
    try:
        if not zenno_api:
            raise HTTPException(status_code=500, detail="ZennoPoster API not initialized")
        
        response = await zenno_api.process_message(message)
        return response
        
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/message/simple")
async def process_simple_message(request: Request):
    """
    Simple endpoint for raw POST requests
    Body: {"message": "user123|Привет красотка"}
    """
    try:
        body = await request.body()
        data = json.loads(body)
        
        message = ZennoMessage(
            message=data.get("message", ""),
            character_name=data.get("character_name", "Анна"),
            language=data.get("language", "ru"),
            country=data.get("country", "россия")
        )
        
        response = await zenno_api.process_message(message)
        
        # Return simple response for ZennoPoster
        return {
            "response": response.response,
            "user_id": response.user_id,
            "is_redirect": response.is_redirect
        }
        
    except Exception as e:
        logger.error(f"Error processing simple message: {e}")
        return {"response": "Извини, произошла ошибка", "error": True}

@app.get("/stats", response_model=ZennoStats)
async def get_stats():
    """Get ZennoPoster statistics"""
    try:
        if not zenno_api:
            raise HTTPException(status_code=500, detail="ZennoPoster API not initialized")
        
        stats = await zenno_api.get_stats()
        return stats
        
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/configure")
async def configure_session(request: Request):
    """
    Configure session parameters
    Body: {"user_id": "user123", "max_messages": 5, "semi_message": "Custom message"}
    """
    try:
        body = await request.body()
        data = json.loads(body)
        
        user_id = data.get("user_id")
        if not user_id:
            raise HTTPException(status_code=400, detail="user_id is required")
        
        config = {
            "max_messages": data.get("max_messages", 3),
            "semi_message": data.get("semi_message", ""),
            "last_message": data.get("last_message", ""),
            "character_name": data.get("character_name", "Анна"),
            "language": data.get("language", "ru")
        }
        
        await zenno_api.configure_session(user_id, config)
        
        return {"message": "Session configured successfully"}
        
    except Exception as e:
        logger.error(f"Error configuring session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/reset/{user_id}")
async def reset_session(user_id: str):
    """Reset specific user session"""
    try:
        await zenno_api.reset_session(user_id)
        return {"message": f"Session {user_id} reset successfully"}
        
    except Exception as e:
        logger.error(f"Error resetting session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "ai_available": advanced_ai is not None,
        "zenno_api_available": zenno_api is not None
    }

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "AI Sexter Bot - ZennoPoster API",
        "version": "1.0.0",
        "endpoints": {
            "POST /message": "Main message processing",
            "POST /message/simple": "Simple message processing",
            "GET /stats": "Get statistics",
            "POST /configure": "Configure session",
            "DELETE /reset/{user_id}": "Reset session",
            "GET /health": "Health check"
        }
    }

if __name__ == "__main__":
    # Run server on specified IP and port
    uvicorn.run(
        "zenno_server:app",
        host="0.0.0.0",  # Listen on all interfaces
        port=8080,       # ZennoPoster port
        reload=False,    # Disable reload for production
        access_log=True,
        log_level="info"
    )