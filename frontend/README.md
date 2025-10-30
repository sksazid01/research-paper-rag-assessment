# Research Paper RAG - Frontend

Modern Next.js web application for the Research Paper RAG system.

## Features

- 🔍 **Query Interface** - Ask questions and get AI-powered answers with citations
- 📤 **File Upload** - Upload PDF research papers
- 📚 **Paper Management** - View, manage, and delete indexed papers
- 📊 **Statistics** - View paper statistics and section distributions
- 📜 **Query History** - Track all your queries with response times
- 📈 **Analytics** - See popular topics and trends

## Tech Stack

- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **Icons**: Lucide React
- **HTTP Client**: Axios

## Setup

1. **Install dependencies**:
   ```bash
   npm install
   ```

2. **Configure API URL** (optional):
   Edit `.env.local`:
   ```bash
   NEXT_PUBLIC_API_URL=http://localhost:8000
   ```

3. **Run development server**:
   ```bash
   npm run dev
   ```

4. **Open browser**:
   Navigate to [http://localhost:3000](http://localhost:3000)

## Build for Production

```bash
# Build the application
npm run build

# Start production server
npm start
```

## Project Structure

```
frontend/
├── app/
│   ├── layout.tsx          # Root layout
│   ├── page.tsx            # Home page
│   └── globals.css         # Global styles
├── components/
│   ├── FileUpload.tsx      # Upload component
│   ├── QueryInterface.tsx  # Query form & results
│   ├── PaperList.tsx       # Papers list & stats
│   └── QueryHistory.tsx    # History & analytics
├── public/                 # Static assets
├── package.json
├── tsconfig.json
├── tailwind.config.js
└── next.config.js
```

## Usage

### 1. Upload Papers
- Click on "Upload Papers" tab
- Select one or more PDF files
- Click "Upload Papers"

### 2. Query Papers
- Go to "Query Papers" tab
- Enter your question
- Adjust top_k slider for retrieval depth
- Click "Search Papers"
- View answer with citations

### 3. Manage Papers
- Go to "My Papers" tab
- View all indexed papers
- Click "Stats" to see paper details
- Click "Delete" to remove a paper

### 4. View History
- Go to "Query History" tab
- See all past queries
- View popular topics

## API Integration

The frontend connects to the FastAPI backend at `http://localhost:8000`.

Endpoints used:
- `POST /api/papers/upload` - Upload papers
- `POST /api/query` - Query papers
- `GET /api/papers` - List papers
- `GET /api/papers/{id}` - Get paper details
- `GET /api/papers/{id}/stats` - Get paper stats
- `DELETE /api/papers/{id}` - Delete paper
- `GET /api/queries/history` - Get query history
- `GET /api/analytics/popular` - Get popular topics

## Development

```bash
# Install dependencies
npm install

# Run in development mode with hot reload
npm run dev

# Lint code
npm run lint

# Build for production
npm run build
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `NEXT_PUBLIC_API_URL` | Backend API URL | `http://localhost:8000` |

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

## License

MIT
