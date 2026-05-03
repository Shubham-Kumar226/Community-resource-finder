# AI Community Resource Finder 🏥📍

An AI-powered, domain-specific chatbot application designed to help citizens locate essential community services, healthcare facilities, and local resources. This project leverages local structured datasets and Generative AI to provide accurate, context-aware assistance across multiple cities.

## 🚀 Key Features
*   **Domain-Specific AI:** Uses Generative AI (Gemini/OpenAI) with high-precision constraints to ensure factual responses.
*   **Local Data Integration:** Efficiently queries local CSV and JSON datasets for resource retrieval.
*   **Interactive Interface:** A responsive chat-based UI built with **Streamlit**.
*   **Multi-City Knowledge Base:** Utilizes localized datasets to provide verified community information for various cities.

## 🛠️ Technology Stack
*   **Frontend:** Streamlit
*   **Backend:** Python
*   **Data Storage:** Local File System (CSV/JSON)
*   **AI Engine:** Generative AI API (Gemini Pro / GPT-3.5)
*   **Data Analysis:** Pandas

## 📂 Project Structure
```text
├── app.py              # Main chatbot interface (Streamlit)
├── .env                # Environment variables (API Keys)
├── requirements.txt    # Project dependencies
└── data/               # Project Knowledge Base
    ├── city_hospital_data.csv
    ├── city_transport_data.csv
    └── community_resources_seed.json
