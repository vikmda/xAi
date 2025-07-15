import React, { useState, useEffect } from "react";
import "./App.css";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function App() {
  const [activeTab, setActiveTab] = useState("main");
  const [characterConfig, setCharacterConfig] = useState({
    name: "Анна",
    age: "23",
    country: "Россия",
    interests: "спорт, кино, музыка",
    mood: "игривое",
    message_count: 3,
    semi_message: "Хочешь увидеть больше? Переходи по ссылке...",
    last_message: "Встретимся в приватном чате, дорогой",
    learning_enabled: true,
    language: "ru"
  });
  
  const [testMessage, setTestMessage] = useState("");
  const [testResponse, setTestResponse] = useState("");
  const [testRating, setTestRating] = useState(0);
  
  const [trainingQuestion, setTrainingQuestion] = useState("");
  const [trainingAnswer, setTrainingAnswer] = useState("");
  
  const [statistics, setStatistics] = useState(null);
  const [badResponses, setBadResponses] = useState([]);
  const [aiStatus, setAiStatus] = useState(null);

  const handleConfigChange = (field, value) => {
    setCharacterConfig(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleTest = async () => {
    try {
      const response = await axios.post(`${API}/test`, {
        message: testMessage,
        character_config: characterConfig
      });
      setTestResponse(response.data.response);
    } catch (error) {
      console.error("Error testing bot:", error);
    }
  };

  const handleTraining = async () => {
    try {
      await axios.post(`${API}/train`, {
        question: trainingQuestion,
        answer: trainingAnswer,
        language: characterConfig.language
      });
      alert("Обучение добавлено!");
      setTrainingQuestion("");
      setTrainingAnswer("");
    } catch (error) {
      console.error("Error training bot:", error);
    }
  };

  const loadAiStatus = async () => {
    try {
      const response = await axios.get(`${API}/ai_status`);
      setAiStatus(response.data);
    } catch (error) {
      console.error("Error loading AI status:", error);
    }
  };

  const loadStatistics = async () => {
    try {
      const response = await axios.get(`${API}/statistics`);
      setStatistics(response.data);
    } catch (error) {
      console.error("Error loading statistics:", error);
    }
  };

  const loadBadResponses = async () => {
    try {
      const response = await axios.get(`${API}/bad_responses`);
      setBadResponses(response.data);
    } catch (error) {
      console.error("Error loading bad responses:", error);
    }
  };

  const deleteBadResponse = async (id) => {
    try {
      await axios.delete(`${API}/bad_responses/${id}`);
      loadBadResponses();
    } catch (error) {
      console.error("Error deleting bad response:", error);
    }
  };

  const resetDatabase = async () => {
    if (window.confirm("Вы уверены, что хотите сбросить всю базу данных?")) {
      try {
        await axios.delete(`${API}/reset`);
        alert("База данных сброшена!");
      } catch (error) {
        console.error("Error resetting database:", error);
      }
    }
  };

  const MainTab = () => (
    <div className="tab-content">
      <h2>Основные настройки</h2>
      <div className="config-grid">
        <div className="config-item">
          <label>Имя:</label>
          <input
            type="text"
            value={characterConfig.name}
            onChange={(e) => handleConfigChange("name", e.target.value)}
          />
        </div>
        
        <div className="config-item">
          <label>Возраст:</label>
          <input
            type="text"
            value={characterConfig.age}
            onChange={(e) => handleConfigChange("age", e.target.value)}
          />
        </div>
        
        <div className="config-item">
          <label>Страна проживания:</label>
          <select
            value={characterConfig.country}
            onChange={(e) => {
              handleConfigChange("country", e.target.value);
              handleConfigChange("language", e.target.value === "Россия" ? "ru" : "en");
            }}
          >
            <option value="Россия">Россия</option>
            <option value="США">США</option>
          </select>
        </div>
        
        <div className="config-item">
          <label>Увлечения:</label>
          <input
            type="text"
            value={characterConfig.interests}
            onChange={(e) => handleConfigChange("interests", e.target.value)}
          />
        </div>
        
        <div className="config-item">
          <label>Настроение:</label>
          <input
            type="text"
            value={characterConfig.mood}
            onChange={(e) => handleConfigChange("mood", e.target.value)}
          />
        </div>
        
        <div className="config-item">
          <label>Количество сообщений:</label>
          <input
            type="number"
            value={characterConfig.message_count}
            onChange={(e) => handleConfigChange("message_count", parseInt(e.target.value))}
          />
        </div>
        
        <div className="config-item">
          <label>Semi сообщение:</label>
          <textarea
            value={characterConfig.semi_message}
            onChange={(e) => handleConfigChange("semi_message", e.target.value)}
          />
        </div>
        
        <div className="config-item">
          <label>Last сообщение:</label>
          <textarea
            value={characterConfig.last_message}
            onChange={(e) => handleConfigChange("last_message", e.target.value)}
          />
        </div>
        
        <div className="config-item">
          <label>
            <input
              type="checkbox"
              checked={characterConfig.learning_enabled}
              onChange={(e) => handleConfigChange("learning_enabled", e.target.checked)}
            />
            Включить обучение
          </label>
        </div>
      </div>
      
      <div className="test-section">
        <h3>Тестирование</h3>
        <div className="test-input">
          <input
            type="text"
            placeholder="Введите сообщение для теста"
            value={testMessage}
            onChange={(e) => setTestMessage(e.target.value)}
          />
          <button onClick={handleTest}>Тестировать</button>
        </div>
        
        {testResponse && (
          <div className="test-response">
            <p><strong>Ответ:</strong> {testResponse}</p>
            {statistics && statistics.ai_confidence && (
              <p><strong>Эмоция:</strong> {statistics.emotion || "neutral"}</p>
            )}
            <div className="rating">
              <label>Оценка:</label>
              {[1, 2, 3, 4, 5].map(num => (
                <button
                  key={num}
                  className={`star ${testRating >= num ? 'active' : ''}`}
                  onClick={() => setTestRating(num)}
                >
                  ★
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
      
      <div className="training-section">
        <h3>Ручное обучение</h3>
        <div className="training-inputs">
          <input
            type="text"
            placeholder="Вопрос"
            value={trainingQuestion}
            onChange={(e) => setTrainingQuestion(e.target.value)}
          />
          <input
            type="text"
            placeholder="Ответ"
            value={trainingAnswer}
            onChange={(e) => setTrainingAnswer(e.target.value)}
          />
          <button onClick={handleTraining}>Добавить</button>
        </div>
      </div>
    </div>
  );

  const AdvancedTab = () => (
    <div className="tab-content">
      <h2>Дополнительные настройки</h2>
      
      <div className="ai-status-section">
        <h3>Статус AI системы</h3>
        <button onClick={loadAiStatus}>Проверить статус AI</button>
        
        {aiStatus && (
          <div className="ai-status-display">
            <div className={`status-item ${aiStatus.advanced_ai_available ? 'active' : 'inactive'}`}>
              <span>🤖 Продвинутая AI: {aiStatus.advanced_ai_available ? 'Активна' : 'Неактивна'}</span>
            </div>
            <div className={`status-item ${aiStatus.vector_db_available ? 'active' : 'inactive'}`}>
              <span>🗄️ Векторная БД: {aiStatus.vector_db_available ? 'Подключена' : 'Отключена'}</span>
            </div>
            <div className={`status-item ${aiStatus.model_loaded ? 'active' : 'inactive'}`}>
              <span>📚 Модель: {aiStatus.model_loaded ? 'Загружена' : 'Не загружена'}</span>
            </div>
            
            {aiStatus.total_vector_entries && (
              <div className="learning-stats">
                <h4>Статистика обучения:</h4>
                <p>Всего векторных записей: {aiStatus.total_vector_entries}</p>
                <p>Автообучение: {aiStatus.auto_learned_responses || 0}</p>
                <p>Ручное обучение: {aiStatus.manual_learned_responses || 0}</p>
                <p>Общее обучение: {aiStatus.total_learned || 0}</p>
              </div>
            )}
          </div>
        )}
      </div>
      
      <div className="stats-section">
        <h3>Статистика</h3>
        <button onClick={loadStatistics}>Загрузить статистику</button>
        
        {statistics && (
          <div className="stats-display">
            <div className="stats-grid">
              <div className="stat-card">
                <h4>Общее</h4>
                <p>Разговоров: {statistics.total_conversations}</p>
                <p>Пользователей: {statistics.total_users}</p>
              </div>
              
              {statistics.ai_confidence && (
                <div className="stat-card">
                  <h4>AI Уверенность</h4>
                  <p>Средняя: {(statistics.ai_confidence.avg_confidence * 100).toFixed(1)}%</p>
                  <p>Высокая: {statistics.ai_confidence.high_confidence}</p>
                </div>
              )}
              
              {statistics.learning_stats && (
                <div className="stat-card">
                  <h4>Обучение</h4>
                  <p>Векторных записей: {statistics.learning_stats.total_vector_entries}</p>
                  <p>Выучено: {statistics.learning_stats.total_learned}</p>
                </div>
              )}
            </div>
            
            <div className="charts-section">
              <h4>Топ вопросов:</h4>
              <div className="questions-list">
                {statistics.top_questions.map((item, index) => (
                  <div key={index} className="question-item">
                    <span className="question-text">{item._id}</span>
                    <span className="question-count">{item.count}</span>
                  </div>
                ))}
              </div>
              
              {statistics.emotion_distribution && (
                <div className="emotions-section">
                  <h4>Распределение эмоций:</h4>
                  <div className="emotions-list">
                    {statistics.emotion_distribution.map((emotion, index) => (
                      <div key={index} className="emotion-item">
                        <span className="emotion-name">{emotion._id}</span>
                        <span className="emotion-count">{emotion.count}</span>
                        <div className="emotion-bar">
                          <div 
                            className="emotion-fill" 
                            style={{width: `${(emotion.count / statistics.total_conversations) * 100}%`}}
                          ></div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
      
      <div className="bad-responses-section">
        <h3>Плохие ответы</h3>
        <button onClick={loadBadResponses}>Загрузить плохие ответы</button>
        
        <div className="bad-responses-list">
          {badResponses.map((response, index) => (
            <div key={index} className="bad-response-item">
              <span>{response.text}</span>
              <button onClick={() => deleteBadResponse(response._id)}>❌</button>
            </div>
          ))}
        </div>
      </div>
      
      <div className="reset-section">
        <h3>Сброс базы данных</h3>
        <p className="warning-text">⚠️ Это удалит все разговоры, обучение и векторную базу данных</p>
        <button className="danger-btn" onClick={resetDatabase}>
          Сбросить БД
        </button>
      </div>
    </div>
  );

  return (
    <div className="App">
      <header className="app-header">
        <h1>AI Секстер Бот - Панель управления</h1>
        <nav className="tabs">
          <button 
            className={activeTab === "main" ? "active" : ""}
            onClick={() => setActiveTab("main")}
          >
            Основное
          </button>
          <button 
            className={activeTab === "advanced" ? "active" : ""}
            onClick={() => setActiveTab("advanced")}
          >
            Дополнительно
          </button>
        </nav>
      </header>
      
      <main className="main-content">
        {activeTab === "main" ? <MainTab /> : <AdvancedTab />}
      </main>
    </div>
  );
}

export default App;