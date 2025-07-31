'use client';

import React, { useState } from 'react';

interface PdfViewerProps {
  pdfUrl: string;
  title?: string;
  showControls?: boolean;
}

const PdfViewer: React.FC<PdfViewerProps> = ({
  pdfUrl,
  title = "PDF预览",
  showControls = true
}) => {
  const [zoom, setZoom] = useState(100);
  const [error, setError] = useState<string | null>(null);

  const handleZoomIn = () => {
    setZoom(prev => Math.min(prev + 25, 200));
  };

  const handleZoomOut = () => {
    setZoom(prev => Math.max(prev - 25, 50));
  };

  const handleResetZoom = () => {
    setZoom(100);
  };

  const handleIframeError = () => {
    setError('PDF预览加载失败，请尝试下载查看');
  };

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-full bg-gray-50 p-8">
        <div className="text-center">
          <i className="ri-file-pdf-line text-6xl text-red-400 mb-4"></i>
          <h3 className="text-lg font-medium text-gray-900 mb-2">PDF预览不可用</h3>
          <p className="text-gray-600 mb-4">{error}</p>
          <a
            href={pdfUrl}
            download
            className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            <i className="ri-download-line mr-2"></i>
            下载PDF文件
          </a>
        </div>
      </div>
    );
  }

  return (
    <div className="relative w-full h-full bg-gray-100">
      {/* 控制栏 */}
      {showControls && (
        <div className="absolute top-4 left-1/2 transform -translate-x-1/2 z-10 bg-white rounded-lg shadow-lg border border-gray-200 px-4 py-2">
          <div className="flex items-center space-x-3">
            <button
              onClick={handleZoomOut}
              disabled={zoom <= 50}
              className="p-1 rounded hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
              title="缩小"
            >
              <i className="ri-zoom-out-line text-gray-600"></i>
            </button>
            
            <span className="text-sm text-gray-600 min-w-[60px] text-center">
              {zoom}%
            </span>
            
            <button
              onClick={handleZoomIn}
              disabled={zoom >= 200}
              className="p-1 rounded hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
              title="放大"
            >
              <i className="ri-zoom-in-line text-gray-600"></i>
            </button>
            
            <div className="w-px h-4 bg-gray-300"></div>
            
            <button
              onClick={handleResetZoom}
              className="p-1 rounded hover:bg-gray-100"
              title="重置缩放"
            >
              <i className="ri-fullscreen-line text-gray-600"></i>
            </button>
          </div>
        </div>
      )}

      {/* PDF内容 */}
      <iframe
        src={`${pdfUrl}#zoom=${zoom}&navpanes=0&toolbar=1&statusbar=0&messages=0&scrollbar=1`}
        width="100%"
        height="100%"
        title={title}
        className="w-full h-full border-0"
        onError={handleIframeError}
        style={{
          transform: `scale(${zoom / 100})`,
          transformOrigin: 'top left',
          width: `${10000 / zoom}%`,
          height: `${10000 / zoom}%`
        }}
      />
    </div>
  );
};

export default PdfViewer;
