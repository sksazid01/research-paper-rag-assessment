# Streaming Response Feature

## Overview
Implemented real-time streaming responses similar to ChatGPT/Claude for the RAG system. Users can now see the LLM response word-by-word as it's being generated, providing a much better user experience.

## Changes Made

### Backend

#### 1. `src/services/ollama_client.py`
- Added `generate_text_stream()` function that yields text chunks as they're generated
- Uses Ollama's streaming API with `stream: True`
- Parses NDJSON (newline-delimited JSON) responses

#### 2. `src/api/routes.py`
- Added new `/api/query/stream` endpoint
- Returns Server-Sent Events (SSE) for real-time streaming
- Sends three types of events:
  - `token`: Individual text chunks (streamed word-by-word)
  - `metadata`: Citations, sources, confidence (sent at the end)
  - `done`: Completion signal

### Frontend

#### 3. `frontend/components/QueryInterface.tsx`
- Added streaming mode toggle (ON/OFF)
- Implemented `handleQueryStreaming()` function using Fetch API with streaming
- Added visual indicators:
  - "Streaming..." badge while generating
  - Blinking cursor animation
  - Real-time text display as tokens arrive
- Maintains backward compatibility with non-streaming mode

## Features

### User Benefits
1. **Faster Perceived Response**: Users see text immediately instead of waiting for the full response
2. **Better UX**: Similar experience to ChatGPT/Claude
3. **Progress Indication**: Users know the system is working
4. **Flexibility**: Can toggle streaming on/off based on preference

### Technical Features
1. **Server-Sent Events (SSE)**: Standard streaming protocol
2. **Graceful Fallback**: Non-streaming mode still available
3. **Error Handling**: Proper error messages for streaming failures
4. **Metadata Preservation**: Citations and confidence still included after streaming completes

## Usage

### Toggle Streaming Mode
- **ON** (default): Responses stream word-by-word
- **OFF**: Traditional mode with full response at once

### API Endpoints
- **Streaming**: `POST /api/query/stream`
- **Non-streaming**: `POST /api/query`

Both endpoints accept the same request format:
```json
{
  "question": "What methodology was used?",
  "top_k": 5,
  "paper_ids": [1, 3],  // optional
  "model": "llama3"
}
```

## Testing

1. **Enable streaming mode** (toggle should be ON)
2. **Ask a question** about your papers
3. **Watch the response** appear word-by-word
4. **Citations and metadata** appear after the answer completes

## Performance Impact

- **Latency**: Significantly reduced perceived latency
- **Network**: More frequent small messages vs one large message
- **Server**: Similar CPU/memory usage, slightly more network overhead

## Future Improvements

1. Add typing speed control
2. Add pause/resume streaming
3. Show estimated completion percentage
4. Add streaming for multiple queries in parallel
