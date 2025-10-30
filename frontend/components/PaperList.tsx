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
  avg_chunk_size: number
  total_citations: number
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
      <div className="bg-gray-50 border-2 border-dashed border-gray-300 rounded-lg p-12 text-center">
        <BookOpen className="w-16 h-16 text-gray-400 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">No papers uploaded yet</h3>
        <p className="text-gray-600">Upload your first research paper to get started</p>
      </div>
    )
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      {/* Papers List */}
      <div className="lg:col-span-2 space-y-4">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">
          Indexed Papers ({papers.length})
        </h2>
        {papers.map((paper) => (
          <div
            key={paper.id}
            className={`bg-white rounded-lg shadow-md p-6 transition-all ${
              selectedPaper === paper.id ? 'ring-2 ring-primary-500' : ''
            }`}
          >
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <h3 className="text-lg font-semibold text-gray-900 mb-2">
                  {paper.title || 'Untitled Paper'}
                </h3>
                <div className="space-y-1 text-sm text-gray-600">
                  <div className="flex items-center space-x-2">
                    <User className="w-4 h-4" />
                    <span>{paper.authors || 'Unknown Author'}</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Calendar className="w-4 h-4" />
                    <span>Year: {paper.year || 'N/A'}</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <FileText className="w-4 h-4" />
                    <span>{paper.filename}</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <BookOpen className="w-4 h-4" />
                    <span>{paper.pages} pages</span>
                  </div>
                </div>
              </div>

              <div className="flex flex-col space-y-2 ml-4">
                <button
                  onClick={() => fetchStats(paper.id)}
                  className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 flex items-center space-x-2"
                >
                  <BarChart3 className="w-4 h-4" />
                  <span>Stats</span>
                </button>
                <button
                  onClick={() => deletePaper(paper.id)}
                  className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 flex items-center space-x-2"
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
        <div className="bg-white rounded-lg shadow-md p-6 sticky top-6">
          <h3 className="text-lg font-bold text-gray-900 mb-4 flex items-center space-x-2">
            <BarChart3 className="w-5 h-5" />
            <span>Paper Statistics</span>
          </h3>

          {loadingStats ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="w-6 h-6 animate-spin text-primary-600" />
            </div>
          ) : stats ? (
            <div className="space-y-4">
              <div>
                <p className="text-sm text-gray-600 mb-1">Total Chunks</p>
                <p className="text-2xl font-bold text-gray-900">{stats.total_chunks}</p>
              </div>

              <div>
                <p className="text-sm text-gray-600 mb-1">Average Chunk Size</p>
                <p className="text-2xl font-bold text-gray-900">
                  {stats.avg_chunk_size.toFixed(0)} chars
                </p>
              </div>

              <div>
                <p className="text-sm text-gray-600 mb-2">Sections Distribution</p>
                <div className="space-y-2">
                  {Object.entries(stats.sections).map(([section, count]) => (
                    <div key={section} className="flex items-center justify-between">
                      <span className="text-sm text-gray-700">{section}</span>
                      <span className="text-sm font-medium text-primary-600">{count}</span>
                    </div>
                  ))}
                </div>
              </div>

              {stats.total_citations > 0 && (
                <div>
                  <p className="text-sm text-gray-600 mb-1">Citations</p>
                  <p className="text-2xl font-bold text-gray-900">{stats.total_citations}</p>
                </div>
              )}
            </div>
          ) : (
            <p className="text-gray-500 text-center py-8">
              Select a paper to view statistics
            </p>
          )}
        </div>
      </div>
    </div>
  )
}
