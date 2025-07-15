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

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

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

class TrainingPair(BaseModel):
    question: str
    answer: str
    language: str = "ru"

class TestRequest(BaseModel):
    message: str
    character_config: Optional[CharacterConfig] = None

class TestResponse(BaseModel):
    response: str
    rating: Optional[int] = None

# База шаблонов для ответов
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

# Система обучения и матчинга
class AISexter:
    def __init__(self):
        self.learned_responses = {}
        
    async def get_response(self, message: str, user_id: str, character_config: CharacterConfig) -> str:
        message_lower = message.lower()
        lang = character_config.language
        
        # Проверяем базу обученных ответов
        if character_config.learning_enabled:
            learned = await self.get_learned_response(message_lower, lang)
            if learned:
                return learned
        
        # Определяем тип сообщения и выбираем шаблон
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
            # Базовый флиртующий ответ
            return self.get_template_response("flirt", lang)
    
    def get_template_response(self, category: str, lang: str) -> str:
        templates = RESPONSE_TEMPLATES.get(lang, RESPONSE_TEMPLATES["ru"])
        return random.choice(templates.get(category, templates["flirt"]))
    
    def get_country_response(self, lang: str) -> str:
        templates = RESPONSE_TEMPLATES.get(lang, RESPONSE_TEMPLATES["ru"])
        country_responses = templates.get("country_specific", {})
        return random.choice(list(country_responses.values()))
    
    async def get_learned_response(self, message: str, lang: str) -> Optional[str]:
        # Ищем в базе обученных ответов
        learned = await db.learned_responses.find_one({
            "question": {"$regex": message, "$options": "i"},
            "language": lang
        })
        if learned:
            return learned["answer"]
        return None
    
    async def add_training_pair(self, question: str, answer: str, lang: str):
        await db.learned_responses.insert_one({
            "question": question.lower(),
            "answer": answer,
            "language": lang,
            "created_at": datetime.utcnow()
        })

# Глобальный экземпляр AI
ai_sexter = AISexter()

# Система подсчета сообщений
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

# API Routes
@api_router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatMessage):
    """Основной endpoint для чата"""
    try:
        # Парсим формат id|message
        if "|" in request.message:
            user_id, message = request.message.split("|", 1)
        else:
            user_id = request.user_id
            message = request.message
        
        # Получаем конфигурацию персонажа
        character_config = request.character_config or CharacterConfig()
        
        # Подсчитываем сообщения
        current_count = await increment_message_count(user_id)
        
        # Логика ответов
        if current_count > character_config.message_count + 1:
            # Отправляем last message
            response = character_config.last_message
            is_last = True
            is_semi = False
        elif current_count == character_config.message_count + 1:
            # Отправляем semi message
            response = character_config.semi_message
            is_last = False
            is_semi = True
        else:
            # Генерируем обычный ответ
            response = await ai_sexter.get_response(message, user_id, character_config)
            is_last = False
            is_semi = False
        
        # Сохраняем разговор
        await db.conversations.insert_one({
            "user_id": user_id,
            "user_message": message,
            "bot_response": response,
            "message_number": current_count,
            "is_semi": is_semi,
            "is_last": is_last,
            "timestamp": datetime.utcnow()
        })
        
        # Обучаем систему если включено
        if character_config.learning_enabled and not is_semi and not is_last:
            # Простое обучение на основе контекста
            pass
        
        return ChatResponse(
            response=response,
            message_number=current_count,
            is_semi=is_semi,
            is_last=is_last
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/test", response_model=TestResponse)
async def test_bot(request: TestRequest):
    """Тестирование бота"""
    character_config = request.character_config or CharacterConfig()
    response = await ai_sexter.get_response(request.message, "test_user", character_config)
    return TestResponse(response=response)

@api_router.post("/train")
async def train_bot(request: TrainingPair):
    """Ручное обучение бота"""
    await ai_sexter.add_training_pair(request.question, request.answer, request.language)
    return {"message": "Training pair added successfully"}

@api_router.get("/statistics")
async def get_statistics():
    """Получение статистики"""
    total_conversations = await db.conversations.count_documents({})
    total_users = await db.user_sessions.count_documents({})
    
    # Топ вопросов
    pipeline = [
        {"$group": {"_id": "$user_message", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 10}
    ]
    top_questions = await db.conversations.aggregate(pipeline).to_list(10)
    
    return {
        "total_conversations": total_conversations,
        "total_users": total_users,
        "top_questions": top_questions
    }

@api_router.delete("/reset")
async def reset_database():
    """Сброс базы данных"""
    await db.conversations.delete_many({})
    await db.user_sessions.delete_many({})
    await db.learned_responses.delete_many({})
    return {"message": "Database reset successfully"}

@api_router.get("/bad_responses")
async def get_bad_responses():
    """Получение плохих ответов"""
    bad_responses = await db.bad_responses.find().to_list(100)
    return bad_responses

@api_router.delete("/bad_responses/{response_id}")
async def delete_bad_response(response_id: str):
    """Удаление плохого ответа"""
    await db.bad_responses.delete_one({"_id": response_id})
    return {"message": "Bad response deleted"}

# Старые роуты для совместимости
@api_router.get("/")
async def root():
    return {"message": "AI Sexter Bot API"}

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