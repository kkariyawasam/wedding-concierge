# 💍 AI Wedding Concierge

An AI-powered wedding planning assistant that acts as a **digital concierge**, helping users plan their wedding with personalized guidance, smart automation, and intelligent recommendations.

---

## ✨ Features

### Smart Foundation (MVP)

* **AI-Powered Onboarding**

  * Chat-based onboarding collects wedding date, budget, location, and vibe
  * Automatically creates a personalized wedding profile

* **Concierge Chat (24/7 AI Assistant)**

  * Ask anything wedding-related
  * Get suggestions, etiquette advice, and creative ideas

* **Dynamic Wedding Checklist**

  * Generate a personalized checklist based on:

    * wedding timeline
    * chat preferences
  * Automatically prioritizes tasks (e.g., urgent tasks for short timelines)

* **Intelligent Budget Manager**

  * Smart budget breakdown (venue, catering, photography, etc.)
  * Adds **custom expenses** from user conversations (e.g., bouquets, DJ)

---

### Researcher (AI + Data)

* **Vendor Matchmaker (RAG)**

  * Uses vector search (ChromaDB) to find best vendors
  * Matches based on:

    * style
    * location
    * budget
  * Example:

    ```
    "Find a modern florist in Berlin under 1500"
    ```

* **Contract Analyzer (PDF Upload)**

  * Upload vendor contracts
  * AI extracts:

    * cancellation policies
    * deposit terms
    * hidden fees
    * risk flags

* **Style & Moodboard Generator**

  * Generate wedding inspiration images using AI
  * Based on vibe, location, and user input

---

## 🏗️ Tech Stack

### Backend

* FastAPI
* SQLModel (SQLite)
* LangChain
* OpenAI API
* ChromaDB (Vector Database)

### Frontend

* HTML
* CSS
* JavaScript (Vanilla)

### AI Capabilities

* Conversational AI (GPT-based)
* Retrieval-Augmented Generation (RAG)
* Document summarization
* Image generation

---

## ⚙️ How It Works

1. User starts chat → onboarding collects profile
2. Profile is stored in SQLite (session-based)
3. User chats freely with AI concierge
4. System extracts preferences from chat
5. Buttons trigger:

   * Checklist generation
   * Budget generation
6. Vendor search uses:

   * embeddings + vector search (ChromaDB)
7. Contracts are:

   * uploaded → parsed → summarized → stored

---

## 🧪 Example Use Cases

* "Find a florist in Berlin under 1500"
* "Is this contract safe to sign?"
* "Give me wedding ideas for a garden party vibe"
* "How do I politely say no kids allowed?"
* "Generate my checklist"
* "Generate my budget"


## 📊 Data Storage

SQLite stores:

* wedding profile
* chat history
* checklist items
* budget breakdown
* contract summaries

All data is linked via **session_id (browser-based)**

---

## 🧠 Future Enhancements

* Multi-agent system (LangGraph)
* Email drafting agent
* Guest list & RSVP management
* Seating arrangement AI

---

## 🌍 Impact

* Reduces stress in wedding planning
* Makes professional planning accessible to everyone
* Saves time and cost with AI automation
* Helps users make informed decisions (contracts, vendors, budgets)

