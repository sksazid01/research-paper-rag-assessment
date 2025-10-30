'use client'

import { useEffect, useState } from 'react'
import axios from 'axios'
import { FileText, Loader2, X } from 'lucide-react'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface Paper {
  id: number
  title: string
  filename: string
  pages: number
}

interface PapersSidebarProps {
  refreshTrigger?: number
  onPaperClick?: (paperId: number) => void
}

export function PapersSidebar({ refreshTrigger = 0, onPaperClick }: PapersSidebarProps) {
  const [papers, setPapers] = useState<Paper[]>([])
  const [loading, setLoading] = useState(true)
  const [isOpen, setIsOpen] = useState(true)

  useEffect(() => {
    fetchPapers()
  }, [refreshTrigger])

  const fetchPapers = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/papers`)
      setPapers(response.data.papers || [])
    } catch (err) {
      console.error('Failed to load papers', err)
    } finally {
      setLoading(false)
    }
  }

  if (!isOpen) {
    return (
      <button
        onClick={() => setIsOpen(true)}
        className="fixed left-0 top-1/2 transform -translate-y-1/2 bg-gradient-to-r from-blue-600 to-indigo-600 shadow-xl rounded-r-xl p-3 border-r border-t border-b border-blue-700 hover:from-blue-700 hover:to-indigo-700 transition-all z-50"
      >
        <FileText className="w-5 h-5 text-white" />
      </button>
    )
  }

  return (
    <div className="fixed left-0 top-0 h-full w-80 bg-gradient-to-b from-white to-slate-50 border-r border-gray-200 shadow-2xl z-40 overflow-hidden flex flex-col">
      {/* Header */}
      <div className="p-5 border-b border-gray-200 flex items-center justify-between bg-gradient-to-r from-blue-600 to-indigo-600">
        <div className="flex items-center space-x-3">
          <div className="bg-white/20 backdrop-blur-sm p-2 rounded-lg">
            <FileText className="w-5 h-5 text-white" />
          </div>
          <h3 className="font-bold text-white text-lg">My Papers</h3>
          <span className="px-3 py-1 bg-white/90 text-blue-700 rounded-full text-xs font-bold shadow-lg">
            {papers.length}
          </span>
        </div>
        <button
          onClick={() => setIsOpen(false)}
          className="p-1.5 hover:bg-white/20 rounded-lg transition-colors"
        >
          <X className="w-5 h-5 text-white" />
        </button>
      </div>

      {/* Papers List */}
      <div className="flex-1 overflow-y-auto custom-scrollbar">
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
          </div>
        ) : papers.length === 0 ? (
          <div className="p-8 text-center">
            <div className="bg-gray-100 rounded-full w-20 h-20 flex items-center justify-center mx-auto mb-4">
              <FileText className="w-10 h-10 text-gray-400" />
            </div>
            <p className="text-sm text-gray-600 font-semibold">No papers uploaded yet</p>
            <p className="text-xs text-gray-500 mt-2">Upload papers to see them here</p>
          </div>
        ) : (
          <div className="p-4 space-y-3">
            {papers.map((paper, index) => (
              <button
                key={paper.id}
                onClick={() => onPaperClick?.(paper.id)}
                className="w-full text-left p-4 rounded-xl border-2 border-gray-200 hover:border-blue-400 hover:bg-blue-50 transition-all group shadow-sm hover:shadow-md"
              >
                <div className="flex items-start space-x-3">
                  <div className="bg-blue-100 group-hover:bg-blue-200 p-2 rounded-lg transition-colors">
                    <FileText className="w-5 h-5 text-blue-600" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-bold text-gray-900 truncate group-hover:text-blue-900 leading-tight">
                      {paper.title || paper.filename}
                    </p>
                    <div className="flex flex-col space-y-1 mt-2">
                      <span className="text-xs text-gray-600 font-medium bg-gray-100 px-2 py-1 rounded w-fit">
                        {paper.filename}
                      </span>
                      <span className="text-xs text-gray-600 font-medium">
                        {paper.pages} pages
                      </span>
                    </div>
                  </div>
                </div>
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="p-4 border-t border-gray-300 bg-gradient-to-r from-gray-100 to-slate-100">
        <p className="text-xs text-gray-600 text-center font-medium">
          Click on a paper to view details
        </p>
      </div>
    </div>
  )
}
