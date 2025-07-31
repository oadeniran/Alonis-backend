# ALONIS Backend

**A**wareness  
**L**ife  
**O**bservation  
**N**urturing  
**I**ntuition  
**S**elfhood

## Overview

Alonis is a comprehensive mental health and personality assessment platform that provides AI-powered therapeutic conversations, assessments, and personalized recommendations. The backend is built with FastAPI and uses MongoDB for data storage, with advanced RAG (Retrieval-Augmented Generation) capabilities for personalized responses.

## Table of contents
- [Overview](#overview)
- [Project Architecture](#project-architecture)
    - [Directory Structure](#directory-structure)
- [Data Flow Architecture](#data-flow-architecture)
    - [Routes → Routes Logic → Core Implementation](#1-routes--routes-logic--core-implementation)
    - [Request Flow Examples](#2-request-flow-examples)
- [Core Modules Functionality](#core-modules-functionality)
- [Recommendation System Architecture](#recommendation-system-architecture)
    - [System Overview](#system-overview)
    - [Recommendation Types](#recommendation-types)
    - [Generation Process](#generation-process)
    - [AI Integration Points](#ai-integration-points)
    - [User Interaction Tracking](#user-interaction-tracking)
    - [Technical Implementation](#technical-implementation)
- [Key Features](#key-features)
- [AI and ML Components](#ai-and-ml-components)
- [Database Schema](#database-schema)
- [Environment Configuration](#environment-configuration)
- [Background Services](#background-services)
- [Security Features](#security-features)
- [Getting Started](#getting-started)
    - [Prerequisites](#prerequisites)
    - [Installation](#installation)
    - [API Documentation](#api-documentation)
- [API Endpoints Overview](#api-endpoints-overview)
    - [Assessment Endpoints](#assessment-endpoints-assessment)
    - [Talk Session Endpoints](#talk-session-endpoints-talk)
    - [User Management Endpoints](#user-management-endpoints-user)
    - [Recommendation Endpoints](#recommendation-endpoints-useruid)
- [Contributing](#contributing)
- [Technology Stack](#technology-stack)

## Project Architecture

### Directory Structure

```text
├── main.py                     # FastAPI application entry point
├── config.py                   # Configuration settings
├── db.py                       # Database connection and collections
├── chatbot.py                  # Core AI chatbot implementations
├── ragImplementation.py        # RAG (Retrieval-Augmented Generation) logic
├── utils.py                    # Utility functions
├── requirements.txt            # Python dependencies
├── Dockerfile                  # Container configuration
├── Home.py                     # Streamlit home page (if applicable)
├── routes/                     # API route definitions
│   ├── assessmentRoutes.py     # Assessment-related endpoints
│   ├── talkRoutes.py          # Talk session endpoints
│   ├── userActionsRoutes.py   # User management endpoints
│   └── commonRoutes.py        # Shared route utilities
├── routesLogic/               # Business logic for routes
│   ├── assessment.py          # Assessment logic implementation
│   ├── talk.py               # Talk session logic
│   └── userActions.py        # User action logic
├── core/                      # Core business modules
│   ├── userActions.py         # User management operations
│   ├── chatActions.py         # Chat message operations
│   ├── talksSessions.py       # Talk session management
│   ├── background_tasks.py    # Asynchronous background operations
│   ├── big5_personality.py    # Big Five personality assessment
│   ├── mental_prediction.py   # Mental health prediction models
│   ├── recommendations.py     # Recommendation generation
│   ├── qloo_core.py          # Qloo integration for recommendations
│   └── notesActions.py       # User notes/goals management
├── dtos/                      # Data Transfer Objects
│   ├── assessment_dto.py      # Assessment request/response models
│   ├── user_dto.py           # User registration/login models
│   ├── notes_dto.py          # Notes and goals models
│   └── talk_dto.py           # Talk session models
├── embeddings/                # Vector embeddings storage
└── model_data/               # ML model files
```

## Data Flow Architecture

### 1. Routes → Routes Logic → Core Implementation

The application follows a clean three-layer architecture:

```text
HTTP Request → Routes → Routes Logic → Core Modules → Database/AI Services
```

#### **Routes Layer** (`routes/`)

- **Purpose**: Define API endpoints and handle HTTP requests/responses
- **Responsibilities**:
  - Request validation using Pydantic DTOs
  - Route parameter extraction
  - Delegating to business logic
- **Files**: `assessmentRoutes.py`, `talkRoutes.py`, `userActionsRoutes.py`

#### **Routes Logic Layer** (`routesLogic/`)

- **Purpose**: Business logic coordination and validation
- **Responsibilities**:
  - Input validation and sanitization
  - Orchestrating multiple core module calls
  - Error handling and response formatting
  - Async task management
- **Files**: `assessment.py`, `talk.py`, `userActions.py`

#### **Core Layer** (`core/`)

- **Purpose**: Core business operations and integrations
- **Responsibilities**:
  - Database operations
  - AI model interactions
  - Background task processing
  - Complex business logic implementation

### 2. Request Flow Examples

#### Assessment Flow

```text
POST /assessment/assessment
├── assessmentRoutes.py (Route)
├── assessment.py (Logic)
│   ├── utils.get_system_template()
│   ├── userActions.add_user_session()
│   ├── chatbot.MindWavebot()
│   └── background_tasks.update_user_embeddings()
└── Return assessment response
```

#### Talk Session Flow

```text
POST /talk/talk-session
├── talkRoutes.py (Route)
├── talk.py (Logic)
│   ├── userActions.add_user_session()
│   ├── talksSessions.talkToMe()
│   │   ├── load_retriever() (RAG)
│   │   ├── load_model()
│   │   └── letsTalk()
│   └── background_tasks.update_user_embeddings()
└── Return chat response
```

#### User Registration Flow

```text
POST /user/sign-up
├── userActionsRoutes.py (Route)
├── userActions.py (Logic)
│   ├── Input validation
│   ├── core.userActions.signup()
│   └── background_tasks.init_user_embeddings()
└── Return registration response
```

#### Recommendation Generation Flow

```text
Multiple Triggers → Background Tasks → Recommendation Generation
│
├── User Login (2nd+ time)
│   └── background_tasks.run_sequenced_user_login_tasks()
│       └── generate_alonis_recommendations_for_user()
│
├── User Interaction Updates
│   └── background_tasks.update_user_embeddings()
│       └── generate_alonis_recommendations_for_user()
│
└── Manual Initiation
    └── POST /user/{uid}/initiate-recommendations
        └── background_tasks.generate_alonis_recommendations_for_user()

Recommendation Types Generated:
├── General Alonis Recommendations (RAG-based)
│   ├── recommendations.get_alonis_recommendations()
│   ├── Uses user embeddings and context
│   └── AI-generated personalized activities
│
├── Qloo-Powered Recommendations
│   ├── Movies/TV Shows
│   │   ├── qloo_core.get_qloo_tags_to_select_from()
│   │   ├── AI selects relevant tags based on user data
│   │   └── qloo_core.get_qloo_recommendations()
│   │
│   └── Books
│       ├── Similar tag-based selection process
│       └── Contextual recommendations with AI commentary
│
└── Storage & Retrieval
    ├── userActions.add_recommendations()
    ├── userActions.get_current_alonis_recommendations()
    └── Interaction tracking for improved future recommendations
```

## Core Modules Functionality

### 1. **User Management** (`core/userActions.py`)

- User registration and authentication
- Session management
- User profile operations
- Report generation and storage

### 2. **Chat Operations** (`core/chatActions.py`)

- Message storage and retrieval
- Chat history management
- Support for different session types (assessment, talk, rant)

### 3. **Talk Sessions** (`core/talksSessions.py`)

- AI-powered therapeutic conversations
- RAG-based context retrieval
- Personalized quote and story generation
- Session state management

### 4. **Background Tasks** (`core/background_tasks.py`)

- Asynchronous embedding updates
- Recommendation generation
- User data processing
- Long-running operations

### 5. **Assessment Modules**

- **Big Five Personality** (`core/big5_personality.py`): OCEAN personality assessment
- **Mental Health Prediction** (`core/mental_prediction.py`): Mental state evaluation

### 6. **Recommendations** (`core/recommendations.py`)

- Personalized content recommendations
- Integration with external APIs (Qloo)
- Multi-type recommendations (books, movies, activities)

## Recommendation System Architecture

### System Overview

Alonis features a sophisticated recommendation engine that provides personalized content across multiple categories. The system combines AI-powered analysis of user data with external API integrations to deliver contextually relevant recommendations.

### Recommendation Types

#### 1. **General Alonis Recommendations** (`alonis_recommendation`)

- **Technology**: RAG-based using user embeddings and interaction history
- **Content**: Personalized activities, wellness suggestions, therapeutic exercises
- **Generation**: AI model analyzes user context and generates recommendations
- **Personalization**: Based on assessment results, chat history, and user behavior

#### 2. **Entertainment Recommendations**

##### Movies & TV Shows (`alonis_recommendation_movies`)

- **API Integration**: Qloo for entertainment data
- **Tag Selection**: AI analyzes user preferences to select relevant content tags
- **Contextual Enhancement**: AI generates personalized commentary for each recommendation
- **Pagination**: Tracks user interaction with tags to avoid repetitive suggestions

##### Books (`alonis_recommendation_books`)

- **Similar Process**: Tag-based selection using Qloo API
- **Literary Focus**: Books aligned with user's mental health journey and interests
- **AI Commentary**: Personalized explanations for why each book fits the user

#### 3. **Future Categories**

- **Music** (`alonis_recommendation_songs`): Planned integration
- **News** (`alonis_recommendation_news`): Curated based on user interests

### Generation Process

#### Trigger Mechanisms

1. **User Login** (2nd+ time): Automatic generation of all recommendation types
2. **Interaction Updates**: New recommendations generated after significant user interactions
3. **Manual Initiation**: Users can request new recommendations via API endpoint
4. **Assessment Completion**: Fresh recommendations based on new psychological insights

#### Generation Workflow

```text
1. Check Recommendation Eligibility
   └── confirm_to_add_more_alonis_recommendations()

2. For General Recommendations:
   ├── Load user-specific RAG retriever
   ├── Build context with previous recommendations
   ├── Generate AI recommendations using user data
   └── Parse and structure recommendation list

3. For Qloo-Powered Recommendations:
   ├── Fetch available content tags from Qloo API
   ├── Use AI to select relevant tags based on user profile
   ├── Query Qloo API with selected tags and pagination
   ├── Enhance each recommendation with AI-generated context
   └── Update user tag interaction history

4. Store & Track:
   ├── Save recommendations to database
   ├── Track user interactions and preferences
   └── Update recommendation pages for future sessions
```

### AI Integration Points

#### Context Analysis

- **User Embeddings**: Vector representations of user interactions and assessments
- **Historical Data**: Previous recommendations, interactions, and feedback
- **Psychological Profile**: Assessment results and therapeutic conversation insights

#### Tag Selection Algorithm

```text
User Data → RAG Model → Tag Relevance Analysis → Qloo Query → Content Retrieval
```

#### Personalization Engine

- **Dynamic Commentary**: AI explains why each recommendation suits the user
- **Behavioral Learning**: System learns from user interactions to improve future suggestions
- **Cross-Category Intelligence**: Insights from one category inform others

### User Interaction Tracking

#### Engagement Metrics

- **View Interactions**: When users access recommendations
- **Completion Tracking**: Marking recommendations as completed
- **Feedback Loop**: User interactions improve future recommendations

#### API Endpoints for Recommendations

```text
GET /{uid}/alonis-recommendations/{rec_type}?page={page}
├── Retrieve personalized recommendations by type
├── Supports pagination for large recommendation sets
└── Returns AI-generated context for each item

POST /{uid}/mark-interaction-with-recommendation/{rec_id}
├── Track user engagement with specific recommendations
├── Updates user preference learning
└── Triggers background embedding updates

POST /{uid}/mark-recommendation-as-completed/{rec_id}
├── Mark recommendations as completed
├── Influences future recommendation generation
└── Tracks user progress and preferences

POST /{uid}/initiate-recommendations
├── Manually trigger recommendation generation
├── Useful for testing or user-requested updates
└── Runs all recommendation types in parallel
```

### Technical Implementation

#### Background Processing

- **Asynchronous Generation**: Recommendations generated without blocking user operations
- **Parallel Processing**: Multiple recommendation types generated simultaneously
- **Error Handling**: Graceful fallbacks and retry mechanisms

#### Data Storage

- **MongoDB Collections**: Dedicated collections for recommendations and user interactions
- **Vector Embeddings**: User-specific embedding stores for contextual analysis
- **Caching Strategy**: Efficient retrieval of frequently accessed recommendations

#### External API Management

- **Qloo Integration**: Robust handling of external API calls with rate limiting
- **Fallback Mechanisms**: Local recommendation generation when external APIs are unavailable
- **Data Enrichment**: AI enhancement of external API responses

## Key Features

### 🧠 **AI-Powered Assessments**

- **Personality Tests**: Big Five (OCEAN) personality assessment
- **Mental Health Screening**: Depression, bipolar, and general mental health evaluation
- **Adaptive Questioning**: Dynamic question generation based on user responses

### 💬 **Therapeutic Chat Sessions**

- **RAG-Enhanced Conversations**: Context-aware responses using user history
- **Session Management**: Persistent chat sessions with state tracking
- **Personalized Content**: Daily quotes and stories based on user profile

### 🔧 **Background Processing**

- **Embedding Management**: Vector embeddings for user data and context
- **Recommendation Engine**: AI-generated personalized recommendations
- **Data Processing**: Asynchronous processing of user interactions

### 📊 **User Analytics**

- **Session Tracking**: Comprehensive session and interaction logging
- **Progress Monitoring**: User journey and assessment progress tracking
- **Report Generation**: Detailed psychological assessment reports

## AI and ML Components

### 1. **Language Models**

- **Primary Model**: GPT-4o-mini via OpenAI API
- **Purpose**: Assessment questions, therapeutic responses, report generation
- **Temperature**: Controlled for consistent psychological assessments

### 2. **RAG Implementation** (`ragImplementation.py`)

- **Vector Database**: ChromaDB for embedding storage
- **Embedding Model**: OpenAI embeddings for semantic search
- **Context Retrieval**: User-specific context for personalized responses

### 3. **Assessment Models**

- **Big Five Assessment**: Psychological profile evaluation
- **Mental Health Prediction**: ML models for mental state prediction
- **Adaptive Testing**: Dynamic question selection based on responses

## Database Schema

### Collections

- **Users**: User profiles and authentication data
- **Sessions**: User session information and metadata
- **Messages**: Chat messages and conversation history
- **Reports**: Assessment results and generated reports
- **Recommendations**: Personalized content recommendations
- **Embeddings**: Vector embeddings per user (file-based ChromaDB)

## Environment Configuration

The application supports multiple environments:

- **Development**: Full debugging and reload capabilities
- **Production**: Optimized settings for deployment
- **API Documentation**: Auto-generated OpenAPI/Swagger docs

## Background Services

### Embedding Management

- **User Initialization**: Create embeddings on user signup
- **Real-time Updates**: Update embeddings with new user data
- **Context Building**: Build conversation context from user history

### Recommendation System

- **Content Types**: General activities, books, movies, music, news
- **Generation Triggers**: Login events, assessment completion
- **External APIs**: Integration with Qloo for enhanced recommendations

## Security Features

- **Password Encryption**: Bcrypt hashing for user passwords
- **Session Management**: Secure session handling with UUIDs
- **Input Validation**: Pydantic DTOs for request validation
- **CORS Configuration**: Cross-origin request handling

## Getting Started

### Prerequisites

- Python 3.11+
- MongoDB instance
- OpenAI API key
- Required Python packages (see `requirements.txt`)

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment variables
# OPENAI_API_KEY, MONGODB_URI, etc.

# Run the application
python main.py
```

### API Documentation

Once running, visit:

- Development: `http://localhost:8000/dev/docs`
- Production: `http://localhost:8000/mindwave/docs`

## API Endpoints Overview

### Assessment Endpoints (`/assessment`)

- `POST /assessment` - Start psychological assessment
- `POST /assessment-result` - Get assessment results and reports
- `GET /generate-session-id` - Generate new session identifier

### Talk Session Endpoints (`/talk`)

- `POST /talk-session` - Engage in therapeutic conversation
- `GET /personalized-quote` - Get daily personalized quote
- `GET /daily-story` - Get personalized daily story

### User Management Endpoints (`/user`)

- `POST /sign-up` - User registration
- `POST /sign-in` - User authentication
- `GET /get-all-sessions` - Retrieve user sessions
- `GET /get-session-chats` - Get chat history for session
- `GET /get-user-reports` - Retrieve assessment reports
- `POST /add-note-or-goal` - Add user notes/goals
- `GET /get-notes-and-goals` - Retrieve user notes/goals

### Recommendation Endpoints (`/user/{uid}`)

- `GET /alonis-recommendations/{rec_type}` - Get personalized recommendations by type
  - **Types**: `alonis_recommendation`, `alonis_recommendation_movies`, `alonis_recommendation_books`, `alonis_recommendation_songs`, `alonis_recommendation_news`
  - **Parameters**: `page` for pagination
- `POST /mark-interaction-with-recommendation/{rec_id}` - Track user engagement with recommendations
- `POST /mark-recommendation-as-completed/{rec_id}` - Mark recommendations as completed
- `POST /initiate-recommendations` - Manually trigger recommendation generation

## Contributing

This project follows clean architecture principles with clear separation of concerns. When contributing:

1. **Routes**: Add new endpoints in appropriate route files
2. **Logic**: Implement business logic in `routesLogic/` layer
3. **Core**: Add reusable operations in `core/` modules
4. **DTOs**: Define request/response models in `dtos/`
5. **Testing**: Ensure comprehensive testing of new features

## Technology Stack

- **Framework**: FastAPI
- **Database**: MongoDB
- **AI/ML**: OpenAI GPT-4o-mini, ChromaDB
- **Authentication**: Bcrypt
- **Async Processing**: asyncio
- **Validation**: Pydantic
- **Containerization**: Docker