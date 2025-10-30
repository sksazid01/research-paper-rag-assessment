'use client'

import { useEffect, useState } from 'react'
import axios from 'axios'
import { Clock, TrendingUp, Loader2 } from 'lucide-react'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface QueryHistoryItem {
  id: number
  question: string
  response_time_ms: number
  confidence: string
  created_at: string
  papers_used: string[]
}

interface PopularTopic {
  keyword: string
  count: number
}

export function QueryHistory() {
  const [history, setHistory] = useState<QueryHistoryItem[]>([])
  const [popularTopics, setPopularTopics] = useState<PopularTopic[]>([])
  const [loading, setLoading] = useState(true)
  const [limit, setLimit] = useState(20)

  useEffect(() => {
    fetchData()
  }, [limit])

  const fetchData = async () => {
    setLoading(true)
    try {
      const [historyRes, topicsRes] = await Promise.all([
        axios.get(`${API_URL}/api/queries/history?limit=${limit}`),
        axios.get(`${API_URL}/api/analytics/popular`),
      ])
      setHistory(historyRes.data.queries || [])
      setPopularTopics(topicsRes.data.topics || [])
    } catch (err) {
      console.error('Failed to load query data', err)
    } finally {
      setLoading(false)
    }
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleString()
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="w-8 h-8 animate-spin text-primary-600" />
      </div>
    )
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      {/* Query History */}
      <div className="lg:col-span-2 space-y-4">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-2xl font-bold text-gray-900">Query History</h2>
          <select
            value={limit}
            onChange={(e) => setLimit(parseInt(e.target.value))}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
          >
            <option value={10}>Last 10</option>
            <option value={20}>Last 20</option>
            <option value={50}>Last 50</option>
            <option value={100}>Last 100</option>
          </select>
        </div>

        {history.length === 0 ? (
          <div className="bg-gray-50 border-2 border-dashed border-gray-300 rounded-lg p-12 text-center">
            <Clock className="w-16 h-16 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No query history yet</h3>
            <p className="text-gray-600">Start querying papers to see your history here</p>
          </div>
        ) : (
          <div className="space-y-3">
            {history.map((item) => (
              <div key={item.id} className="bg-white rounded-lg shadow-md p-6">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <p className="font-medium text-gray-900 mb-2">{item.question}</p>
                    <div className="flex items-center space-x-4 text-sm text-gray-600">
                      <span className="flex items-center space-x-1">
                        <Clock className="w-4 h-4" />
                        <span>{formatDate(item.created_at)}</span>
                      </span>
                      <span>Response: {item.response_time_ms}ms</span>
                      <span>Confidence: {(parseFloat(item.confidence) * 100).toFixed(0)}%</span>
                    </div>
                    {item.papers_used && item.papers_used.length > 0 && (
                      <div className="mt-2 flex flex-wrap gap-2">
                        {item.papers_used.map((paper, idx) => (
                          <span
                            key={idx}
                            className="px-2 py-1 bg-primary-50 text-primary-700 rounded text-xs"
                          >
                            {paper}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Popular Topics */}
      <div className="lg:col-span-1">
        <div className="bg-white rounded-lg shadow-md p-6 sticky top-6">
          <h3 className="text-lg font-bold text-gray-900 mb-4 flex items-center space-x-2">
            <TrendingUp className="w-5 h-5" />
            <span>Popular Topics</span>
          </h3>

          {popularTopics.length === 0 ? (
            <p className="text-gray-500 text-center py-4">No topics yet</p>
          ) : (
            <div className="space-y-3">
              {popularTopics.map((topic, index) => (
                <div key={index} className="flex items-center justify-between">
                  <span className="text-sm font-medium text-gray-700">{topic.keyword}</span>
                  <div className="flex items-center space-x-2">
                    <div className="w-20 bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-primary-600 h-2 rounded-full"
                        style={{
                          width: `${Math.min((topic.count / Math.max(...popularTopics.map(t => t.count))) * 100, 100)}%`,
                        }}
                      ></div>
                    </div>
                    <span className="text-sm text-gray-600 w-8 text-right">{topic.count}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
