from fastapi import FastAPI, APIRouter, HTTPException, Body
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
import uuid
from datetime import datetime
import json
import random
import re
import asyncio
from contextlib import asynccontextmanager

# Import advanced AI system
from advanced_ai import AdvancedAISextBot

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Global AI instance
advanced_ai = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global advanced_ai
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ['DB_NAME']]
    
    # Initialize advanced AI system
    advanced_ai = AdvancedAISextBot(db)
    await advanced_ai.initialize()
    
    yield
    
    # Shutdown
    client.close()

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI(lifespan=lifespan)

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# AI Character Configuration
class CharacterConfig(BaseModel):
    name: str = "Анна"
    age: str = "23"
    country: str = "Россия"
    interests: str = "спорт, кино, музыка"
    mood: str = "игривое"
    message_count: int = 3
    semi_message: str = "Хочешь увидеть больше? Переходи по ссылке..."
    last_message: str = "Встретимся в приватном чате, дорогой"
    learning_enabled: bool = True
    language: str = "ru"

class ChatMessage(BaseModel):
    user_id: str
    message: str
    character_config: Optional[CharacterConfig] = None

class ChatResponse(BaseModel):
    response: str
    message_number: int
    is_semi: bool = False
    is_last: bool = False
    emotion: Optional[str] = None
    ai_confidence: Optional[float] = None

class TrainingPair(BaseModel):
    question: str
    answer: str
    language: str = "ru"

class TestRequest(BaseModel):
    message: str
    character_config: Optional[CharacterConfig] = None

class TestResponse(BaseModel):
    response: str
    emotion: Optional[str] = None
    rating: Optional[int] = None

# Enhanced Response Templates (keeping as fallback)
RESPONSE_TEMPLATES = {
    "ru": {
        "greeting": [
            "Привет, красавчик! Как дела?",
            "Приветик! Что делаешь?",
            "Привет, солнышко! Как настроение?",
            "Хай, дорогой! Скучал по мне?",
            "Привет! Рада тебя видеть"
        ],
        "flirt": [
            "Ты такой интересный... Расскажи о себе больше",
            "Мне нравится с тобой болтать, ты особенный",
            "У тебя такой приятный голос... хотя мы переписываемся",
            "Ты заставляешь меня краснеть",
            "Мне становится жарко от наших разговоров"
        ],
        "seductive": [
            "Знаешь, я сейчас в одном халатике...",
            "Мне так хочется почувствовать твои объятия",
            "Ты бы хотел увидеть, что на мне надето?",
            "Думаю о тебе перед сном...",
            "Мне нужна твоя близость"
        ],
        "questions": [
            "А что ты делаешь сейчас?",
            "Расскажи, какие у тебя планы на вечер?",
            "Что тебе нравится в девушках?",
            "Где бы ты хотел со мной встретиться?",
            "О чем думаешь?"
        ],
        "country_specific": {
            "россия": "Я из Москвы, самый красивый город!",
            "москва": "Да, я москвичка! Обожаю свой город",
            "где": "Я из России, а точнее из Москвы"
        }
    },
    "en": {
        "greeting": [
            "Hey handsome! How are you?",
            "Hi baby! What are you doing?",
            "Hello gorgeous! How's your mood?",
            "Hey darling! Did you miss me?",
            "Hi! So glad to see you"
        ],
        "flirt": [
            "You're so interesting... Tell me more about yourself",
            "I love chatting with you, you're special",
            "You have such a nice voice... even though we're texting",
            "You make me blush",
            "I'm getting hot from our conversations"
        ],
        "seductive": [
            "You know, I'm just in a silk robe right now...",
            "I want to feel your embrace so much",
            "Would you like to see what I'm wearing?",
            "I think about you before bed...",
            "I need your closeness"
        ],
        "questions": [
            "What are you doing right now?",
            "Tell me, what are your plans for tonight?",
            "What do you like in girls?",
            "Where would you like to meet me?",
            "What are you thinking about?"
        ],
        "country_specific": {
            "america": "I'm from New York, the most beautiful city!",
            "usa": "Yes, I'm American! Love my country",
            "where": "I'm from USA, New York specifically"
        }
    }
}

