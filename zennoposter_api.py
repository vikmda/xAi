"""
ZennoPoster API Integration for AI Sexter Bot
Optimized for POST requests from external tools
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
import json
import logging
from datetime import datetime
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from advanced_ai import AdvancedAISextBot

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ZennoPoster specific models
class ZennoMessage(BaseModel):
    message: str  # Format: "user123|Привет красотка"
    character_name: Optional[str] = "Анна"
    language: Optional[str] = "ru"  # ru/en
    country: Optional[str] = "россия"  # россия/usa

class ZennoResponse(BaseModel):
    response: str
    user_id: str
    message_number: int
    emotion: str
    is_redirect: bool = False
    redirect_type: Optional[str] = None  # semi/last
    ai_confidence: float

class ZennoStats(BaseModel):
    total_users: int
    active_conversations: int
    redirect_rate: float
    avg_messages_per_user: float
    top_emotions: list

class ZennoPosterAPI:
    def __init__(self, mongo_db, advanced_ai):
        self.db = mongo_db
        self.ai = advanced_ai
        self.active_sessions = {}
        
    async def process_message(self, message_data: ZennoMessage) -> ZennoResponse:
        """Process message from ZennoPoster"""
        try:
            # Parse user_id and message
            if "|" in message_data.message:
                user_id, user_message = message_data.message.split("|", 1)
            else:
                # If no ID provided, generate one
                user_id = f"zenno_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                user_message = message_data.message
            
            # Get user session
            session = await self._get_or_create_session(user_id, message_data)
            
            # Check if should redirect
            if session['message_count'] >= session['max_messages']:
                return await self._handle_redirect(user_id, session, user_message)
            
            # Generate AI response
            character_config = self._build_character_config(message_data, session)
            
            if self.ai:
                response, emotion = await self.ai.get_smart_response(
                    user_message, user_id, character_config
                )
                ai_confidence = 0.8
            else:
                response, emotion, ai_confidence = await self._fallback_response(
                    user_message, character_config
                )
            
            # Update session
            session['message_count'] += 1
            session['last_message'] = user_message
            session['last_response'] = response
            session['last_emotion'] = emotion
            session['updated_at'] = datetime.utcnow()
            
            await self._update_session(user_id, session)
            
            # Log conversation
            await self._log_conversation(user_id, user_message, response, emotion, session)
            
            return ZennoResponse(
                response=response,
                user_id=user_id,
                message_number=session['message_count'],
                emotion=emotion,
                is_redirect=False,
                ai_confidence=ai_confidence
            )
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return ZennoResponse(
                response="Извини, произошла ошибка. Попробуй еще раз.",
                user_id=user_id if 'user_id' in locals() else "unknown",
                message_number=1,
                emotion="neutral",
                is_redirect=False,
                ai_confidence=0.1
            )
    
    async def _get_or_create_session(self, user_id: str, message_data: ZennoMessage) -> Dict:
        """Get or create user session"""
        session = await self.db.zenno_sessions.find_one({"user_id": user_id})
        
        if not session:
            # Create new session
            session = {
                "user_id": user_id,
                "message_count": 0,
                "max_messages": 3,  # Default, can be configured
                "character_name": message_data.character_name,
                "language": message_data.language,
                "country": message_data.country,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "stage": "beginning",
                "emotions_history": [],
                "semi_message": "Хочешь увидеть больше? Переходи по ссылке: https://example.com/more" if message_data.language == "ru" else "Want to see more? Follow the link: https://example.com/more",
                "last_message": "Встретимся в приватном чате, жду тебя: https://example.com/private" if message_data.language == "ru" else "Meet me in private chat, waiting for you: https://example.com/private"
            }
            
            await self.db.zenno_sessions.insert_one(session)
        
        return session
    
    async def _handle_redirect(self, user_id: str, session: Dict, user_message: str) -> ZennoResponse:
        """Handle redirect logic (semi/last messages)"""
        message_count = session['message_count']
        max_messages = session['max_messages']
        
        if message_count == max_messages:
            # Semi message
            response = session['semi_message']
            redirect_type = "semi"
            session['message_count'] += 1
            await self._update_session(user_id, session)
            
        else:
            # Last message
            response = session['last_message']
            redirect_type = "last"
        
        # Log redirect
        await self._log_conversation(user_id, user_message, response, "redirect", session)
        
        return ZennoResponse(
            response=response,
            user_id=user_id,
            message_number=message_count + 1,
            emotion="redirect",
            is_redirect=True,
            redirect_type=redirect_type,
            ai_confidence=1.0
        )
    
    def _build_character_config(self, message_data: ZennoMessage, session: Dict) -> Dict:
        """Build character configuration"""
        return {
            "name": message_data.character_name,
            "age": "23",
            "country": "Россия" if message_data.language == "ru" else "США",
            "interests": "флирт, общение, романтика",
            "mood": "игривое",
            "message_count": session['max_messages'],
            "semi_message": session['semi_message'],
            "last_message": session['last_message'],
            "learning_enabled": True,
            "language": message_data.language
        }
    
    async def _fallback_response(self, message: str, character_config: Dict) -> tuple:
        """Fallback response when AI is not available"""
        lang = character_config.get("language", "ru")
        message_lower = message.lower()
        
        if lang == "ru":
            if any(word in message_lower for word in ["привет", "здравствуй", "хай"]):
                response = "Привет дорогой! Как дела?"
                emotion = "flirty"
            elif any(word in message_lower for word in ["как дела", "что делаешь"]):
                response = "Думаю о тебе, красавчик"
                emotion = "romantic"
            elif any(word in message_lower for word in ["красив", "сексуальн"]):
                response = "Ты заставляешь меня краснеть"
                emotion = "flirty"
            elif any(word in message_lower for word in ["хочу", "желаю"]):
                response = "Мм, мне тоже хочется близости"
                emotion = "seductive"
            else:
                response = "Ты такой интересный, расскажи мне больше"
                emotion = "neutral"
        else:
            if any(word in message_lower for word in ["hello", "hi", "hey"]):
                response = "Hi handsome! How are you?"
                emotion = "flirty"
            elif any(word in message_lower for word in ["how are you", "what are you doing"]):
                response = "Thinking about you, gorgeous"
                emotion = "romantic"
            elif any(word in message_lower for word in ["beautiful", "sexy"]):
                response = "You make me blush"
                emotion = "flirty"
            elif any(word in message_lower for word in ["want", "desire"]):
                response = "Mmm, I want closeness too"
                emotion = "seductive"
            else:
                response = "You're so interesting, tell me more"
                emotion = "neutral"
        
        return response, emotion, 0.5
    
    async def _update_session(self, user_id: str, session: Dict):
        """Update user session"""
        await self.db.zenno_sessions.update_one(
            {"user_id": user_id},
            {"$set": session}
        )
    
    async def _log_conversation(self, user_id: str, user_message: str, response: str, emotion: str, session: Dict):
        """Log conversation for analytics"""
        await self.db.zenno_conversations.insert_one({
            "user_id": user_id,
            "user_message": user_message,
            "bot_response": response,
            "emotion": emotion,
            "message_number": session['message_count'],
            "session_stage": session.get('stage', 'unknown'),
            "language": session.get('language', 'ru'),
            "timestamp": datetime.utcnow()
        })
    
    async def get_stats(self) -> ZennoStats:
        """Get ZennoPoster statistics"""
        try:
            # Total users
            total_users = await self.db.zenno_sessions.count_documents({})
            
            # Active conversations (last 24 hours)
            yesterday = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            active_conversations = await self.db.zenno_conversations.count_documents({
                "timestamp": {"$gte": yesterday}
            })
            
            # Redirect rate
            total_messages = await self.db.zenno_conversations.count_documents({})
            redirect_messages = await self.db.zenno_conversations.count_documents({
                "emotion": "redirect"
            })
            redirect_rate = (redirect_messages / total_messages * 100) if total_messages > 0 else 0
            
            # Average messages per user
            avg_messages = await self.db.zenno_conversations.aggregate([
                {"$group": {"_id": "$user_id", "count": {"$sum": 1}}},
                {"$group": {"_id": None, "avg": {"$avg": "$count"}}}
            ]).to_list(1)
            avg_messages_per_user = avg_messages[0]["avg"] if avg_messages else 0
            
            # Top emotions
            top_emotions = await self.db.zenno_conversations.aggregate([
                {"$group": {"_id": "$emotion", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}},
                {"$limit": 5}
            ]).to_list(5)
            
            return ZennoStats(
                total_users=total_users,
                active_conversations=active_conversations,
                redirect_rate=redirect_rate,
                avg_messages_per_user=avg_messages_per_user,
                top_emotions=top_emotions
            )
            
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return ZennoStats(
                total_users=0,
                active_conversations=0,
                redirect_rate=0,
                avg_messages_per_user=0,
                top_emotions=[]
            )
    
    async def configure_session(self, user_id: str, config: Dict):
        """Configure specific session parameters"""
        await self.db.zenno_sessions.update_one(
            {"user_id": user_id},
            {"$set": {
                "max_messages": config.get("max_messages", 3),
                "semi_message": config.get("semi_message", ""),
                "last_message": config.get("last_message", ""),
                "character_name": config.get("character_name", "Анна"),
                "language": config.get("language", "ru")
            }},
            upsert=True
        )
    
    async def reset_session(self, user_id: str):
        """Reset specific user session"""
        await self.db.zenno_sessions.delete_one({"user_id": user_id})
        await self.db.zenno_conversations.delete_many({"user_id": user_id})