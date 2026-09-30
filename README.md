# 🥗 MacroSnap

> Your AI-powered nutrition tracker and personal assistant.

MacroSnap is an AI-powered web application that lets you interact with an intelligent assistant, analyze meals from photos, estimate calories and macros, and receive conversation summaries directly through WhatsApp.

It also works as a general-purpose AI assistant, so you can ask questions about programming, technology, mathematics, engineering, studies, fitness, nutrition, and everyday topics.

---

## ✨ Features

- 🤖 **AI Assistant**
  - Ask questions on a wide range of topics
  - Get explanations, ideas, and assistance in a conversational way

- 📸 **AI Meal Analysis**
  - Upload a photo of your meal
  - Identify what the meal appears to contain
  - Estimate calories
  - Estimate protein, carbohydrates, and fat

- 💬 **Text-Based Food Analysis**
  - Describe what you ate
  - Get estimated nutritional information

- 📊 **Nutrition Summary**
  - Generate a summary of meals discussed during the conversation
  - Calculate running calorie and macro totals when possible

- 📱 **WhatsApp Integration**
  - Send your conversation/nutrition summary directly to WhatsApp

- 🌐 **Web-Based Interface**
  - Built with Streamlit
  - No separate frontend application required

- 🔐 **Secure API Configuration**
  - API keys and credentials are stored using Streamlit Secrets

---

## How It Works

```text
                    ┌─────────────────┐
                    │      User       │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │    Streamlit    │
                    │   Web Interface │
                    └────────┬────────┘
                             │
                 ┌───────────┴───────────┐
                 │                       │
                 ▼                       ▼
          Text / Question          Meal Image
                 │                       │
                 └───────────┬───────────┘
                             ▼
                    ┌─────────────────┐
                    │   Google GenAI  │
                    │   AI Assistant  │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │ AI Response /   │
                    │ Nutrition Info  │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │     Twilio      │
                    │    WhatsApp     │
                    └─────────────────┘
