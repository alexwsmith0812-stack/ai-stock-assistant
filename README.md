# Stock Insights Assistant

A web application that allows users to ask natural language questions about stocks and receive AI-powered answers using OpenAI's function calling capabilities and real-time stock data from Finnhub.

## Architecture Overview

The application follows a clean, layered architecture with clear separation of concerns. The frontend is a simple HTML/JavaScript chat interface that communicates with a FastAPI backend via REST endpoints. When a user submits a question, the backend routes it to the AI service, which uses OpenAI's function calling (tool calling) feature. OpenAI analyzes the question and decides which stock data tools to invoke—such as fetching quotes, company profiles, comparisons, or news. The AI service executes these tools via the stock service, which wraps the Finnhub Python client and handles all external API calls. Results are passed back to OpenAI, which synthesizes them into a natural language response that's returned to the user.

The design emphasizes dependency injection (clients are passed as parameters) to enable easy testing, graceful error handling at every layer, and a simple request-response flow without over-engineering. The stock service functions are pure and testable, while the AI service manages the tool-calling loop and conversation state. Configuration is centralized using Pydantic settings with environment variable validation, ensuring clear error messages if API keys are missing.

## How to Run

### Prerequisites

- Python 3.10 or higher
- Docker and Docker Compose (for containerized deployment)
- OpenAI API key
- Finnhub API key (free tier available at [finnhub.io](https://finnhub.io))

### Local Development

1. Clone the repository and navigate to the project directory:
   ```bash
   cd stock-insights
   ```

2. Create a `.env` file from the example:
   ```bash
   cp .env.example .env
   ```

3. Edit `.env` and add your API keys:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   FINNHUB_API_KEY=your_finnhub_api_key_here
   ```

4. Install dependencies:
   ```bash
   pip install -e ".[dev]"
   ```

5. Run the application:
   ```bash
   uvicorn app.main:app --reload
   ```

6. Open your browser to `http://localhost:8000`

### Docker Deployment

1. Create a `.env` file with your API keys (see above)

2. Build and run with Docker Compose:
   ```bash
   docker compose up --build
   ```

3. The application will be available at `http://localhost:8000`

### Running Tests

```bash
pytest
```

### Linting

```bash
ruff check .
```

## Trade-offs and Decisions

- **Simple Frontend**: Chose vanilla HTML/JS over a framework to keep the project lightweight and focused on the backend AI integration. This reduces complexity and makes the codebase easier to understand.

- **Synchronous Stock Service**: The Finnhub client is synchronous, so stock service functions are synchronous. The AI service is async to handle concurrent requests efficiently, but tool execution happens in a thread pool implicitly when needed.

- **Tool Calling Loop Limit**: Implemented a hard cap of 3 iterations in the tool-calling loop to prevent infinite loops. In production, you might want to make this configurable or add more sophisticated termination logic.

- **Error Handling Strategy**: All stock service functions return structured error responses (Pydantic models with error fields) rather than raising exceptions. This ensures the AI always receives a response it can work with, even when APIs fail.

- **No Database**: The application is stateless—no conversation history is persisted. This keeps the architecture simple but means users can't reference previous questions. For production, you'd want to add session management and storage.

## What I Would Improve with More Time

1. **Conversation Memory**: Add session management and store conversation history so the AI can reference previous questions and maintain context across multiple interactions.

2. **Rate Limiting**: Implement rate limiting per user/IP to prevent abuse and manage API costs, especially for OpenAI calls which can be expensive.

3. **Caching**: Add caching for frequently requested stock data (e.g., quotes) to reduce API calls and improve response times. Redis would be a good fit here.

4. **Better Error Messages**: Enhance error handling to provide more specific, actionable error messages to users when APIs fail or rate limits are hit.

5. **Streaming Responses**: Implement Server-Sent Events (SSE) to stream AI responses token-by-token for a better user experience, similar to ChatGPT.

6. **Input Validation**: Add more robust input validation and sanitization, especially for ticker symbols, to prevent injection or invalid API calls.

7. **Monitoring and Logging**: Add structured logging, metrics collection, and health check endpoints for production observability.

8. **Frontend Enhancements**: Improve the UI with markdown rendering for AI responses, syntax highlighting for stock data, and better mobile responsiveness.

## AI Tools Used

This project was scaffolded and developed with assistance from **Claude Sonnet** (via Cursor). The AI helped with:

- **Architecture Design**: Iterating on the overall structure, deciding on the layered service approach, and determining how to integrate OpenAI's function calling with the stock data API.

- **Code Generation**: Generating boilerplate for FastAPI routes, Pydantic models, service functions, and test cases with proper mocking strategies.

- **Error Handling Patterns**: Designing graceful error handling that works well with AI tool calling—ensuring errors are always returned as structured data rather than exceptions.

- **Testing Strategy**: Creating comprehensive test suites that mock external APIs and verify both happy paths and error cases.

- **Documentation**: Assisting with README structure and explaining architectural decisions clearly.

The AI was particularly helpful in ensuring consistency across the codebase, catching edge cases in error handling, and suggesting improvements to the tool-calling loop implementation.
