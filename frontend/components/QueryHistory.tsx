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
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center space-x-3">
            <div className="bg-gradient-to-br from-blue-100 to-indigo-100 p-2 rounded-lg">
              <Clock className="w-6 h-6 text-blue-600" />
            </div>
            <h2 className="text-2xl font-bold text-gray-900">Query History</h2>
          </div>
          <select
            value={limit}
            onChange={(e) => setLimit(parseInt(e.target.value))}
            className="px-4 py-2 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 font-semibold text-sm bg-white shadow-sm"
          >
            <option value={10}>Last 10</option>
            <option value={20}>Last 20</option>
            <option value={50}>Last 50</option>
            <option value={100}>Last 100</option>
          </select>
        </div>

        {history.length === 0 ? (
          <div className="bg-gradient-to-br from-gray-50 to-blue-50 border-2 border-dashed border-gray-300 rounded-2xl p-16 text-center">
            <div className="bg-white rounded-full w-24 h-24 flex items-center justify-center mx-auto mb-6 shadow-lg">
              <Clock className="w-12 h-12 text-blue-600" />
            </div>
            <h3 className="text-2xl font-bold text-gray-900 mb-3">No query history yet</h3>
            <p className="text-gray-600 text-lg">Start querying papers to see your history here</p>
          </div>
        ) : (
          <div className="space-y-3">
            {history.map((item, index) => (
              <div key={item.id} className="bg-white rounded-2xl shadow-lg border border-gray-100 p-6 hover:shadow-xl transition-all">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-start space-x-3 mb-3">
                      <span className="bg-blue-600 text-white px-2.5 py-1 rounded-lg text-xs font-bold">
                        #{history.length - index}
                      </span>
                      <p className="font-semibold text-gray-900 text-lg flex-1">{item.question}</p>
                    </div>
                    <div className="flex items-center flex-wrap gap-3 text-sm">
                      <span className="flex items-center space-x-1.5 bg-gray-100 px-3 py-1.5 rounded-lg">
                        <Clock className="w-4 h-4 text-blue-600" />
                        <span className="font-medium text-gray-700">{formatDate(item.created_at)}</span>
                      </span>
                      <span className="bg-green-100 text-green-700 px-3 py-1.5 rounded-lg font-semibold">
                        {item.response_time_ms}ms
                      </span>
                      <span className="bg-blue-100 text-blue-700 px-3 py-1.5 rounded-lg font-semibold">
                        {(parseFloat(item.confidence) * 100).toFixed(0)}% Confidence
                      </span>
                    </div>
                    {item.papers_used && item.papers_used.length > 0 && (
                      <div className="mt-3 flex flex-wrap gap-2">
                        {item.papers_used.map((paper, idx) => (
                          <span
                            key={idx}
                            className="px-3 py-1 bg-gradient-to-r from-purple-50 to-pink-50 border border-purple-200 text-purple-700 rounded-full text-xs font-semibold"
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
        <div className="bg-gradient-to-br from-white to-orange-50/30 rounded-2xl shadow-xl border border-orange-100 p-6 sticky top-6">
          <h3 className="text-lg font-bold text-gray-900 mb-6 flex items-center space-x-3">
            <div className="bg-gradient-to-br from-orange-100 to-red-100 p-2 rounded-lg">
              <TrendingUp className="w-5 h-5 text-orange-600" />
            </div>
            <span>Popular Topics</span>
          </h3>

          {popularTopics.length === 0 ? (
            <div className="text-center py-8">
              <div className="bg-gray-100 rounded-full w-16 h-16 flex items-center justify-center mx-auto mb-4">
                <TrendingUp className="w-8 h-8 text-gray-400" />
              </div>
              <p className="text-gray-500 font-medium">No topics yet</p>
            </div>
          ) : (
            <div className="space-y-4">
              {popularTopics.map((topic, index) => (
                <div key={index} className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-bold text-gray-900">{topic.keyword}</span>
                    <span className="bg-orange-100 text-orange-700 px-2.5 py-1 rounded-full text-xs font-bold">
                      {topic.count}
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2.5">
                    <div
                      className="bg-gradient-to-r from-orange-500 to-red-500 h-2.5 rounded-full transition-all"
                      style={{
                        width: `${Math.min((topic.count / Math.max(...popularTopics.map(t => t.count))) * 100, 100)}%`,
                      }}
                    ></div>
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
