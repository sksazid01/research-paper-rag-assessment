'use client'

import { useState, useEffect } from 'react'
import axios from 'axios'
import { Search, Loader2, BookOpen, MapPin, TrendingUp, FileText, X, AlertCircle, CheckCircle2, Zap } from 'lucide-react'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface Citation {
  paper_title: string
  paper_filename?: string
  section: string
  page: string | number
  source_index?: number
  relevance_score: number
}

interface QueryResponse {
  answer: string
  citations: Citation[]
  sources_used: string[]
  confidence: number
  paper_ids_used?: number[]
}

interface Paper {
  id: number
  title: string
  filename: string
  authors?: string
  year?: string
}

export function QueryInterface() {
  const [question, setQuestion] = useState('')
  const [topK, setTopK] = useState(5)
  const [loading, setLoading] = useState(false)
  const [response, setResponse] = useState<QueryResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [papers, setPapers] = useState<Paper[]>([])
  const [selectedPaperIds, setSelectedPaperIds] = useState<number[]>([])
  const [loadingPapers, setLoadingPapers] = useState(false)
  const [streamingAnswer, setStreamingAnswer] = useState('')
  const [streamProgress, setStreamProgress] = useState(0)

  // Fetch available papers on component mount
  useEffect(() => {
    const fetchPapers = async () => {
      setLoadingPapers(true)
      try {
        const result = await axios.get(`${API_URL}/api/papers`)
        setPapers(result.data.papers || [])
      } catch (err) {
        console.error('Failed to fetch papers:', err)
      } finally {
        setLoadingPapers(false)
      }
    }

    fetchPapers()
  }, [])

  const togglePaperSelection = (paperId: number) => {
    setSelectedPaperIds(prev => 
      prev.includes(paperId) 
        ? prev.filter(id => id !== paperId)
        : [...prev, paperId]
    )
  }

  const handleQueryStreaming = async (queryPayload: any) => {
    setStreamingAnswer('')
    setStreamProgress(0)
    
    try {
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), 300000) // 5 min timeout

      const response = await fetch(`${API_URL}/api/query/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'text/event-stream',
        },
        cache: 'no-store',
        body: JSON.stringify(queryPayload),
        signal: controller.signal
      })

      clearTimeout(timeoutId)

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const reader = response.body?.getReader()
      const decoder = new TextDecoder()

      if (!reader) {
        throw new Error('Response body is not readable')
      }

      let fullAnswer = ''
      let metadata: any = null
      let buffer = '' // Buffer for incomplete lines
      let sawFirstToken = false
      let tokenCount = 0
      const estimatedTokens = 500

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        // Decode chunk and add to buffer
        buffer += decoder.decode(value, { stream: true })
        
        // Split by double newline (SSE event separator)
        const events = buffer.split('\n\n')
        
        // Keep the last incomplete event in buffer
        buffer = events.pop() || ''

        // Process complete events
        for (const event of events) {
          const lines = event.split('\n')
          
          for (const line of lines) {
            if (line.startsWith('data: ')) {
              try {
                const jsonStr = line.slice(6).trim()
                if (!jsonStr) continue
                
                const data = JSON.parse(jsonStr)
                
                if (data.type === 'token') {
                  fullAnswer += data.content
                  setStreamingAnswer(fullAnswer)
                  tokenCount++
                  setStreamProgress(Math.min((tokenCount / estimatedTokens) * 100, 95))
                  
                  if (!sawFirstToken) {
                    // Drop the loading state as soon as we start receiving data
                    setLoading(false)
                    sawFirstToken = true
                  }
                } else if (data.type === 'metadata') {
                  metadata = data
                  setStreamProgress(100)
                } else if (data.type === 'done') {
                  // Finalize response
                  if (metadata) {
                    setResponse({
                      answer: fullAnswer,
                      citations: metadata.citations || [],
                      sources_used: metadata.sources_used || [],
                      confidence: metadata.confidence || 0,
                      paper_ids_used: metadata.paper_ids_used || []
                    })
                  }
                  setStreamProgress(100)
                } else if (data.type === 'error') {
                  throw new Error(data.message)
                }
              } catch (parseErr) {
                console.warn('Failed to parse SSE data:', line, parseErr)
              }
            }
          }
        }
      }
    } catch (err: any) {
      if (err.name === 'AbortError') {
        throw new Error('Request timed out. Please try a simpler question or reduce top_k.')
      }
      throw err
    } finally {
      setStreamProgress(0)
    }
  }

  const handleQuery = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!question.trim()) {
      setError('Please enter a question')
      return
    }

    setLoading(true)
    setError(null)
    setResponse(null)
    setStreamingAnswer('')

    try {
      const queryPayload: any = {
        question: question.trim(),
        top_k: topK,
        model: "llama3"
      }

      // Add paper_ids filter if papers are selected
      if (selectedPaperIds.length > 0) {
        queryPayload.paper_ids = selectedPaperIds
      }

      await handleQueryStreaming(queryPayload)
    } catch (err: any) {
      console.error('Query error:', err)
      setError(err.message || 'Failed to process query')
      setLoading(false)
    }
  }

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'text-green-600'
    if (confidence >= 0.6) return 'text-yellow-600'
    return 'text-red-600'
  }

  const getConfidenceBadge = (confidence: number) => {
    if (confidence >= 0.8) return 'bg-green-100 text-green-800'
    if (confidence >= 0.6) return 'bg-yellow-100 text-yellow-800'
    return 'bg-red-100 text-red-800'
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="text-center mb-12">
          <div className="flex items-center justify-center mb-4">
            <BookOpen className="h-12 w-12 text-indigo-600 mr-3" />
            <h1 className="text-5xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-indigo-600 to-purple-600">
              Research Paper RAG
            </h1>
          </div>
          <p className="mt-3 text-xl text-gray-600 max-w-3xl mx-auto">
            Ask questions and get answers backed by scientific research papers
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left Sidebar - Paper Selection */}
          <div className="lg:col-span-1">
            <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-xl border border-gray-100 p-6 sticky top-8">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-lg font-bold text-gray-900 flex items-center">
                  <FileText className="h-5 w-5 mr-2 text-indigo-600" />
                  Filter by Papers
                </h2>
                {selectedPaperIds.length > 0 && (
                  <span className="px-3 py-1 bg-indigo-100 text-indigo-700 rounded-full text-sm font-semibold">
                    {selectedPaperIds.length} selected
                  </span>
                )}
              </div>

              {loadingPapers ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="h-8 w-8 animate-spin text-indigo-600" />
                </div>
              ) : (
                <div className="space-y-3 max-h-96 overflow-y-auto pr-2 custom-scrollbar">
                  {papers.map(paper => (
                    <label
                      key={paper.id}
                      className="flex items-start p-3 rounded-xl border-2 border-gray-200 hover:border-indigo-300 cursor-pointer transition-all duration-200 hover:shadow-md bg-white"
                    >
                      <input
                        type="checkbox"
                        checked={selectedPaperIds.includes(paper.id)}
                        onChange={() => togglePaperSelection(paper.id)}
                        className="mt-1 h-4 w-4 text-indigo-600 focus:ring-indigo-500 rounded border-gray-300"
                      />
                      <div className="ml-3 flex-1 min-w-0">
                        <p className="text-sm font-semibold text-gray-900 line-clamp-2">
                          {paper.title}
                        </p>
                        {(paper.authors || paper.year) && (
                          <p className="text-xs text-gray-500 mt-1">
                            {paper.authors && <span>{paper.authors}</span>}
                            {paper.authors && paper.year && <span> • </span>}
                            {paper.year && <span>{paper.year}</span>}
                          </p>
                        )}
                      </div>
                    </label>
                  ))}
                </div>
              )}

              {selectedPaperIds.length > 0 && (
                <button
                  onClick={() => setSelectedPaperIds([])}
                  className="mt-4 w-full flex items-center justify-center px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors duration-200"
                >
                  <X className="h-4 w-4 mr-2" />
                  Clear Selection
                </button>
              )}
            </div>
          </div>

          {/* Main Content */}
          <div className="lg:col-span-2 space-y-8">
            {/* Query Form */}
            <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-xl border border-gray-100 p-8">
              <form onSubmit={handleQuery} className="space-y-6">
                <div>
                  <label htmlFor="question" className="block text-sm font-semibold text-gray-900 mb-3">
                    <Search className="inline h-4 w-4 mr-2 text-indigo-600" />
                    Your Research Question
                  </label>
                  <textarea
                    id="question"
                    value={question}
                    onChange={(e) => setQuestion(e.target.value)}
                    placeholder="e.g., What are the main applications of blockchain technology?"
                    className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all duration-200 text-gray-900 placeholder-gray-400 resize-none"
                    rows={3}
                    disabled={loading}
                  />
                </div>

                <div>
                  <div className="flex items-center justify-between mb-3">
                    <label htmlFor="topK" className="block text-sm font-semibold text-gray-900">
                      <TrendingUp className="inline h-4 w-4 mr-2 text-indigo-600" />
                      Number of Sources (top_k):
                    </label>
                    <input
                      type="number"
                      min="1"
                      max="100"
                      value={topK}
                      onChange={(e) => setTopK(Math.max(1, Math.min(100, Number(e.target.value) || 1)))}
                      className="w-20 px-3 py-1 text-center border-2 border-indigo-200 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-indigo-600 font-bold"
                      disabled={loading}
                    />
                  </div>
                  <div className="relative">
                    <input
                      id="topK"
                      type="range"
                      min="1"
                      max="10"
                      value={Math.min(topK, 10)}
                      onChange={(e) => setTopK(Number(e.target.value))}
                      className="w-full h-2 rounded-lg appearance-none cursor-pointer slider-with-fill"
                      style={{
                        background: `linear-gradient(to right, #6366f1 0%, #a855f7 ${((Math.min(topK, 10) - 1) / 9) * 100}%, #e5e7eb ${((Math.min(topK, 10) - 1) / 9) * 100}%, #e5e7eb 100%)`
                      }}
                      disabled={loading}
                    />
                  </div>
                  <div className="flex justify-between text-xs text-gray-500 mt-2">
                    <span>More precise</span>
                    <span>More comprehensive (use input for &gt;10)</span>
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={loading || !question.trim()}
                  className="w-full flex items-center justify-center px-6 py-4 border border-transparent text-lg font-semibold rounded-xl text-white bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 shadow-lg hover:shadow-xl transform hover:-translate-y-0.5"
                >
                  {loading ? (
                    <>
                      <Loader2 className="animate-spin h-5 w-5 mr-3" />
                      Processing...
                    </>
                  ) : (
                    <>
                      <Zap className="h-5 w-5 mr-3" />
                      Ask Question
                    </>
                  )}
                </button>
              </form>

              {/* Progress Bar */}
              {loading && streamProgress > 0 && (
                <div className="mt-6">
                  <div className="flex justify-between text-sm text-gray-600 mb-2">
                    <span>Generating answer...</span>
                    <span>{Math.round(streamProgress)}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
                    <div
                      className="h-full bg-gradient-to-r from-indigo-500 to-purple-500 transition-all duration-300 ease-out"
                      style={{ width: `${streamProgress}%` }}
                    />
                  </div>
                </div>
              )}
            </div>

            {/* Error Display */}
            {error && (
              <div className="bg-red-50 border-l-4 border-red-500 rounded-lg p-6 flex items-start shadow-md">
                <AlertCircle className="h-6 w-6 text-red-500 mr-3 flex-shrink-0 mt-0.5" />
                <div>
                  <h3 className="text-sm font-semibold text-red-800 mb-1">Error</h3>
                  <p className="text-sm text-red-700">{error}</p>
                </div>
              </div>
            )}

            {/* Streaming Answer */}
            {streamingAnswer && (
              <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-xl border border-gray-100 p-8">
                <div className="flex items-center mb-6">
                  <div className="flex-shrink-0 h-10 w-10 rounded-full bg-gradient-to-r from-indigo-500 to-purple-500 flex items-center justify-center">
                    <BookOpen className="h-6 w-6 text-white" />
                  </div>
                  <h2 className="ml-4 text-2xl font-bold text-gray-900">Answer</h2>
                  {loading && (
                    <div className="ml-auto flex items-center text-indigo-600">
                      <Loader2 className="animate-spin h-5 w-5 mr-2" />
                      <span className="text-sm font-medium">Streaming...</span>
                    </div>
                  )}
                </div>
                <div className="prose prose-lg max-w-none text-gray-800 leading-relaxed">
                  {streamingAnswer}
                  {loading && <span className="inline-block w-2 h-5 bg-indigo-600 animate-pulse ml-1"></span>}
                </div>
              </div>
            )}

            {/* Final Response with Citations */}
            {response && !loading && (
              <div className="space-y-6">
                {/* Metadata Cards */}
                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-xl p-6 border border-indigo-100 shadow-md">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm font-medium text-gray-600 mb-1">Confidence Score</p>
                        <p className={`text-3xl font-bold ${getConfidenceColor(response.confidence)}`}>
                          {(response.confidence * 100).toFixed(0)}%
                        </p>
                      </div>
                      <CheckCircle2 className={`h-12 w-12 ${getConfidenceColor(response.confidence)} opacity-20`} />
                    </div>
                  </div>

                  <div className="bg-gradient-to-br from-purple-50 to-pink-50 rounded-xl p-6 border border-purple-100 shadow-md">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm font-medium text-gray-600 mb-1">Sources Used</p>
                        <p className="text-3xl font-bold text-purple-600">
                          {response.sources_used?.length || 0}
                        </p>
                      </div>
                      <FileText className="h-12 w-12 text-purple-600 opacity-20" />
                    </div>
                  </div>
                </div>

                {/* Citations */}
                {response.citations && response.citations.length > 0 && (
                  <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-xl border border-gray-100 p-8">
                    <h3 className="text-xl font-bold text-gray-900 mb-6 flex items-center">
                      <MapPin className="h-6 w-6 mr-3 text-indigo-600" />
                      Citations ({response.citations.length})
                    </h3>
                    <div className="space-y-4">
                      {response.citations.map((citation, idx) => (
                        <div
                          key={idx}
                          className="border-l-4 border-indigo-500 bg-gradient-to-r from-indigo-50 to-transparent rounded-r-lg p-5 hover:shadow-md transition-shadow duration-200"
                        >
                          <div className="flex items-start justify-between mb-2">
                            <div className="flex-1 pr-4">
                              <div className="flex items-center space-x-3">
                                <h4 className="font-semibold text-gray-900">
                                  {citation.paper_title}
                                </h4>
                                {citation.source_index && (
                                  <span className="text-xs bg-indigo-100 text-indigo-700 px-2 py-0.5 rounded-full font-medium">Source {citation.source_index}</span>
                                )}
                              </div>
                              {citation.paper_filename && (
                                <p className="text-xs text-gray-500 mt-1">{citation.paper_filename}</p>
                              )}
                            </div>
                            <span className={`px-3 py-1 rounded-full text-xs font-semibold ${getConfidenceBadge(citation.relevance_score)}`}>
                              {(citation.relevance_score * 100).toFixed(0)}% match
                            </span>
                          </div>
                          <div className="flex items-center text-sm text-gray-600 space-x-4">
                            <span className="flex items-center">
                              <BookOpen className="h-4 w-4 mr-1 text-indigo-500" />
                              {citation.section}
                            </span>
                            <span className="flex items-center">
                              <FileText className="h-4 w-4 mr-1 text-indigo-500" />
                              Page {citation.page}
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>

      <style jsx>{`
        .custom-scrollbar::-webkit-scrollbar {
          width: 6px;
        }
        .custom-scrollbar::-webkit-scrollbar-track {
          background: #f1f1f1;
          border-radius: 10px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: #c7d2fe;
          border-radius: 10px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background: #a5b4fc;
        }
        .slider-thumb::-webkit-slider-thumb {
          appearance: none;
          width: 20px;
          height: 20px;
          border-radius: 50%;
          background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%);
          cursor: pointer;
          box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        }
        .slider-thumb::-moz-range-thumb {
          width: 20px;
          height: 20px;
          border-radius: 50%;
          background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%);
          cursor: pointer;
          border: none;
          box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        }
        .line-clamp-2 {
          display: -webkit-box;
          -webkit-line-clamp: 2;
          -webkit-box-orient: vertical;
          overflow: hidden;
        }
      `}</style>
    </div>
  )
}
