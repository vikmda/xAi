# AI Sexter Bot - Подробный мануал установки на Windows 11 Pro

## 📋 Содержание
1. [Системные требования](#системные-требования)
2. [Предварительная подготовка](#предварительная-подготовка)
3. [Автоматическая установка](#автоматическая-установка)
4. [Ручная установка](#ручная-установка)
5. [Настройка сети](#настройка-сети)
6. [Запуск и управление](#запуск-и-управление)
7. [Интеграция с ZennoPoster](#интеграция-с-zennoposter)
8. [Устранение проблем](#устранение-проблем)
9. [Обслуживание](#обслуживание)

---

## 🔧 Системные требования

### Минимальные требования:
- **ОС**: Windows 11 Pro (64-bit)
- **Процессор**: Intel Core i5 или AMD Ryzen 5
- **Оперативная память**: 8 GB RAM
- **Свободное место**: 5 GB
- **Сеть**: Подключение к интернету

### Рекомендуемые требования:
- **Процессор**: Intel Xeon E5-2699 v3 (28 ядер) или аналогичный
- **Оперативная память**: 32 GB RAM
- **Накопитель**: SSD диск
- **Сеть**: Гигабитное подключение

---

## 🎯 Предварительная подготовка

### 1. Установка Python 3.8+
```bash
# Скачайте Python с официального сайта
https://www.python.org/downloads/

# При установке обязательно отметьте:
☑️ Add Python to PATH
☑️ Install pip
☑️ Install for all users (если нужно)
```

### 2. Установка Node.js
```bash
# Скачайте Node.js LTS с официального сайта
https://nodejs.org/en/download/

# Установите с настройками по умолчанию
# Проверьте установку:
node --version
npm --version
```

### 3. Установка MongoDB Community Edition
```bash
# Скачайте MongoDB Community Edition
https://www.mongodb.com/try/download/community

# Выберите:
- Version: Latest
- Platform: Windows
- Package: msi

# При установке:
☑️ Complete installation
☑️ Install MongoDB as a Service
☑️ Run service as Network Service user
☑️ Install MongoDB Compass (GUI)
```

### 4. Настройка брандмауэра Windows
```powershell
# Откройте PowerShell от имени администратора
# Добавьте правила для портов:

# Основной API
New-NetFirewallRule -DisplayName "AI Sexter Bot - Main API" -Direction Inbound -Protocol TCP -LocalPort 8001 -Action Allow

# ZennoPoster API
New-NetFirewallRule -DisplayName "AI Sexter Bot - ZennoPoster" -Direction Inbound -Protocol TCP -LocalPort 8080 -Action Allow

# Web Interface
New-NetFirewallRule -DisplayName "AI Sexter Bot - Web" -Direction Inbound -Protocol TCP -LocalPort 3000 -Action Allow

# MongoDB
New-NetFirewallRule -DisplayName "MongoDB" -Direction Inbound -Protocol TCP -LocalPort 27017 -Action Allow
```

---

## 🚀 Автоматическая установка

### 1. Скачайте файлы
```bash
# Скачайте все файлы проекта в папку
C:\AI_Sexter_Bot\

# Структура папки должна быть:
AI_Sexter_Bot\
├── install_sexter_bot.bat
├── start_sexter_bot.bat
├── stop_sexter_bot.bat
├── requirements.txt
├── backend\
│   ├── server.py
│   ├── advanced_ai.py
│   ├── zenno_server.py
│   └── zennoposter_api.py
└── frontend\
    ├── package.json
    ├── src\
    │   ├── App.js
    │   └── App.css
    └── public\
```

### 2. Запустите автоматическую установку
```bash
# Щелкните правой кнопкой мыши по файлу:
install_sexter_bot.bat

# Выберите "Запуск от имени администратора"
# Следуйте инструкциям установщика
```

### 3. Дождитесь завершения установки
```bash
# Установщик автоматически:
✅ Проверит системные требования
✅ Создаст виртуальную среду Python
✅ Установит все зависимости
✅ Настроит MongoDB
✅ Создаст конфигурационные файлы
✅ Настроит брандмауэр
✅ Создаст ярлыки на рабочем столе
```

---

## 🛠️ Ручная установка

### 1. Создайте структуру папок
```bash
mkdir C:\AI_Sexter_Bot
mkdir C:\AI_Sexter_Bot\backend
mkdir C:\AI_Sexter_Bot\frontend
mkdir C:\AI_Sexter_Bot\data
mkdir C:\AI_Sexter_Bot\data\db
mkdir C:\AI_Sexter_Bot\logs
```

### 2. Создайте виртуальную среду Python
```bash
cd C:\AI_Sexter_Bot
python -m venv venv
venv\Scripts\activate
```

### 3. Установите Python зависимости
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Настройте MongoDB
```bash
# Создайте конфигурационный файл
echo dbpath=C:\AI_Sexter_Bot\data\db > C:\AI_Sexter_Bot\mongodb.conf
echo port=27017 >> C:\AI_Sexter_Bot\mongodb.conf
echo logpath=C:\AI_Sexter_Bot\logs\mongodb.log >> C:\AI_Sexter_Bot\mongodb.conf

# Запустите MongoDB
mongod --config C:\AI_Sexter_Bot\mongodb.conf
```

### 5. Создайте файл конфигурации
```bash
# Создайте файл backend\.env
MONGO_URL=mongodb://localhost:27017
DB_NAME=sexter_bot
HOST=0.0.0.0
PORT=8001
ZENNO_HOST=192.168.0.16
ZENNO_PORT=8080
```

### 6. Установите Node.js зависимости
```bash
cd C:\AI_Sexter_Bot\frontend
npm install
```

---

## 🌐 Настройка сети

### 1. Настройка IP адреса 192.168.0.16
```bash
# Откройте "Параметры сети и Интернет"
# Выберите "Изменить параметры адаптера"
# Щелкните правой кнопкой по сетевому адаптеру
# Выберите "Свойства"
# Выберите "Протокол Интернета версии 4 (TCP/IPv4)"
# Нажмите "Свойства"

# Установите:
IP-адрес: 192.168.0.16
Маска подсети: 255.255.255.0
Основной шлюз: 192.168.0.1
Предпочитаемый DNS: 8.8.8.8
```

### 2. Проверка сетевых настроек
```bash
# Откройте командную строку
ipconfig

# Убедитесь что IP адрес 192.168.0.16 назначен
ping 192.168.0.16
```

### 3. Настройка доступа из сети
```bash
# Убедитесь что порты открыты:
netstat -an | findstr :8001
netstat -an | findstr :8080
netstat -an | findstr :3000
```

---

## 🚦 Запуск и управление

### 1. Запуск через ярлыки
```bash
# На рабочем столе найдите ярлык:
"Start AI Sexter Bot"

# Двойной щелчок запустит все сервисы
```

### 2. Запуск через батник
```bash
# Щелкните правой кнопкой по файлу:
start_sexter_bot.bat

# Выберите "Запуск от имени администратора"
```

### 3. Ручной запуск
```bash
cd C:\AI_Sexter_Bot
venv\Scripts\activate

# Запустите MongoDB
mongod --dbpath data\db --port 27017

# Запустите основной сервер
python backend\server.py

# Запустите ZennoPoster API
python backend\zenno_server.py

# Запустите веб-интерфейс
cd frontend
npm start
```

### 4. Проверка работы
```bash
# Откройте браузер и перейдите на:
http://localhost:3000      # Веб-интерфейс
http://192.168.0.16:8001   # Основной API
http://192.168.0.16:8080   # ZennoPoster API

# Или используйте curl:
curl http://192.168.0.16:8080/health
```

### 5. Остановка сервисов
```bash
# Используйте ярлык:
"Stop AI Sexter Bot"

# Или батник:
stop_sexter_bot.bat
```

---

## 🔗 Интеграция с ZennoPoster

### 1. Настройка ZennoPoster
```csharp
// В ZennoPoster создайте POST запрос к:
string url = "http://192.168.0.16:8080/message/simple";

// Тело запроса:
var requestBody = new {
    message = "user123|Привет красотка",
    language = "ru",
    character_name = "Анна"
};

// Отправьте JSON запрос
string jsonRequest = JsonConvert.SerializeObject(requestBody);
string response = instance.SendRequest(url, jsonRequest, "POST", "application/json");
```

### 2. Примеры запросов
```bash
# Простое сообщение
curl -X POST http://192.168.0.16:8080/message/simple \
  -H "Content-Type: application/json" \
  -d '{"message": "user123|Привет красотка"}'

# Настройка персонажа
curl -X POST http://192.168.0.16:8080/configure \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "max_messages": 5,
    "semi_message": "Хочешь больше? Переходи: https://example.com",
    "character_name": "Анна",
    "language": "ru"
  }'

# Получение статистики
curl http://192.168.0.16:8080/stats
```

### 3. Обработка ответов
```json
// Обычный ответ
{
  "response": "Привет дорогой! Как дела?",
  "user_id": "user123",
  "is_redirect": false
}

// Перенаправление
{
  "response": "Хочешь больше? Переходи: https://example.com",
  "user_id": "user123",
  "is_redirect": true
}
```

---

## 🔧 Устранение проблем

### 1. Проблемы с запуском
```bash
# Проверьте порты
netstat -an | findstr :8080
netstat -an | findstr :8001

# Проверьте процессы
tasklist | findstr python
tasklist | findstr node
tasklist | findstr mongod
```

### 2. Проблемы с MongoDB
```bash
# Проверьте службу MongoDB
sc query MongoDB

# Запустите вручную
mongod --dbpath C:\AI_Sexter_Bot\data\db --port 27017

# Проверьте подключение
mongo --host localhost --port 27017
```

### 3. Проблемы с сетью
```bash
# Проверьте IP
ipconfig

# Проверьте доступность
ping 192.168.0.16

# Проверьте брандмауэр
netsh advfirewall show allprofiles
```

### 4. Проблемы с Python
```bash
# Проверьте версию Python
python --version

# Проверьте виртуальную среду
venv\Scripts\activate
pip list

# Переустановите зависимости
pip install --upgrade -r requirements.txt
```

### 5. Логи и отладка
```bash
# Проверьте логи
type C:\AI_Sexter_Bot\logs\main.log
type C:\AI_Sexter_Bot\logs\zenno.log
type C:\AI_Sexter_Bot\logs\mongodb.log

# Запустите в режиме отладки
python backend\zenno_server.py --debug
```

---

## 🔄 Обслуживание

### 1. Обновление системы
```bash
# Активируйте виртуальную среду
venv\Scripts\activate

# Обновите зависимости
pip install --upgrade -r requirements.txt

# Обновите Node.js пакеты
cd frontend
npm update
```

### 2. Резервное копирование
```bash
# Создайте резервную копию базы данных
mongodump --host localhost --port 27017 --out C:\AI_Sexter_Bot\backup

# Сохраните конфигурационные файлы
copy backend\.env C:\AI_Sexter_Bot\backup\
copy mongodb.conf C:\AI_Sexter_Bot\backup\
```

### 3. Мониторинг
```bash
# Проверьте статус системы
curl http://192.168.0.16:8080/health

# Проверьте статистику
curl http://192.168.0.16:8080/stats

# Проверьте использование ресурсов
tasklist /fi "imagename eq python.exe"
tasklist /fi "imagename eq mongod.exe"
```

### 4. Очистка логов
```bash
# Создайте батник для очистки логов
echo del /Q C:\AI_Sexter_Bot\logs\*.log > clear_logs.bat
echo echo Logs cleared! >> clear_logs.bat

# Запускайте еженедельно
```

---

## 📞 Поддержка

### Контакты технической поддержки:
- **Email**: support@sexter-bot.com
- **Telegram**: @sexter_bot_support
- **Discord**: SexyBot#1234

### Полезные ссылки:
- [Документация API](http://192.168.0.16:8080/docs)
- [Веб-интерфейс](http://192.168.0.16:3000)
- [Статистика](http://192.168.0.16:8080/stats)

---

## 📋 Чек-лист успешной установки

- [ ] Python 3.8+ установлен
- [ ] Node.js LTS установлен
- [ ] MongoDB Community Edition установлен
- [ ] Брандмауэр настроен
- [ ] IP адрес 192.168.0.16 назначен
- [ ] Все зависимости установлены
- [ ] Конфигурационные файлы созданы
- [ ] Сервисы запускаются без ошибок
- [ ] API отвечает на http://192.168.0.16:8080/health
- [ ] Веб-интерфейс доступен на http://192.168.0.16:3000
- [ ] ZennoPoster может отправлять запросы

---

**Готово! AI Sexter Bot установлен и готов к работе! 🚀**