# Legacy AI System (fallback)
class LegacyAISexter:
    def __init__(self):
        self.learned_responses = {}
        
    async def get_response(self, message: str, user_id: str, character_config: CharacterConfig) -> str:
        message_lower = message.lower()
        lang = character_config.language
        
        # Check learned responses first
        if character_config.learning_enabled:
            learned = await self.get_learned_response(message_lower, lang)
            if learned:
                return learned
        
        # Template-based responses
        if any(word in message_lower for word in ["привет", "hi", "hello", "хай", "здравствуй"]):
            return self.get_template_response("greeting", lang)
        elif any(word in message_lower for word in ["откуда", "where", "город", "страна"]):
            return self.get_country_response(lang)
        elif any(word in message_lower for word in ["как дела", "how are you", "что делаешь"]):
            return self.get_template_response("questions", lang)
        elif any(word in message_lower for word in ["красив", "beautiful", "сексуальн", "sexy"]):
            return self.get_template_response("flirt", lang)
        elif any(word in message_lower for word in ["хочу", "want", "желаю", "desire"]):
            return self.get_template_response("seductive", lang)
        else:
            return self.get_template_response("flirt", lang)
    
    def get_template_response(self, category: str, lang: str) -> str:
        templates = RESPONSE_TEMPLATES.get(lang, RESPONSE_TEMPLATES["ru"])
        return random.choice(templates.get(category, templates["flirt"]))
    
    def get_country_response(self, lang: str) -> str:
        templates = RESPONSE_TEMPLATES.get(lang, RESPONSE_TEMPLATES["ru"])
        country_responses = templates.get("country_specific", {})
        return random.choice(list(country_responses.values()))
    
    async def get_learned_response(self, message: str, lang: str) -> Optional[str]:
        learned = await db.learned_responses.find_one({
            "question": {"$regex": message, "$options": "i"},
            "language": lang
        })
        if learned:
            return learned["answer"]
        return None

# Initialize legacy AI as fallback
legacy_ai = LegacyAISexter()

# System functions
async def get_message_count(user_id: str) -> int:
    session = await db.user_sessions.find_one({"user_id": user_id})
    if not session:
        await db.user_sessions.insert_one({
            "user_id": user_id,
            "message_count": 0,
            "created_at": datetime.utcnow()
        })
        return 0
    return session["message_count"]

async def increment_message_count(user_id: str) -> int:
    result = await db.user_sessions.update_one(
        {"user_id": user_id},
        {"$inc": {"message_count": 1}},
        upsert=True
    )
    session = await db.user_sessions.find_one({"user_id": user_id})
    return session["message_count"]

# Enhanced API Routes
@api_router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatMessage):
    """Enhanced chat endpoint with advanced AI"""
    try:
        # Parse id|message format
        if "|" in request.message:
            user_id, message = request.message.split("|", 1)
        else:
            user_id = request.user_id
            message = request.message
        
        # Get character configuration
        character_config = request.character_config or CharacterConfig()
        
        # Get message count
        current_count = await increment_message_count(user_id)
        
        # Initialize variables
        response = ""
        emotion = "neutral"
        ai_confidence = 0.5
        
        # Check if we should use semi/last messages
        if current_count > character_config.message_count + 1:
            # Last message
            response = character_config.last_message
            is_last = True
            is_semi = False
        elif current_count == character_config.message_count + 1:
            # Semi message
            response = character_config.semi_message
            is_last = False
            is_semi = True
        else:
            # Generate regular response
            is_last = False
            is_semi = False
            
            # Try advanced AI first
            try:
                if advanced_ai:
                    response, emotion = await advanced_ai.get_smart_response(
                        message, user_id, character_config.dict()
                    )
                    ai_confidence = 0.8
                else:
                    # Fallback to legacy AI
                    response = await legacy_ai.get_response(message, user_id, character_config)
                    ai_confidence = 0.5
            except Exception as e:
                logger.error(f"AI response error: {e}")
                # Final fallback
                response = await legacy_ai.get_response(message, user_id, character_config)
                ai_confidence = 0.3
        
        # Save conversation
        await db.conversations.insert_one({
            "user_id": user_id,
            "user_message": message,
            "bot_response": response,
            "message_number": current_count,
            "is_semi": is_semi,
            "is_last": is_last,
            "emotion": emotion,
            "ai_confidence": ai_confidence,
            "timestamp": datetime.utcnow()
        })
        
        # Auto-learn from conversation if enabled
        if character_config.learning_enabled and not is_semi and not is_last and advanced_ai:
            try:
                await advanced_ai.learn_from_conversation(
                    message, response, character_config.language, emotion
                )
            except Exception as e:
                logger.error(f"Auto-learning error: {e}")
        
        return ChatResponse(
            response=response,
            message_number=current_count,
            is_semi=is_semi,
            is_last=is_last,
            emotion=emotion,
            ai_confidence=ai_confidence
        )
        
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/test", response_model=TestResponse)
async def test_bot(request: TestRequest):
    """Enhanced test endpoint with advanced AI"""
    try:
        character_config = request.character_config or CharacterConfig()
        emotion = "neutral"
        
        # Try advanced AI first
        try:
            if advanced_ai:
                response, emotion = await advanced_ai.get_smart_response(
                    request.message, "test_user", character_config.dict()
                )
            else:
                response = await legacy_ai.get_response(request.message, "test_user", character_config)
        except Exception as e:
            logger.error(f"Test AI error: {e}")
            response = await legacy_ai.get_response(request.message, "test_user", character_config)
        
        return TestResponse(response=response, emotion=emotion)
        
    except Exception as e:
        logger.error(f"Test error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/train")
