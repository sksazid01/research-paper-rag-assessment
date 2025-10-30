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
        model: "llama3"
      }, {
        headers: {
          'Content-Type': 'application/json'
        }
      })

      setResponse(result.data)
    } catch (err: any) {
      let errorMessage = 'Failed to process query. Please try again.'
      
      if (err.response?.data?.detail) {
        const detail = err.response.data.detail
        if (typeof detail === 'string') {
          errorMessage = detail
        } else if (Array.isArray(detail)) {
          errorMessage = detail.map((e: any) => e.msg || JSON.stringify(e)).join(', ')
        } else if (typeof detail === 'object') {
          errorMessage = detail.msg || JSON.stringify(detail)
        }
      } else if (err.message) {
        errorMessage = err.message
      }
      
      setError(errorMessage)
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
      <div className="bg-white rounded-2xl shadow-lg border border-gray-100 p-8 mb-6">
        <div className="flex items-center space-x-3 mb-4">
          <div className="bg-gradient-to-br from-blue-100 to-indigo-100 p-2 rounded-lg">
            <Search className="w-6 h-6 text-blue-600" />
          </div>
          <h2 className="text-2xl font-bold text-gray-900">Ask a Question</h2>
        </div>
        <p className="text-gray-600 mb-6 leading-relaxed">
          Query your indexed research papers using natural language. The AI will search through papers and provide cited answers.
        </p>

        <form onSubmit={handleQuery} className="space-y-4">
          <div>
            <label htmlFor="question" className="block text-sm font-semibold text-gray-700 mb-2">
              Your Question
            </label>
            <textarea
              id="question"
              rows={4}
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="e.g., What methodology was used in the transformer paper?"
              className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all resize-none"
            />
          </div>

          <div className="bg-gradient-to-br from-gray-50 to-slate-50 p-5 rounded-xl border-2 border-gray-200">
            <div className="flex items-center justify-between mb-4">
              <label htmlFor="topK" className="block text-sm font-semibold text-gray-700">
                Number of relevant chunks to retrieve
              </label>
              <div className="flex items-center space-x-3">
                <input
                  type="number"
                  min="1"
                  max="100"
                  value={topK}
                  onChange={(e) => {
                    const val = parseInt(e.target.value) || 1
                    setTopK(Math.max(1, Math.min(100, val)))
                  }}
                  className="w-20 px-3 py-2 border-2 border-blue-200 rounded-lg text-center font-bold text-blue-700 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
                <span className="text-xs font-medium text-gray-500">chunks</span>
              </div>
            </div>
            
            <div className="relative">
              <input
                id="topK"
                type="range"
                min="1"
                max="20"
                value={Math.min(topK, 20)}
                onChange={(e) => setTopK(parseInt(e.target.value))}
                className="w-full h-3 rounded-lg appearance-none cursor-pointer slider-thumb"
                style={{
                  background: `linear-gradient(to right, #3b82f6 0%, #6366f1 ${((Math.min(topK, 20) - 1) / 19) * 100}%, #e5e7eb ${((Math.min(topK, 20) - 1) / 19) * 100}%, #e5e7eb 100%)`
                }}
              />
            </div>
            
            <div className="flex justify-between text-xs text-gray-600 mt-3 font-medium">
              <span className="flex items-center space-x-1">
                <span className="w-2 h-2 rounded-full bg-blue-600"></span>
                <span>1 (Focused)</span>
              </span>
              <span className="text-gray-500">Use slider (1-20) or type manually (1-100)</span>
              <span className="flex items-center space-x-1">
                <span className="w-2 h-2 rounded-full bg-indigo-600"></span>
                <span>20+ (Comprehensive)</span>
              </span>
            </div>
          </div>

          <button
            type="submit"
            disabled={loading || !question.trim()}
            className={`
              w-full px-6 py-4 rounded-xl font-semibold flex items-center justify-center space-x-2 transition-all transform
              ${loading || !question.trim()
                ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
                : 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white hover:from-blue-700 hover:to-indigo-700 shadow-lg hover:shadow-xl hover:scale-[1.02] active:scale-[0.98]'
              }
            `}
          >
            {loading ? (
              <>
                <Loader2 className="w-6 h-6 animate-spin" />
                <span className="text-lg">Processing Query...</span>
              </>
            ) : (
              <>
                <Search className="w-6 h-6" />
                <span className="text-lg">Search Papers</span>
              </>
            )}
          </button>
        </form>

        {error && (
          <div className="mt-4 p-4 bg-red-50 border-l-4 border-red-500 rounded-lg shadow-sm">
            <p className="text-sm text-red-700 font-medium">{error}</p>
          </div>
        )}
      </div>

      {/* Response */}
      {response && (
        <div className="space-y-6 animate-in fade-in duration-500">
          {/* Answer Card */}
          <div className="bg-gradient-to-br from-white to-blue-50/30 rounded-2xl shadow-xl border border-blue-100 p-8">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-2xl font-bold text-gray-900 flex items-center space-x-2">
                <div className="w-1 h-8 bg-gradient-to-b from-blue-600 to-indigo-600 rounded-full"></div>
                <span>Answer</span>
              </h3>
              <div className={`px-4 py-2 rounded-full text-sm font-bold shadow-md ${getConfidenceColor(response.confidence)}`}>
                {(response.confidence * 100).toFixed(0)}% Confidence
              </div>
            </div>
            <div className="prose prose-base max-w-none">
              <p className="text-gray-800 leading-relaxed whitespace-pre-wrap text-lg">{response.answer}</p>
            </div>
          </div>

          {/* Citations */}
          {response.citations && response.citations.length > 0 && (
            <div className="bg-white rounded-2xl shadow-lg border border-gray-100 p-8">
              <h3 className="text-xl font-bold text-gray-900 mb-6 flex items-center space-x-3">
                <div className="bg-gradient-to-br from-amber-100 to-orange-100 p-2 rounded-lg">
                  <BookOpen className="w-5 h-5 text-amber-600" />
                </div>
                <span>Citations ({response.citations.length})</span>
              </h3>
              <div className="space-y-3">
                {response.citations.map((citation, index) => (
                  <div
                    key={index}
                    className="border-2 border-gray-100 rounded-xl p-5 hover:border-blue-200 hover:shadow-md transition-all bg-gradient-to-r from-white to-gray-50"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <h4 className="font-semibold text-gray-900 mb-3 flex items-start space-x-2">
                          <span className="bg-blue-600 text-white px-2 py-0.5 rounded text-xs font-bold">{index + 1}</span>
                          <span className="flex-1">{citation.paper_title}</span>
                        </h4>
                        <div className="flex items-center space-x-4 text-sm text-gray-600">
                          <span className="flex items-center space-x-1 bg-gray-100 px-3 py-1 rounded-full">
                            <MapPin className="w-3.5 h-3.5" />
                            <span className="font-medium">{citation.section}</span>
                          </span>
                          <span className="bg-gray-100 px-3 py-1 rounded-full font-medium">Page {citation.page}</span>
                        </div>
                      </div>
                      <div className="ml-4">
                        <div className="flex items-center space-x-1.5 bg-blue-50 px-3 py-2 rounded-lg">
                          <TrendingUp className="w-4 h-4 text-blue-600" />
                          <span className="font-bold text-blue-700 text-sm">
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
            <div className="bg-white rounded-2xl shadow-lg border border-gray-100 p-6">
              <h4 className="font-semibold text-gray-900 mb-4 text-lg">Sources Used</h4>
              <div className="flex flex-wrap gap-2">
                {response.sources_used.map((source, index) => (
                  <span
                    key={index}
                    className="px-4 py-2 bg-gradient-to-r from-blue-50 to-indigo-50 text-blue-700 border border-blue-200 rounded-full text-sm font-semibold shadow-sm hover:shadow-md transition-all"
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
