#!/usr/bin/env python3
"""
AI Sexter Bot Backend API Testing
Tests all endpoints and functionality of the sexter bot system
"""

import requests
import json
import sys
from datetime import datetime
import time

class SexterBotAPITester:
    def __init__(self, base_url="https://6d312c9c-1d46-457c-b15c-985814bf6797.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.test_user_id = f"test_user_{datetime.now().strftime('%H%M%S')}"
        self.timeout = 30  # Increased timeout

    def log_test(self, name, success, details=""):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED")
        else:
            print(f"❌ {name} - FAILED: {details}")
        
        if details:
            print(f"   Details: {details}")

    def test_api_root(self):
        """Test basic API connectivity"""
        try:
            response = requests.get(f"{self.api_url}/", timeout=self.timeout)
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            if success:
                data = response.json()
                details += f", Response: {data.get('message', 'No message')}"
            self.log_test("API Root Connectivity", success, details)
            return success
        except Exception as e:
            self.log_test("API Root Connectivity", False, str(e))
            return False

    def test_chat_basic(self):
        """Test basic chat functionality"""
        try:
            payload = {
                "user_id": self.test_user_id,
                "message": "Привет"
            }
            response = requests.post(f"{self.api_url}/chat", json=payload, timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                required_fields = ["response", "message_number", "is_semi", "is_last"]
                missing_fields = [field for field in required_fields if field not in data]
                if missing_fields:
                    success = False
                    details = f"Missing fields: {missing_fields}"
                else:
                    details = f"Response: '{data['response'][:50]}...', Message #: {data['message_number']}"
            else:
                details = f"Status: {response.status_code}, Error: {response.text}"
                
            self.log_test("Basic Chat", success, details)
            return success, response.json() if success else {}
        except Exception as e:
            self.log_test("Basic Chat", False, str(e))
            return False, {}

    def test_chat_id_format(self):
        """Test chat with id|message format"""
        try:
            payload = {
                "user_id": "dummy",  # Should be ignored
                "message": f"{self.test_user_id}_format|Как дела?"
            }
            response = requests.post(f"{self.api_url}/chat", json=payload, timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                details = f"Response: '{data['response'][:50]}...', Message #: {data['message_number']}"
            else:
                details = f"Status: {response.status_code}"
                
            self.log_test("Chat ID|Message Format", success, details)
            return success
        except Exception as e:
            self.log_test("Chat ID|Message Format", False, str(e))
            return False

    def test_message_counting_system(self):
        """Test message counting and semi/last message system"""
        try:
            # Create character config with low message count for testing
            character_config = {
                "name": "Тест",
                "age": "25",
                "country": "Россия",
                "interests": "тестирование",
                "mood": "тестовое",
                "message_count": 2,  # Low count for quick testing
                "semi_message": "Это semi сообщение для теста",
                "last_message": "Это last сообщение для теста",
                "learning_enabled": True,
                "language": "ru"
            }
            
            test_user = f"{self.test_user_id}_counting"
            responses = []
            
            # Send messages to trigger semi and last
            for i in range(5):
                payload = {
                    "user_id": test_user,
                    "message": f"Сообщение {i+1}",
                    "character_config": character_config
                }
                response = requests.post(f"{self.api_url}/chat", json=payload, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    responses.append({
                        "message_number": data["message_number"],
                        "is_semi": data["is_semi"],
                        "is_last": data["is_last"],
                        "response": data["response"]
                    })
                else:
                    self.log_test("Message Counting System", False, f"Request {i+1} failed")
                    return False
            
            # Analyze responses
            semi_found = any(r["is_semi"] for r in responses)
            last_found = any(r["is_last"] for r in responses)
            
            success = semi_found and last_found
            details = f"Semi found: {semi_found}, Last found: {last_found}"
            if success:
                semi_msg = next(r for r in responses if r["is_semi"])
                last_msg = next(r for r in responses if r["is_last"])
                details += f", Semi at msg #{semi_msg['message_number']}, Last at msg #{last_msg['message_number']}"
            
            self.log_test("Message Counting System", success, details)
            return success
        except Exception as e:
            self.log_test("Message Counting System", False, str(e))
            return False

    def test_bot_testing_endpoint(self):
        """Test the /test endpoint"""
        try:
            payload = {
                "message": "Привет, как дела?",
                "character_config": {
                    "name": "Анна",
                    "language": "ru"
                }
            }
            response = requests.post(f"{self.api_url}/test", json=payload, timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                has_response = "response" in data and len(data["response"]) > 0
                success = has_response
                details = f"Response: '{data.get('response', 'No response')[:50]}...'"
            else:
                details = f"Status: {response.status_code}"
                
            self.log_test("Bot Testing Endpoint", success, details)
            return success
        except Exception as e:
            self.log_test("Bot Testing Endpoint", False, str(e))
            return False

    def test_training_endpoint(self):
        """Test manual training functionality"""
        try:
            payload = {
                "question": "тестовый вопрос",
                "answer": "тестовый ответ",
                "language": "ru"
            }
            response = requests.post(f"{self.api_url}/train", json=payload, timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                details = f"Message: {data.get('message', 'No message')}"
            else:
                details = f"Status: {response.status_code}"
                
            self.log_test("Training Endpoint", success, details)
            return success
        except Exception as e:
            self.log_test("Training Endpoint", False, str(e))
            return False

    def test_statistics_endpoint(self):
        """Test statistics endpoint"""
        try:
            response = requests.get(f"{self.api_url}/statistics", timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                required_fields = ["total_conversations", "total_users", "top_questions"]
                missing_fields = [field for field in required_fields if field not in data]
                if missing_fields:
                    success = False
                    details = f"Missing fields: {missing_fields}"
                else:
                    details = f"Conversations: {data['total_conversations']}, Users: {data['total_users']}"
            else:
                details = f"Status: {response.status_code}"
                
            self.log_test("Statistics Endpoint", success, details)
            return success
        except Exception as e:
            self.log_test("Statistics Endpoint", False, str(e))
            return False

    def test_bad_responses_endpoint(self):
        """Test bad responses endpoint"""
        try:
            response = requests.get(f"{self.api_url}/bad_responses", timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                details = f"Bad responses count: {len(data)}"
            else:
                details = f"Status: {response.status_code}"
                
            self.log_test("Bad Responses Endpoint", success, details)
            return success
        except Exception as e:
            self.log_test("Bad Responses Endpoint", False, str(e))
            return False

    def test_language_support(self):
        """Test Russian and English language support"""
        try:
            # Test Russian
            ru_payload = {
                "user_id": f"{self.test_user_id}_ru",
                "message": "Привет, красавица",
                "character_config": {"language": "ru"}
            }
            ru_response = requests.post(f"{self.api_url}/chat", json=ru_payload, timeout=10)
            
            # Test English
            en_payload = {
                "user_id": f"{self.test_user_id}_en",
                "message": "Hello beautiful",
                "character_config": {"language": "en"}
            }
            en_response = requests.post(f"{self.api_url}/chat", json=en_payload, timeout=10)
            
            ru_success = ru_response.status_code == 200
            en_success = en_response.status_code == 200
            success = ru_success and en_success
            
            details = f"Russian: {ru_success}, English: {en_success}"
            if success:
                ru_data = ru_response.json()
                en_data = en_response.json()
                details += f", RU response: '{ru_data['response'][:30]}...', EN response: '{en_data['response'][:30]}...'"
            
            self.log_test("Language Support", success, details)
            return success
        except Exception as e:
            self.log_test("Language Support", False, str(e))
            return False

    def test_flirting_responses(self):
        """Test that bot generates flirting responses"""
        try:
            flirt_messages = [
                "Ты красивая",
                "Хочу тебя",
                "Ты сексуальная",
                "Как дела, красотка?"
            ]
            
            flirt_responses = []
            for msg in flirt_messages:
                payload = {
                    "user_id": f"{self.test_user_id}_flirt",
                    "message": msg
                }
                response = requests.post(f"{self.api_url}/chat", json=payload, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    flirt_responses.append(data["response"])
                else:
                    self.log_test("Flirting Responses", False, f"Failed to get response for: {msg}")
                    return False
            
            # Check if responses seem flirtatious (basic check)
            flirt_keywords = ["красив", "интересн", "особенн", "нравится", "жарко", "близост", "объятия"]
            flirty_count = sum(1 for response in flirt_responses 
                             if any(keyword in response.lower() for keyword in flirt_keywords))
            
            success = flirty_count > 0
            details = f"Flirty responses: {flirty_count}/{len(flirt_responses)}"
            if success:
                details += f", Sample: '{flirt_responses[0][:50]}...'"
            
            self.log_test("Flirting Responses", success, details)
            return success
        except Exception as e:
            self.log_test("Flirting Responses", False, str(e))
            return False

    def run_all_tests(self):
        """Run all backend tests"""
        print("🚀 Starting AI Sexter Bot Backend API Tests")
        print(f"🔗 Testing API at: {self.api_url}")
        print("=" * 60)
        
        # Basic connectivity
        if not self.test_api_root():
            print("❌ API is not accessible, stopping tests")
            return False
        
        # Core functionality tests
        self.test_chat_basic()
        self.test_chat_id_format()
        self.test_message_counting_system()
        self.test_bot_testing_endpoint()
        self.test_training_endpoint()
        self.test_statistics_endpoint()
        self.test_bad_responses_endpoint()
        
        # Sexter-specific tests
        self.test_language_support()
        self.test_flirting_responses()
        
        # Print summary
        print("=" * 60)
        print(f"📊 Test Results: {self.tests_passed}/{self.tests_run} tests passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All tests passed!")
            return True
        else:
            print(f"⚠️  {self.tests_run - self.tests_passed} tests failed")
            return False

def main():
    """Main test execution"""
    tester = SexterBotAPITester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())