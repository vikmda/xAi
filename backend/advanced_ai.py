"""
Advanced AI System with RAG and Vector Database
"""
import chromadb
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import re
import asyncio
from typing import List, Dict, Optional, Tuple
import logging
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
import json
import random

logger = logging.getLogger(__name__)

class AdvancedAISextBot:
    def __init__(self, mongo_db):
        self.db = mongo_db
        self.model = None
        self.chroma_client = None
        self.collection = None
        self.conversation_contexts = {}
        self.emotion_keywords = {
            "flirty": ["красивый", "сексуальный", "привлекательный", "милый", "handsome", "sexy", "attractive", "cute"],
            "romantic": ["любовь", "сердце", "романтика", "love", "heart", "romance", "romantic"],
            "playful": ["игра", "шутка", "веселье", "play", "joke", "fun", "playful"],
            "seductive": ["хочу", "желаю", "страсть", "want", "desire", "passion", "seductive"],
            "intimate": ["близость", "объятия", "поцелуи", "intimacy", "hug", "kiss", "close"]
        }
        
    async def initialize(self):
        """Initialize the advanced AI system"""
        try:
            # Initialize sentence transformer model
            logger.info("Loading sentence transformer model...")
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
            
            # Initialize ChromaDB
            logger.info("Initializing ChromaDB...")
            self.chroma_client = chromadb.Client()
            
            # Create or get collection
            try:
                self.collection = self.chroma_client.get_collection(name="sexter_knowledge")
            except:
                self.collection = self.chroma_client.create_collection(name="sexter_knowledge")
                await self._populate_initial_knowledge()
            
            logger.info("Advanced AI system initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize advanced AI: {e}")
            raise
    
    async def _populate_initial_knowledge(self):
        """Populate the vector database with initial knowledge"""
        initial_knowledge = [
            # Русские фразы
            {"text": "Привет как дела", "response": "Привет дорогой! У меня все отлично, особенно когда вижу тебя", "emotion": "flirty", "lang": "ru"},
            {"text": "Что делаешь", "response": "Думаю о тебе и наших встречах", "emotion": "romantic", "lang": "ru"},
            {"text": "Откуда ты", "response": "Я из Москвы, самый красивый город для самой красивой девушки", "emotion": "flirty", "lang": "ru"},
            {"text": "Как тебя зовут", "response": "Меня зовут Анна, а как мне тебя называть, красавчик?", "emotion": "flirty", "lang": "ru"},
            {"text": "Сколько тебе лет", "response": "Мне 23, самый расцвет для девушки, не правда ли?", "emotion": "flirty", "lang": "ru"},
            {"text": "Что любишь", "response": "Люблю страсть, романтику и интересных мужчин как ты", "emotion": "seductive", "lang": "ru"},
            {"text": "Хочу тебя", "response": "Мм, мне тоже хочется близости с тобой", "emotion": "seductive", "lang": "ru"},
            {"text": "Встретимся", "response": "Было бы замечательно, где бы ты хотел встретиться?", "emotion": "romantic", "lang": "ru"},
            {"text": "Что на тебе", "response": "Сейчас на мне шелковое белье... думаю, тебе понравилось бы", "emotion": "seductive", "lang": "ru"},
            {"text": "Скучаю", "response": "Я тоже скучаю по тебе, дорогой", "emotion": "romantic", "lang": "ru"},
            
            # English phrases
            {"text": "Hello how are you", "response": "Hi handsome! I'm doing great, especially when I see you", "emotion": "flirty", "lang": "en"},
            {"text": "What are you doing", "response": "Thinking about you and our meetings", "emotion": "romantic", "lang": "en"},
            {"text": "Where are you from", "response": "I'm from New York, the most beautiful city for the most beautiful girl", "emotion": "flirty", "lang": "en"},
            {"text": "What is your name", "response": "My name is Anna, and how should I call you, handsome?", "emotion": "flirty", "lang": "en"},
            {"text": "How old are you", "response": "I'm 23, the perfect age for a girl, don't you think?", "emotion": "flirty", "lang": "en"},
            {"text": "What do you like", "response": "I love passion, romance and interesting men like you", "emotion": "seductive", "lang": "en"},
            {"text": "I want you", "response": "Mmm, I want closeness with you too", "emotion": "seductive", "lang": "en"},
            {"text": "Let's meet", "response": "That would be wonderful, where would you like to meet?", "emotion": "romantic", "lang": "en"},
            {"text": "What are you wearing", "response": "Right now I'm wearing silk lingerie... I think you'd like it", "emotion": "seductive", "lang": "en"},
            {"text": "I miss you", "response": "I miss you too, darling", "emotion": "romantic", "lang": "en"},
        ]
        
        # Add to vector database
        for i, item in enumerate(initial_knowledge):
            embedding = self.model.encode([item["text"]])
            self.collection.add(
                embeddings=[embedding[0].tolist()],
                documents=[item["text"]],
                metadatas=[{"response": item["response"], "emotion": item["emotion"], "lang": item["lang"]}],
                ids=[f"init_{i}"]
            )
        
        logger.info(f"Populated vector database with {len(initial_knowledge)} initial items")
    
    async def get_smart_response(self, message: str, user_id: str, character_config: dict) -> Tuple[str, str]:
        """Get a smart response using RAG and context awareness"""
        try:
            # Clean and prepare message
            clean_message = self._clean_message(message)
            lang = character_config.get("language", "ru")
            
            # Get user conversation context
            context = await self._get_conversation_context(user_id)
            
            # Detect emotion/intent
            emotion = self._detect_emotion(clean_message)
            
            # Search for similar messages in vector database
            similar_responses = await self._search_similar(clean_message, lang, emotion)
            
            # Generate contextual response
            response = await self._generate_contextual_response(
                clean_message, similar_responses, context, character_config, emotion
            )
            
            # Update conversation context
            await self._update_context(user_id, message, response, emotion)
            
            return response, emotion
            
        except Exception as e:
            logger.error(f"Error in smart response generation: {e}")
            return await self._get_fallback_response(message, character_config), "neutral"
    
    def _clean_message(self, message: str) -> str:
        """Clean and normalize message"""
        # Remove extra spaces and normalize
        message = re.sub(r'\s+', ' ', message.strip().lower())
        # Remove special characters but keep essential punctuation
        message = re.sub(r'[^\w\s\?\!\.\,\-]', '', message)
        return message
    
    def _detect_emotion(self, message: str) -> str:
        """Detect emotion from message"""
        for emotion, keywords in self.emotion_keywords.items():
            if any(keyword in message for keyword in keywords):
                return emotion
        return "neutral"
    
    async def _search_similar(self, message: str, lang: str, emotion: str) -> List[Dict]:
        """Search for similar messages in vector database"""
        try:
            # Create embedding for the message
            embedding = self.model.encode([message])
            
            # Search in ChromaDB
            results = self.collection.query(
                query_embeddings=[embedding[0].tolist()],
                n_results=5,
                where={"lang": lang}
            )
            
            similar_responses = []
            if results["documents"]:
                for i, doc in enumerate(results["documents"][0]):
                    metadata = results["metadatas"][0][i]
                    distance = results["distances"][0][i] if "distances" in results else 0
                    
                    similar_responses.append({
                        "text": doc,
                        "response": metadata["response"],
                        "emotion": metadata["emotion"],
                        "similarity": 1 - distance  # Convert distance to similarity
                    })
            
            return similar_responses
            
        except Exception as e:
            logger.error(f"Error searching similar messages: {e}")
            return []
    
    async def _get_conversation_context(self, user_id: str) -> Dict:
        """Get conversation context for user"""
        try:
            # Get recent conversations from MongoDB
            recent_conversations = await self.db.conversations.find(
                {"user_id": user_id}
            ).sort("timestamp", -1).limit(5).to_list(5)
            
            # Analyze context
            context = {
                "recent_topics": [],
                "emotion_history": [],
                "conversation_stage": "beginning",
                "user_preferences": {}
            }
            
            if recent_conversations:
                for conv in recent_conversations:
                    if "emotion" in conv:
                        context["emotion_history"].append(conv["emotion"])
                    
                    # Simple topic extraction
                    message = conv.get("user_message", "").lower()
                    if "встреч" in message or "meet" in message:
                        context["recent_topics"].append("meeting")
                    elif "фото" in message or "photo" in message:
                        context["recent_topics"].append("photos")
                    elif "видео" in message or "video" in message:
                        context["recent_topics"].append("video")
                
                # Determine conversation stage
                if len(recent_conversations) > 3:
                    context["conversation_stage"] = "advanced"
                elif len(recent_conversations) > 1:
                    context["conversation_stage"] = "developing"
            
            return context
            
        except Exception as e:
            logger.error(f"Error getting conversation context: {e}")
            return {"recent_topics": [], "emotion_history": [], "conversation_stage": "beginning"}
    
    async def _generate_contextual_response(
        self, message: str, similar_responses: List[Dict], context: Dict, 
        character_config: dict, emotion: str
    ) -> str:
        """Generate contextual response based on all available information"""
        
        # Priority 1: Use high-similarity learned responses
        for response in similar_responses:
            if response["similarity"] > 0.8:
                return self._personalize_response(response["response"], character_config, context)
        
        # Priority 2: Generate response based on emotion and context
        if emotion == "seductive" and context["conversation_stage"] == "advanced":
            return await self._generate_seductive_response(message, character_config, context)
        elif emotion == "romantic":
            return await self._generate_romantic_response(message, character_config, context)
        elif emotion == "flirty":
            return await self._generate_flirty_response(message, character_config, context)
        
        # Priority 3: Use best similar response with modifications
        if similar_responses:
            best_response = max(similar_responses, key=lambda x: x["similarity"])
            return self._personalize_response(best_response["response"], character_config, context)
        
        # Priority 4: Generate dynamic response
        return await self._generate_dynamic_response(message, character_config, context, emotion)
    
    async def _generate_seductive_response(self, message: str, character_config: dict, context: Dict) -> str:
        """Generate seductive response"""
        lang = character_config.get("language", "ru")
        name = character_config.get("name", "Анна" if lang == "ru" else "Anna")
        
        if lang == "ru":
            responses = [
                f"Мм, {name} становится возбужденной от твоих слов...",
                f"Ты заставляешь меня краснеть, дорогой",
                f"Я думаю о тебе в самые интимные моменты",
                f"Хочешь узнать, о чем я мечтаю по ночам?",
                f"Твои слова зажигают во мне огонь страсти"
            ]
        else:
            responses = [
                f"Mmm, {name} gets excited from your words...",
                f"You make me blush, darling",
                f"I think about you in the most intimate moments",
                f"Want to know what I dream about at night?",
                f"Your words ignite the fire of passion in me"
            ]
        
        return random.choice(responses)
    
    async def _generate_romantic_response(self, message: str, character_config: dict, context: Dict) -> str:
        """Generate romantic response"""
        lang = character_config.get("language", "ru")
        
        if lang == "ru":
            responses = [
                "Ты такой романтичный... это так привлекательно в мужчине",
                "Мое сердце бьется быстрее когда я читаю твои сообщения",
                "Ты особенный, не такой как все остальные",
                "Мне нравится как ты со мной разговариваешь",
                "Ты заставляешь меня чувствовать себя особенной"
            ]
        else:
            responses = [
                "You're so romantic... it's so attractive in a man",
                "My heart beats faster when I read your messages",
                "You're special, not like all the others",
                "I like how you talk to me",
                "You make me feel special"
            ]
        
        return random.choice(responses)
    
    async def _generate_flirty_response(self, message: str, character_config: dict, context: Dict) -> str:
        """Generate flirty response"""
        lang = character_config.get("language", "ru")
        
        if lang == "ru":
            responses = [
                "Ты такой очаровательный, не могу устоять",
                "Умеешь ли ты флиртовать или это у тебя природный талант?",
                "Мне нравится твоя уверенность",
                "Ты заставляешь меня улыбаться",
                "Какой ты интересный собеседник"
            ]
        else:
            responses = [
                "You're so charming, I can't resist",
                "Do you know how to flirt or is this your natural talent?",
                "I like your confidence",
                "You make me smile",
                "What an interesting conversationalist you are"
            ]
        
        return random.choice(responses)
    
    async def _generate_dynamic_response(self, message: str, character_config: dict, context: Dict, emotion: str) -> str:
        """Generate dynamic response based on context"""
        lang = character_config.get("language", "ru")
        stage = context.get("conversation_stage", "beginning")
        
        # Contextual responses based on conversation stage
        if stage == "advanced":
            if lang == "ru":
                responses = [
                    "Наши разговоры становятся все более интимными...",
                    "Мне нравится как развиваются наши отношения",
                    "Ты уже знаешь, как меня завести",
                    "Каждый раз ты удивляешь меня все больше"
                ]
            else:
                responses = [
                    "Our conversations are getting more intimate...",
                    "I like how our relationship is developing",
                    "You already know how to turn me on",
                    "Each time you surprise me more and more"
                ]
        else:
            if lang == "ru":
                responses = [
                    "Расскажи мне о себе больше, ты такой интересный",
                    "Мне нравится с тобой общаться",
                    "Ты кажешься очень интересным человеком",
                    "Что тебе нравится делать в свободное время?"
                ]
            else:
                responses = [
                    "Tell me more about yourself, you're so interesting",
                    "I like talking with you",
                    "You seem like a very interesting person",
                    "What do you like to do in your free time?"
                ]
        
        return random.choice(responses)
    
    def _personalize_response(self, response: str, character_config: dict, context: Dict) -> str:
        """Personalize response based on character config"""
        name = character_config.get("name", "Анна")
        mood = character_config.get("mood", "игривое")
        
        # Add mood-based modifications
        if "игривое" in mood or "playful" in mood:
            if random.random() < 0.3:  # 30% chance to add playful element
                lang = character_config.get("language", "ru")
                if lang == "ru":
                    response += " 😉"
                else:
                    response += " 😉"
        
        return response
    
    async def _get_fallback_response(self, message: str, character_config: dict) -> str:
        """Get fallback response when other methods fail"""
        lang = character_config.get("language", "ru")
        
        if lang == "ru":
            responses = [
                "Интересно... расскажи мне больше об этом",
                "Ты всегда знаешь, что сказать",
                "Мне нравится наш разговор",
                "Ты заставляешь меня думать",
                "Какой ты загадочный"
            ]
        else:
            responses = [
                "Interesting... tell me more about this",
                "You always know what to say",
                "I like our conversation",
                "You make me think",
                "How mysterious you are"
            ]
        
        return random.choice(responses)
    
    async def _update_context(self, user_id: str, message: str, response: str, emotion: str):
        """Update conversation context"""
        try:
            # Update conversation in database with emotion
            await self.db.conversations.update_one(
                {"user_id": user_id, "user_message": message},
                {"$set": {"emotion": emotion, "ai_confidence": 0.8}},
                upsert=False
            )
            
            # Store in memory context if needed
            if user_id not in self.conversation_contexts:
                self.conversation_contexts[user_id] = {"messages": [], "emotions": []}
            
            self.conversation_contexts[user_id]["messages"].append({
                "user": message,
                "bot": response,
                "emotion": emotion,
                "timestamp": datetime.utcnow()
            })
            
            # Keep only last 10 messages in memory
            if len(self.conversation_contexts[user_id]["messages"]) > 10:
                self.conversation_contexts[user_id]["messages"].pop(0)
            
        except Exception as e:
            logger.error(f"Error updating context: {e}")
    
    async def learn_from_conversation(self, user_message: str, bot_response: str, lang: str, emotion: str = "neutral"):
        """Learn from conversation automatically"""
        try:
            # Clean message
            clean_message = self._clean_message(user_message)
            
            # Create embedding
            embedding = self.model.encode([clean_message])
            
            # Add to vector database
            unique_id = f"learned_{datetime.utcnow().timestamp()}"
            self.collection.add(
                embeddings=[embedding[0].tolist()],
                documents=[clean_message],
                metadatas=[{"response": bot_response, "emotion": emotion, "lang": lang, "learned": True}],
                ids=[unique_id]
            )
            
            # Also store in MongoDB for backup
            await self.db.learned_responses.insert_one({
                "question": clean_message,
                "answer": bot_response,
                "language": lang,
                "emotion": emotion,
                "learned_at": datetime.utcnow(),
                "auto_learned": True
            })
            
            logger.info(f"Learned new response: {clean_message[:50]}...")
            
        except Exception as e:
            logger.error(f"Error learning from conversation: {e}")
    
    async def add_manual_training(self, question: str, answer: str, lang: str):
        """Add manual training data"""
        try:
            # Clean question
            clean_question = self._clean_message(question)
            
            # Create embedding
            embedding = self.model.encode([clean_question])
            
            # Add to vector database
            unique_id = f"manual_{datetime.utcnow().timestamp()}"
            self.collection.add(
                embeddings=[embedding[0].tolist()],
                documents=[clean_question],
                metadatas=[{"response": answer, "emotion": "neutral", "lang": lang, "manual": True}],
                ids=[unique_id]
            )
            
            logger.info(f"Added manual training: {clean_question[:50]}...")
            
        except Exception as e:
            logger.error(f"Error adding manual training: {e}")
    
    async def get_learning_stats(self) -> Dict:
        """Get learning statistics"""
        try:
            # Get collection info
            collection_count = self.collection.count()
            
            # Get MongoDB stats
            auto_learned = await self.db.learned_responses.count_documents({"auto_learned": True})
            manual_learned = await self.db.learned_responses.count_documents({"auto_learned": {"$ne": True}})
            
            return {
                "total_vector_entries": collection_count,
                "auto_learned_responses": auto_learned,
                "manual_learned_responses": manual_learned,
                "total_learned": auto_learned + manual_learned
            }
            
        except Exception as e:
            logger.error(f"Error getting learning stats: {e}")
            return {"error": str(e)}