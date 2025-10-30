'use client'

import { useState } from 'react'
import axios from 'axios'
import { Search, Loader2, BookOpen, MapPin, TrendingUp } from 'lucide-react'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface Citation {
  paper_title: string
  section: string
  page: number
  relevance_score: number
}

interface QueryResponse {
  answer: string
  citations: Citation[]
  sources_used: string[]
  confidence: number
  paper_ids_used?: number[]
}

export function QueryInterface() {
  const [question, setQuestion] = useState('')
  const [topK, setTopK] = useState(5)
  const [loading, setLoading] = useState(false)
  const [response, setResponse] = useState<QueryResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

  const handleQuery = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!question.trim()) {
      setError('Please enter a question')
      return
    }

    setLoading(true)
    setError(null)
    setResponse(null)

    try {
      const result = await axios.post(`${API_URL}/api/query`, {
        question: question.trim(),
        top_k: topK,
      })

      setResponse(result.data)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to process query. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'text-green-600 bg-green-100'
    if (confidence >= 0.6) return 'text-yellow-600 bg-yellow-100'
    return 'text-red-600 bg-red-100'
  }

  return (
    <div className="max-w-5xl mx-auto">
      {/* Query Form */}
      <div className="bg-white rounded-lg shadow-md p-8 mb-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">Ask a Question</h2>
        <p className="text-gray-600 mb-6">
          Query your indexed research papers using natural language. The AI will search through papers and provide cited answers.
        </p>

        <form onSubmit={handleQuery} className="space-y-4">
          <div>
            <label htmlFor="question" className="block text-sm font-medium text-gray-700 mb-2">
              Your Question
            </label>
            <textarea
              id="question"
              rows={3}
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="e.g., What methodology was used in the transformer paper?"
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            />
          </div>

          <div>
            <label htmlFor="topK" className="block text-sm font-medium text-gray-700 mb-2">
              Number of relevant chunks to retrieve: {topK}
            </label>
            <input
              id="topK"
              type="range"
              min="1"
              max="20"
              value={topK}
              onChange={(e) => setTopK(parseInt(e.target.value))}
              className="w-full"
            />
            <div className="flex justify-between text-xs text-gray-500 mt-1">
              <span>1 (Focused)</span>
              <span>20 (Comprehensive)</span>
            </div>
          </div>

          <button
            type="submit"
            disabled={loading || !question.trim()}
            className={`
              w-full px-6 py-3 rounded-lg font-medium flex items-center justify-center space-x-2
              ${loading || !question.trim()
                ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                : 'bg-primary-600 text-white hover:bg-primary-700 active:bg-primary-800'
              }
            `}
          >
            {loading ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                <span>Processing...</span>
              </>
            ) : (
              <>
                <Search className="w-5 h-5" />
                <span>Search Papers</span>
              </>
            )}
          </button>
        </form>

        {error && (
          <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-sm text-red-700">{error}</p>
          </div>
        )}
      </div>

      {/* Response */}
      {response && (
        <div className="space-y-6">
          {/* Answer Card */}
          <div className="bg-white rounded-lg shadow-md p-8">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xl font-bold text-gray-900">Answer</h3>
              <div className={`px-3 py-1 rounded-full text-sm font-medium ${getConfidenceColor(response.confidence)}`}>
                {(response.confidence * 100).toFixed(0)}% Confidence
              </div>
            </div>
            <div className="prose prose-sm max-w-none">
              <p className="text-gray-700 leading-relaxed whitespace-pre-wrap">{response.answer}</p>
            </div>
          </div>

          {/* Citations */}
          {response.citations && response.citations.length > 0 && (
            <div className="bg-white rounded-lg shadow-md p-8">
              <h3 className="text-xl font-bold text-gray-900 mb-4 flex items-center space-x-2">
                <BookOpen className="w-5 h-5" />
                <span>Citations ({response.citations.length})</span>
              </h3>
              <div className="space-y-4">
                {response.citations.map((citation, index) => (
                  <div
                    key={index}
                    className="border border-gray-200 rounded-lg p-4 hover:border-primary-300 transition-colors"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <h4 className="font-medium text-gray-900 mb-2">
                          [{index + 1}] {citation.paper_title}
                        </h4>
                        <div className="flex items-center space-x-4 text-sm text-gray-600">
                          <span className="flex items-center space-x-1">
                            <MapPin className="w-4 h-4" />
                            <span>Section: {citation.section}</span>
                          </span>
                          <span>Page: {citation.page}</span>
                        </div>
                      </div>
                      <div className="ml-4">
                        <div className="flex items-center space-x-1 text-sm">
                          <TrendingUp className="w-4 h-4 text-primary-600" />
                          <span className="font-medium text-primary-600">
                            {(citation.relevance_score * 100).toFixed(1)}%
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Sources Used */}
          {response.sources_used && response.sources_used.length > 0 && (
            <div className="bg-white rounded-lg shadow-md p-6">
              <h4 className="font-medium text-gray-900 mb-3">Sources Used</h4>
              <div className="flex flex-wrap gap-2">
                {response.sources_used.map((source, index) => (
                  <span
                    key={index}
                    className="px-3 py-1 bg-primary-50 text-primary-700 rounded-full text-sm"
                  >
                    {source}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
