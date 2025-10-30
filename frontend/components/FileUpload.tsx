'use client'

import { useState } from 'react'
import axios from 'axios'
import { Upload, Check, AlertCircle } from 'lucide-react'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface FileUploadProps {
  onUploadSuccess?: () => void
}

export function FileUpload({ onUploadSuccess }: FileUploadProps) {
  const [files, setFiles] = useState<FileList | null>(null)
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFiles(e.target.files)
    setError(null)
    setSuccess(null)
  }

  const handleUpload = async () => {
    if (!files || files.length === 0) {
      setError('Please select at least one PDF file')
      return
    }

    setUploading(true)
    setError(null)
    setSuccess(null)

    const formData = new FormData()
    Array.from(files).forEach((file) => {
      formData.append('files', file)
    })

    try {
      const response = await axios.post(`${API_URL}/api/papers/upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      })

      setSuccess(`Successfully uploaded ${files.length} paper(s)!`)
      setFiles(null)
      
      // Reset file input
      const fileInput = document.getElementById('file-upload') as HTMLInputElement
      if (fileInput) fileInput.value = ''

      if (onUploadSuccess) {
        onUploadSuccess()
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to upload papers. Please try again.')
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="max-w-3xl mx-auto">
      <div className="bg-white rounded-2xl shadow-xl border border-gray-100 p-8">
        <div className="flex items-center space-x-3 mb-4">
          <div className="bg-gradient-to-br from-purple-100 to-pink-100 p-2 rounded-lg">
            <Upload className="w-6 h-6 text-purple-600" />
          </div>
          <h2 className="text-2xl font-bold text-gray-900">Upload Research Papers</h2>
        </div>
        <p className="text-gray-600 mb-6 leading-relaxed">
          Upload PDF research papers to index them in the RAG system. Papers will be processed, chunked, and vectorized for semantic search.
        </p>

        {/* File Upload Area */}
        <div className="border-3 border-dashed border-gray-300 rounded-2xl p-12 text-center hover:border-blue-400 hover:bg-blue-50/30 transition-all bg-gradient-to-br from-gray-50 to-slate-50">
          <div className="bg-white rounded-full w-20 h-20 flex items-center justify-center mx-auto mb-4 shadow-lg">
            <Upload className="w-10 h-10 text-blue-600" />
          </div>
          <label htmlFor="file-upload" className="cursor-pointer">
            <span className="text-blue-600 hover:text-blue-700 font-bold text-lg">
              Click to upload
            </span>
            <span className="text-gray-700 text-lg"> or drag and drop</span>
            <p className="text-sm text-gray-500 mt-3 font-medium">PDF files only • Max 10MB per file</p>
          </label>
          <input
            id="file-upload"
            type="file"
            multiple
            accept=".pdf"
            onChange={handleFileChange}
            className="hidden"
          />
        </div>

        {/* Selected Files */}
        {files && files.length > 0 && (
          <div className="mt-6 space-y-3">
            <p className="font-semibold text-gray-800 flex items-center space-x-2">
              <span className="bg-blue-100 text-blue-700 px-2 py-1 rounded-full text-xs font-bold">{files.length}</span>
              <span>Selected Files</span>
            </p>
            {Array.from(files).map((file, index) => (
              <div key={index} className="flex items-center justify-between bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 p-4 rounded-xl hover:shadow-md transition-all">
                <span className="text-sm text-gray-800 font-medium flex items-center space-x-2">
                  <span className="bg-blue-600 text-white w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold">{index + 1}</span>
                  <span>{file.name}</span>
                </span>
                <span className="text-xs text-gray-600 bg-white px-3 py-1 rounded-full font-semibold">{(file.size / 1024 / 1024).toFixed(2)} MB</span>
              </div>
            ))}
          </div>
        )}

        {/* Upload Button */}
        <button
          onClick={handleUpload}
          disabled={!files || files.length === 0 || uploading}
          className={`
            w-full mt-6 px-6 py-4 rounded-xl font-semibold flex items-center justify-center space-x-2 transition-all transform
            ${!files || files.length === 0 || uploading
              ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
              : 'bg-gradient-to-r from-purple-600 to-pink-600 text-white hover:from-purple-700 hover:to-pink-700 shadow-lg hover:shadow-xl hover:scale-[1.02] active:scale-[0.98]'
            }
          `}
        >
          {uploading ? (
            <>
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-white"></div>
              <span className="text-lg">Uploading & Processing...</span>
            </>
          ) : (
            <>
              <Upload className="w-6 h-6" />
              <span className="text-lg">Upload Papers</span>
            </>
          )}
        </button>

        {/* Success Message */}
        {success && (
          <div className="mt-4 p-5 bg-gradient-to-r from-green-50 to-emerald-50 border-2 border-green-300 rounded-xl flex items-start space-x-3 shadow-md">
            <div className="bg-green-500 rounded-full p-1">
              <Check className="w-5 h-5 text-white" />
            </div>
            <div>
              <p className="font-bold text-green-900 text-lg">Success!</p>
              <p className="text-sm text-green-800 mt-1 font-medium">{success}</p>
            </div>
          </div>
        )}

        {/* Error Message */}
        {error && (
          <div className="mt-4 p-5 bg-gradient-to-r from-red-50 to-pink-50 border-2 border-red-300 rounded-xl flex items-start space-x-3 shadow-md">
            <div className="bg-red-500 rounded-full p-1">
              <AlertCircle className="w-5 h-5 text-white" />
            </div>
            <div>
              <p className="font-bold text-red-900 text-lg">Error</p>
              <p className="text-sm text-red-800 mt-1 font-medium">{error}</p>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
