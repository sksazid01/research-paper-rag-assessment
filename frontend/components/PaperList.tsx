'use client'

import { useEffect, useState } from 'react'
import axios from 'axios'
import { BookOpen, Trash2, BarChart3, Loader2, Calendar, User, FileText } from 'lucide-react'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface Paper {
  id: number
  title: string
  authors: string
  year: string
  filename: string
  pages: number
  created_at: string
}

interface PaperStats {
  total_chunks: number
  sections: Record<string, number>
  avg_chunk_length: number
  total_citations?: number
}

export function PaperList() {
  const [papers, setPapers] = useState<Paper[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedPaper, setSelectedPaper] = useState<number | null>(null)
  const [stats, setStats] = useState<PaperStats | null>(null)
  const [loadingStats, setLoadingStats] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchPapers()
  }, [])

  const fetchPapers = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/papers`)
      setPapers(response.data.papers || [])
      setError(null)
    } catch (err) {
      setError('Failed to load papers')
    } finally {
      setLoading(false)
    }
  }

  const fetchStats = async (paperId: number) => {
    setLoadingStats(true)
    try {
      const response = await axios.get(`${API_URL}/api/papers/${paperId}/stats`)
      setStats(response.data)
      setSelectedPaper(paperId)
    } catch (err) {
      console.error('Failed to load stats', err)
    } finally {
      setLoadingStats(false)
    }
  }

  const deletePaper = async (paperId: number) => {
    if (!confirm('Are you sure you want to delete this paper?')) return

    try {
      await axios.delete(`${API_URL}/api/papers/${paperId}`)
      fetchPapers()
      if (selectedPaper === paperId) {
        setSelectedPaper(null)
        setStats(null)
      }
    } catch (err) {
      alert('Failed to delete paper')
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="w-8 h-8 animate-spin text-primary-600" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
        <p className="text-red-700">{error}</p>
      </div>
    )
  }

  if (papers.length === 0) {
    return (
      <div className="bg-gradient-to-br from-gray-50 to-blue-50 border-2 border-dashed border-gray-300 rounded-2xl p-16 text-center">
        <div className="bg-white rounded-full w-24 h-24 flex items-center justify-center mx-auto mb-6 shadow-lg">
          <BookOpen className="w-12 h-12 text-blue-600" />
        </div>
        <h3 className="text-2xl font-bold text-gray-900 mb-3">No papers uploaded yet</h3>
        <p className="text-gray-600 text-lg">Upload your first research paper to get started</p>
      </div>
    )
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      {/* Papers List */}
      <div className="lg:col-span-2 space-y-4">
        <div className="flex items-center space-x-3 mb-6">
          <div className="bg-gradient-to-br from-blue-100 to-indigo-100 p-2 rounded-lg">
            <BookOpen className="w-6 h-6 text-blue-600" />
          </div>
          <h2 className="text-2xl font-bold text-gray-900">
            Indexed Papers
          </h2>
          <span className="bg-blue-100 text-blue-700 px-3 py-1 rounded-full text-sm font-bold">
            {papers.length}
          </span>
        </div>
        {papers.map((paper) => (
          <div
            key={paper.id}
            className={`bg-white rounded-2xl shadow-lg border-2 p-6 transition-all hover:shadow-xl ${
              selectedPaper === paper.id ? 'border-blue-500 shadow-blue-200' : 'border-gray-100'
            }`}
          >
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <h3 className="text-xl font-bold text-gray-900 mb-3 leading-tight flex items-center space-x-2">
                  <FileText className="w-6 h-6 text-blue-600" />
                  <span>{paper.filename}</span>
                </h3>
                <div className="space-y-2 text-sm text-gray-600">
                  {paper.title && paper.title !== paper.filename && (
                    <div className="flex items-start space-x-2 bg-blue-50 px-3 py-2 rounded-lg">
                      <BookOpen className="w-4 h-4 text-blue-600 mt-0.5 flex-shrink-0" />
                      <span className="font-medium text-blue-900">{paper.title}</span>
                    </div>
                  )}
                  <div className="flex items-center space-x-2 bg-gray-50 px-3 py-1.5 rounded-lg w-fit">
                    <User className="w-4 h-4 text-blue-600" />
                    <span className="font-medium">{paper.authors || 'Unknown Author'}</span>
                  </div>
                  <div className="flex items-center space-x-3">
                    <div className="flex items-center space-x-1.5 bg-gray-50 px-3 py-1.5 rounded-lg">
                      <Calendar className="w-4 h-4 text-blue-600" />
                      <span className="font-medium">{paper.year || 'N/A'}</span>
                    </div>
                    <div className="flex items-center space-x-1.5 bg-gray-50 px-3 py-1.5 rounded-lg">
                      <BookOpen className="w-4 h-4 text-blue-600" />
                      <span className="font-medium">{paper.pages} pages</span>
                    </div>
                  </div>
                </div>
              </div>

              <div className="flex flex-col space-y-3 ml-4">
                <button
                  onClick={() => fetchStats(paper.id)}
                  className="px-5 py-2.5 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-xl hover:from-blue-700 hover:to-indigo-700 shadow-md hover:shadow-lg transition-all font-semibold flex items-center space-x-2"
                >
                  <BarChart3 className="w-4 h-4" />
                  <span>Stats</span>
                </button>
                <button
                  onClick={() => deletePaper(paper.id)}
                  className="px-5 py-2.5 bg-gradient-to-r from-red-600 to-pink-600 text-white rounded-xl hover:from-red-700 hover:to-pink-700 shadow-md hover:shadow-lg transition-all font-semibold flex items-center space-x-2"
                >
                  <Trash2 className="w-4 h-4" />
                  <span>Delete</span>
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Stats Panel */}
      <div className="lg:col-span-1">
        <div className="bg-gradient-to-br from-white to-blue-50/30 rounded-2xl shadow-xl border border-blue-100 p-6 sticky top-6">
          <h3 className="text-lg font-bold text-gray-900 mb-6 flex items-center space-x-3">
            <div className="bg-gradient-to-br from-green-100 to-emerald-100 p-2 rounded-lg">
              <BarChart3 className="w-5 h-5 text-green-600" />
            </div>
            <span>Paper Statistics</span>
          </h3>

          {loadingStats ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
            </div>
          ) : stats ? (
            <div className="space-y-5">
              <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
                <p className="text-sm text-gray-600 mb-2 font-medium">Total Chunks</p>
                <p className="text-3xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">{stats.total_chunks}</p>
              </div>

              <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
                <p className="text-sm text-gray-600 mb-2 font-medium">Average Chunk Size</p>
                <p className="text-3xl font-bold bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent">
                  {stats.avg_chunk_length || 0}
                </p>
                <p className="text-xs text-gray-500 mt-1">characters</p>
              </div>

              <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
                <p className="text-sm text-gray-600 mb-3 font-semibold">Sections Distribution</p>
                <div className="space-y-2">
                  {Object.entries(stats.sections).map(([section, count]) => (
                    <div key={section} className="flex items-center justify-between bg-gradient-to-r from-blue-50 to-indigo-50 px-3 py-2 rounded-lg">
                      <span className="text-sm text-gray-800 font-medium">{section}</span>
                      <span className="text-sm font-bold text-blue-600 bg-white px-2 py-0.5 rounded-full">{count}</span>
                    </div>
                  ))}
                </div>
              </div>

              {stats.total_citations && stats.total_citations > 0 && (
                <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
                  <p className="text-sm text-gray-600 mb-2 font-medium">Citations</p>
                  <p className="text-3xl font-bold bg-gradient-to-r from-green-600 to-emerald-600 bg-clip-text text-transparent">{stats.total_citations}</p>
                </div>
              )}
            </div>
          ) : (
            <div className="text-center py-12">
              <div className="bg-gray-100 rounded-full w-16 h-16 flex items-center justify-center mx-auto mb-4">
                <BarChart3 className="w-8 h-8 text-gray-400" />
              </div>
              <p className="text-gray-500 font-medium">
                Select a paper to view statistics
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
