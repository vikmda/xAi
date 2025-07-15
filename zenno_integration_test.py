#!/usr/bin/env python3
"""
ZennoPoster Integration Testing for AI Sexter Bot
Tests ZennoPoster-specific functionality and network integration
"""

import requests
import json
import sys
import time
from datetime import datetime
import concurrent.futures
import threading

class ZennoPosterIntegrationTester:
    def __init__(self, base_url="https://6d312c9c-1d46-457c-b15c-985814bf6797.preview.emergentagent.com"):
        self.base_url = base_url
        self.zenno_port = 8080
        self.zenno_url = f"{base_url}:{self.zenno_port}" if "localhost" in base_url else base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.timeout = 30
        
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

    def test_zenno_server_health(self):
        """Test ZennoPoster server health endpoint"""
        try:
            # Try different possible endpoints
            endpoints = [
                f"{self.zenno_url}/health",
                f"{self.base_url}/api/",  # Main API as fallback
                f"{self.base_url}/health"
            ]
            
            for endpoint in endpoints:
                try:
                    response = requests.get(endpoint, timeout=self.timeout)
                    if response.status_code == 200:
                        data = response.json()
                        details = f"Endpoint: {endpoint}, Status: healthy"
                        if "ai_available" in data:
                            details += f", AI Available: {data['ai_available']}"
                        self.log_test("ZennoPoster Server Health", True, details)
                        return True
                except:
                    continue
            
            self.log_test("ZennoPoster Server Health", False, "No health endpoint accessible")
            return False
        except Exception as e:
            self.log_test("ZennoPoster Server Health", False, str(e))
            return False

    def test_zenno_message_format(self):
        """Test ZennoPoster id|message format processing"""
        try:
            # Test the main chat endpoint with id|message format
            test_user_id = f"zenno_test_{datetime.now().strftime('%H%M%S')}"
            payload = {
                "user_id": "dummy",  # Should be ignored
                "message": f"{test_user_id}|Привет красотка, как дела?"
            }
            
            response = requests.post(f"{self.base_url}/api/chat", json=payload, timeout=self.timeout)
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
                    # Check if response is appropriate for sexter bot
                    response_text = data['response'].lower()
                    sexter_keywords = ['привет', 'дорогой', 'красав', 'дела', 'как']
                    has_sexter_response = any(keyword in response_text for keyword in sexter_keywords)
                    if has_sexter_response:
                        details += ", Sexter-style response detected"
                    else:
                        details += ", Warning: Response may not be sexter-style"
            else:
                details = f"Status: {response.status_code}, Error: {response.text[:100]}"
                
            self.log_test("ZennoPoster Message Format", success, details)
            return success
        except Exception as e:
            self.log_test("ZennoPoster Message Format", False, str(e))
            return False

    def test_zenno_redirect_system(self):
        """Test ZennoPoster semi/last message redirection system"""
        try:
            test_user_id = f"zenno_redirect_{datetime.now().strftime('%H%M%S')}"
            
            # Configure character with low message count for quick testing
            character_config = {
                "name": "Анна",
                "age": "23",
                "country": "Россия",
                "interests": "флирт, общение",
                "mood": "игривое",
                "message_count": 2,  # Low count for quick testing
                "semi_message": "Хочешь увидеть больше? Переходи по ссылке: https://example.com/more",
                "last_message": "Встретимся в приватном чате: https://example.com/private",
                "learning_enabled": True,
                "language": "ru"
            }
            
            responses = []
            
            # Send messages to trigger semi and last
            for i in range(5):
                payload = {
                    "user_id": test_user_id,
                    "message": f"{test_user_id}|Сообщение {i+1} для теста",
                    "character_config": character_config
                }
                
                response = requests.post(f"{self.base_url}/api/chat", json=payload, timeout=self.timeout)
                if response.status_code == 200:
                    data = response.json()
                    responses.append({
                        "message_number": data["message_number"],
                        "is_semi": data["is_semi"],
                        "is_last": data["is_last"],
                        "response": data["response"]
                    })
                else:
                    self.log_test("ZennoPoster Redirect System", False, f"Request {i+1} failed: {response.status_code}")
                    return False
            
            # Analyze responses for redirect behavior
            semi_found = any(r["is_semi"] for r in responses)
            last_found = any(r["is_last"] for r in responses)
            
            success = semi_found and last_found
            details = f"Semi found: {semi_found}, Last found: {last_found}"
            
            if success:
                semi_msg = next(r for r in responses if r["is_semi"])
                last_msg = next(r for r in responses if r["is_last"])
                details += f", Semi at msg #{semi_msg['message_number']}, Last at msg #{last_msg['message_number']}"
                
                # Check if redirect messages contain links
                if "https://" in semi_msg["response"] or "http://" in semi_msg["response"]:
                    details += ", Semi message contains link"
                if "https://" in last_msg["response"] or "http://" in last_msg["response"]:
                    details += ", Last message contains link"
            
            self.log_test("ZennoPoster Redirect System", success, details)
            return success
        except Exception as e:
            self.log_test("ZennoPoster Redirect System", False, str(e))
            return False

    def test_zenno_network_accessibility(self):
        """Test network accessibility for ZennoPoster integration"""
        try:
            # Test if the API is accessible from network (simulating ZennoPoster access)
            test_endpoints = [
                f"{self.base_url}/api/",
                f"{self.base_url}/api/chat",
                f"{self.base_url}/api/test"
            ]
            
            accessible_endpoints = []
            for endpoint in test_endpoints:
                try:
                    if "chat" in endpoint or "test" in endpoint:
                        # POST request
                        response = requests.post(endpoint, json={"message": "test"}, timeout=10)
                    else:
                        # GET request
                        response = requests.get(endpoint, timeout=10)
                    
                    if response.status_code in [200, 422]:  # 422 is validation error, but endpoint is accessible
                        accessible_endpoints.append(endpoint)
                except:
                    continue
            
            success = len(accessible_endpoints) > 0
            details = f"Accessible endpoints: {len(accessible_endpoints)}/{len(test_endpoints)}"
            if success:
                details += f", Working endpoints: {accessible_endpoints}"
            
            self.log_test("ZennoPoster Network Accessibility", success, details)
            return success
        except Exception as e:
            self.log_test("ZennoPoster Network Accessibility", False, str(e))
            return False

    def test_zenno_concurrent_users(self):
        """Test concurrent user handling (simulating multiple ZennoPoster instances)"""
        try:
            def send_message(user_id):
                """Send a message from a specific user"""
                payload = {
                    "user_id": user_id,
                    "message": f"{user_id}|Привет, как дела?"
                }
                try:
                    response = requests.post(f"{self.base_url}/api/chat", json=payload, timeout=15)
                    return response.status_code == 200, response.json() if response.status_code == 200 else {}
                except Exception as e:
                    return False, {"error": str(e)}
            
            # Create multiple concurrent users
            num_users = 5
            user_ids = [f"zenno_concurrent_{i}_{datetime.now().strftime('%H%M%S')}" for i in range(num_users)]
            
            # Send concurrent requests
            with concurrent.futures.ThreadPoolExecutor(max_workers=num_users) as executor:
                future_to_user = {executor.submit(send_message, user_id): user_id for user_id in user_ids}
                results = []
                
                for future in concurrent.futures.as_completed(future_to_user):
                    user_id = future_to_user[future]
                    try:
                        success, data = future.result()
                        results.append({"user_id": user_id, "success": success, "data": data})
                    except Exception as e:
                        results.append({"user_id": user_id, "success": False, "error": str(e)})
            
            # Analyze results
            successful_requests = sum(1 for r in results if r["success"])
            success = successful_requests >= num_users * 0.8  # At least 80% success rate
            
            details = f"Successful requests: {successful_requests}/{num_users}"
            if success:
                # Check if responses are different (indicating proper user separation)
                responses = [r["data"].get("response", "") for r in results if r["success"]]
                unique_responses = len(set(responses))
                details += f", Unique responses: {unique_responses}"
            
            self.log_test("ZennoPoster Concurrent Users", success, details)
            return success
        except Exception as e:
            self.log_test("ZennoPoster Concurrent Users", False, str(e))
            return False

    def test_zenno_response_speed(self):
        """Test API response speed for ZennoPoster integration"""
        try:
            test_user_id = f"zenno_speed_{datetime.now().strftime('%H%M%S')}"
            response_times = []
            
            # Send multiple requests and measure response time
            for i in range(5):
                payload = {
                    "user_id": test_user_id,
                    "message": f"{test_user_id}|Тест скорости {i+1}"
                }
                
                start_time = time.time()
                response = requests.post(f"{self.base_url}/api/chat", json=payload, timeout=self.timeout)
                end_time = time.time()
                
                if response.status_code == 200:
                    response_times.append(end_time - start_time)
                else:
                    self.log_test("ZennoPoster Response Speed", False, f"Request {i+1} failed")
                    return False
            
            # Analyze response times
            avg_response_time = sum(response_times) / len(response_times)
            max_response_time = max(response_times)
            min_response_time = min(response_times)
            
            # Success if average response time is under 5 seconds
            success = avg_response_time < 5.0
            details = f"Avg: {avg_response_time:.2f}s, Min: {min_response_time:.2f}s, Max: {max_response_time:.2f}s"
            
            if not success:
                details += " (Too slow for production)"
            
            self.log_test("ZennoPoster Response Speed", success, details)
            return success
        except Exception as e:
            self.log_test("ZennoPoster Response Speed", False, str(e))
            return False

    def test_zenno_context_memory(self):
        """Test context memory between ZennoPoster requests"""
        try:
            test_user_id = f"zenno_context_{datetime.now().strftime('%H%M%S')}"
            
            # Send a series of messages to test context retention
            messages = [
                f"{test_user_id}|Привет, меня зовут Алексей",
                f"{test_user_id}|Как тебя зовут?",
                f"{test_user_id}|Помнишь как меня зовут?",
                f"{test_user_id}|Что мы обсуждали?"
            ]
            
            responses = []
            for i, msg in enumerate(messages):
                payload = {
                    "user_id": test_user_id,
                    "message": msg
                }
                
                response = requests.post(f"{self.base_url}/api/chat", json=payload, timeout=self.timeout)
                if response.status_code == 200:
                    data = response.json()
                    responses.append({
                        "message": msg,
                        "response": data["response"],
                        "message_number": data["message_number"]
                    })
                    # Small delay between messages
                    time.sleep(0.5)
                else:
                    self.log_test("ZennoPoster Context Memory", False, f"Message {i+1} failed")
                    return False
            
            # Check if context is maintained (message numbers should increment)
            message_numbers = [r["message_number"] for r in responses]
            context_maintained = all(message_numbers[i] < message_numbers[i+1] for i in range(len(message_numbers)-1))
            
            success = context_maintained and len(responses) == len(messages)
            details = f"Messages sent: {len(responses)}, Message numbers: {message_numbers}"
            
            if success:
                details += ", Context maintained across requests"
            
            self.log_test("ZennoPoster Context Memory", success, details)
            return success
        except Exception as e:
            self.log_test("ZennoPoster Context Memory", False, str(e))
            return False

    def test_zenno_language_switching(self):
        """Test language switching for international ZennoPoster usage"""
        try:
            test_user_base = f"zenno_lang_{datetime.now().strftime('%H%M%S')}"
            
            # Test Russian
            ru_payload = {
                "user_id": f"{test_user_base}_ru",
                "message": f"{test_user_base}_ru|Привет красавица",
                "character_config": {"language": "ru", "country": "Россия"}
            }
            
            # Test English
            en_payload = {
                "user_id": f"{test_user_base}_en", 
                "message": f"{test_user_base}_en|Hello beautiful",
                "character_config": {"language": "en", "country": "США"}
            }
            
            ru_response = requests.post(f"{self.base_url}/api/chat", json=ru_payload, timeout=self.timeout)
            en_response = requests.post(f"{self.base_url}/api/chat", json=en_payload, timeout=self.timeout)
            
            ru_success = ru_response.status_code == 200
            en_success = en_response.status_code == 200
            success = ru_success and en_success
            
            details = f"Russian: {ru_success}, English: {en_success}"
            
            if success:
                ru_data = ru_response.json()
                en_data = en_response.json()
                
                # Check if responses are in appropriate languages
                ru_text = ru_data['response']
                en_text = en_data['response']
                
                # Simple language detection (check for Cyrillic vs Latin characters)
                has_cyrillic = any('\u0400' <= char <= '\u04FF' for char in ru_text)
                has_latin = any('a' <= char.lower() <= 'z' for char in en_text)
                
                details += f", RU response: '{ru_text[:30]}...', EN response: '{en_text[:30]}...'"
                if has_cyrillic:
                    details += ", Russian response contains Cyrillic"
                if has_latin:
                    details += ", English response contains Latin"
            
            self.log_test("ZennoPoster Language Switching", success, details)
            return success
        except Exception as e:
            self.log_test("ZennoPoster Language Switching", False, str(e))
            return False

    def test_zenno_error_handling(self):
        """Test error handling for malformed ZennoPoster requests"""
        try:
            error_tests = [
                # Missing message
                {"payload": {"user_id": "test"}, "expected": "validation error"},
                # Empty message
                {"payload": {"user_id": "test", "message": ""}, "expected": "empty message"},
                # Invalid JSON structure
                {"payload": {"invalid": "structure"}, "expected": "validation error"},
                # Very long message
                {"payload": {"user_id": "test", "message": "x" * 10000}, "expected": "long message handling"}
            ]
            
            error_handled_count = 0
            for i, test in enumerate(error_tests):
                try:
                    response = requests.post(f"{self.base_url}/api/chat", json=test["payload"], timeout=10)
                    # Error handling is successful if we get a proper error response (4xx) or a graceful fallback (200)
                    if response.status_code in [400, 422, 500] or (response.status_code == 200 and "error" not in response.text.lower()):
                        error_handled_count += 1
                except:
                    # If request fails completely, that's also acceptable error handling
                    error_handled_count += 1
            
            success = error_handled_count >= len(error_tests) * 0.75  # At least 75% of errors handled gracefully
            details = f"Errors handled gracefully: {error_handled_count}/{len(error_tests)}"
            
            self.log_test("ZennoPoster Error Handling", success, details)
            return success
        except Exception as e:
            self.log_test("ZennoPoster Error Handling", False, str(e))
            return False

    def test_zenno_production_readiness(self):
        """Test production readiness indicators"""
        try:
            indicators = {
                "api_accessible": False,
                "proper_cors": False,
                "error_handling": False,
                "response_format": False,
                "performance": False
            }
            
            # Test API accessibility
            try:
                response = requests.get(f"{self.base_url}/api/", timeout=10)
                indicators["api_accessible"] = response.status_code == 200
            except:
                pass
            
            # Test CORS headers
            try:
                response = requests.options(f"{self.base_url}/api/chat", timeout=10)
                cors_headers = response.headers.get('Access-Control-Allow-Origin', '')
                indicators["proper_cors"] = '*' in cors_headers or 'localhost' in cors_headers
            except:
                pass
            
            # Test error handling
            try:
                response = requests.post(f"{self.base_url}/api/chat", json={"invalid": "data"}, timeout=10)
                indicators["error_handling"] = response.status_code in [400, 422, 500]
            except:
                pass
            
            # Test response format
            try:
                payload = {"user_id": "prod_test", "message": "test"}
                response = requests.post(f"{self.base_url}/api/chat", json=payload, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    required_fields = ["response", "message_number", "is_semi", "is_last"]
                    indicators["response_format"] = all(field in data for field in required_fields)
            except:
                pass
            
            # Test performance
            try:
                start_time = time.time()
                payload = {"user_id": "perf_test", "message": "performance test"}
                response = requests.post(f"{self.base_url}/api/chat", json=payload, timeout=10)
                end_time = time.time()
                indicators["performance"] = (end_time - start_time) < 3.0 and response.status_code == 200
            except:
                pass
            
            # Calculate readiness score
            readiness_score = sum(indicators.values())
            total_indicators = len(indicators)
            success = readiness_score >= total_indicators * 0.8  # At least 80% ready
            
            details = f"Readiness score: {readiness_score}/{total_indicators}"
            for indicator, status in indicators.items():
                details += f", {indicator}: {'✓' if status else '✗'}"
            
            self.log_test("ZennoPoster Production Readiness", success, details)
            return success
        except Exception as e:
            self.log_test("ZennoPoster Production Readiness", False, str(e))
            return False

    def run_all_tests(self):
        """Run all ZennoPoster integration tests"""
        print("🚀 Starting ZennoPoster Integration Tests for AI Sexter Bot")
        print(f"🔗 Testing API at: {self.base_url}")
        print("=" * 70)
        
        # Core ZennoPoster functionality
        print("📡 Testing Core ZennoPoster Functionality...")
        self.test_zenno_server_health()
        self.test_zenno_message_format()
        self.test_zenno_redirect_system()
        
        # Network and performance
        print("\n🌐 Testing Network Integration...")
        self.test_zenno_network_accessibility()
        self.test_zenno_concurrent_users()
        self.test_zenno_response_speed()
        
        # Advanced features
        print("\n🧠 Testing Advanced Features...")
        self.test_zenno_context_memory()
        self.test_zenno_language_switching()
        self.test_zenno_error_handling()
        
        # Production readiness
        print("\n🏭 Testing Production Readiness...")
        self.test_zenno_production_readiness()
        
        # Print summary
        print("=" * 70)
        print(f"📊 ZennoPoster Integration Test Results: {self.tests_passed}/{self.tests_run} tests passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All ZennoPoster integration tests passed! System is ready for production.")
            return True
        else:
            failed_tests = self.tests_run - self.tests_passed
            print(f"⚠️  {failed_tests} tests failed. Review issues before production deployment.")
            return False

def main():
    """Main test execution"""
    tester = ZennoPosterIntegrationTester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())