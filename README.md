# VPN Remna Mini App

Telegram Mini App для VPN сервиса, разработанное на React + Vite.

## Особенности

- 🎨 Современный UI с голубой цветовой гаммой (#85b5dd)
- 📱 Интеграция с Telegram Web App SDK
- 🔐 Управление VPN подключением
- 💳 Профиль и баланс пользователя
- ⚙️ Настройки подключения
- 💬 Поддержка пользователей

## Установка

```bash
npm install
```

## Запуск

```bash
npm run dev
```

Приложение будет доступно по адресу `http://localhost:5173`

## Сборка

```bash
npm run build
```

## Структура проекта

```
src/
├── components/       # Компоненты (Layout, BottomNav)
├── contexts/         # React контексты (TelegramContext)
├── pages/           # Страницы приложения
│   ├── MainPage.jsx      # Главная страница с подключением
│   ├── SettingsPage.jsx  # Настройки
│   ├── ProfilePage.jsx   # Профиль и баланс
│   └── SupportPage.jsx   # Поддержка
├── App.jsx          # Главный компонент
└── main.jsx         # Точка входа

```

## Технологии

- React 18
- Vite 5
- React Router DOM 6
- Telegram Web App SDK

## Цветовая схема

- Основной цвет: #85b5dd
- Акцентный цвет: #4fc3f7
- Фон: градиент от #1a3a4a до #0d1f2d
