import { useState } from 'react'
import { X, Maximize2 } from 'lucide-react'

export function ZoomableChart({ title, children }: { title: string; children: React.ReactNode }) {
  const [zoomed, setZoomed] = useState(false)

  return (
    <>
      <div className="bg-white p-4 rounded-lg border border-gray-200 relative group">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-medium text-gray-700">{title}</h3>
          <button
            onClick={() => setZoomed(true)}
            className="p-1 rounded hover:bg-gray-100 text-gray-400 hover:text-gray-600 opacity-0 group-hover:opacity-100 transition-opacity"
            title="Expand chart"
          >
            <Maximize2 size={14} />
          </button>
        </div>
        {children}
      </div>

      {zoomed && (
        <div className="fixed inset-0 z-50 bg-black/60 flex items-center justify-center p-8" onClick={() => setZoomed(false)}>
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-5xl h-[80vh] p-6 relative" onClick={e => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-medium text-gray-700">{title}</h3>
              <button onClick={() => setZoomed(false)} className="p-1 rounded hover:bg-gray-100 text-gray-500">
                <X size={18} />
              </button>
            </div>
            <div className="h-[calc(100%-3rem)]">
              {children}
            </div>
          </div>
        </div>
      )}
    </>
  )
}