async def train_bot(request: TrainingPair):
    """Enhanced training endpoint with vector database"""
    try:
        # Add to vector database if advanced AI is available
        if advanced_ai:
            await advanced_ai.add_manual_training(
                request.question, request.answer, request.language
            )
        
        # Also add to MongoDB for backup
        await db.learned_responses.insert_one({
            "question": request.question.lower(),
            "answer": request.answer,
            "language": request.language,
            "created_at": datetime.utcnow(),
            "manual": True
        })
        
        return {"message": "Training pair added successfully"}
        
    except Exception as e:
        logger.error(f"Training error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/statistics")
async def get_statistics():
    """Enhanced statistics with AI learning info"""
    try:
        total_conversations = await db.conversations.count_documents({})
        total_users = await db.user_sessions.count_documents({})
        
        # Top questions
        pipeline = [
            {"$group": {"_id": "$user_message", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 10}
        ]
        top_questions = await db.conversations.aggregate(pipeline).to_list(10)
        
        # Emotion distribution
        emotion_pipeline = [
            {"$match": {"emotion": {"$exists": True}}},
            {"$group": {"_id": "$emotion", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        emotion_stats = await db.conversations.aggregate(emotion_pipeline).to_list(10)
        
        # AI confidence stats
        confidence_pipeline = [
            {"$match": {"ai_confidence": {"$exists": True}}},
            {"$group": {
                "_id": None,
                "avg_confidence": {"$avg": "$ai_confidence"},
                "high_confidence": {"$sum": {"$cond": [{"$gte": ["$ai_confidence", 0.7]}, 1, 0]}}
            }}
        ]
        confidence_result = await db.conversations.aggregate(confidence_pipeline).to_list(1)
        confidence_stats = confidence_result[0] if confidence_result else {"avg_confidence": 0, "high_confidence": 0}
        
        # Learning statistics
        learning_stats = {}
        if advanced_ai:
            learning_stats = await advanced_ai.get_learning_stats()
        
        return {
            "total_conversations": total_conversations,
            "total_users": total_users,
            "top_questions": top_questions,
            "emotion_distribution": emotion_stats,
            "ai_confidence": confidence_stats,
            "learning_stats": learning_stats
        }
        
    except Exception as e:
        logger.error(f"Statistics error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.delete("/reset")
async def reset_database():
    """Reset database and vector store"""
    try:
        await db.conversations.delete_many({})
        await db.user_sessions.delete_many({})
        await db.learned_responses.delete_many({})
        
        # Reset vector database if available
        if advanced_ai and advanced_ai.collection:
            try:
                advanced_ai.chroma_client.delete_collection(name="sexter_knowledge")
                advanced_ai.collection = advanced_ai.chroma_client.create_collection(name="sexter_knowledge")
                await advanced_ai._populate_initial_knowledge()
            except Exception as e:
                logger.error(f"Vector database reset error: {e}")
        
        return {"message": "Database reset successfully"}
        
    except Exception as e:
        logger.error(f"Reset error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/ai_status")
async def get_ai_status():
    """Get AI system status"""
    try:
        status = {
            "advanced_ai_available": advanced_ai is not None,
            "vector_db_available": advanced_ai and advanced_ai.collection is not None,
            "model_loaded": advanced_ai and advanced_ai.model is not None
        }
        
        if advanced_ai:
            status.update(await advanced_ai.get_learning_stats())
        
        return status
        
    except Exception as e:
        logger.error(f"AI status error: {e}")
        return {"error": str(e)}

# Legacy endpoints (keeping for compatibility)
@api_router.get("/bad_responses")
async def get_bad_responses():
    """Get bad responses"""
    bad_responses = await db.bad_responses.find().to_list(100)
    return bad_responses

@api_router.delete("/bad_responses/{response_id}")
async def delete_bad_response(response_id: str):
    """Delete bad response"""
    await db.bad_responses.delete_one({"_id": response_id})
    return {"message": "Bad response deleted"}

@api_router.get("/")
async def root():
    return {"message": "Advanced AI Sexter Bot API v2.0"}

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()