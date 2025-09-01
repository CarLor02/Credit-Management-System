// 文件图标工具函数

export interface FileIconInfo {
  icon: string;
  color: string;
  bg: string;
}

/**
 * 根据文件类型获取图标信息
 * @param type 文件类型，如 'pdf', 'excel', 'word', 'image', 'markdown', 'text'
 * @returns 包含图标类名、颜色和背景色的对象
 */
export const getFileIconByType = (type: string): FileIconInfo => {
  switch (type) {
    case 'pdf':
      return { icon: 'ri-file-pdf-line', color: 'text-red-600', bg: 'bg-red-100' };
    case 'excel':
      return { icon: 'ri-file-excel-line', color: 'text-green-600', bg: 'bg-green-100' };
    case 'word':
      return { icon: 'ri-file-word-line', color: 'text-blue-600', bg: 'bg-blue-100' };
    case 'image':
      return { icon: 'ri-image-line', color: 'text-purple-600', bg: 'bg-purple-100' };
    case 'markdown':
      return { icon: 'ri-markdown-line', color: 'text-blue-600', bg: 'bg-blue-100' };
    case 'text':
      return { icon: 'ri-file-text-line', color: 'text-gray-600', bg: 'bg-gray-100' };
    default:
      return { icon: 'ri-file-line', color: 'text-gray-600', bg: 'bg-gray-100' };
  }
};

/**
 * 根据文件名（扩展名）获取图标信息
 * @param fileName 文件名，如 'document.pdf'
 * @returns 包含图标类名、颜色和背景色的对象
 */
export const getFileIconByFileName = (fileName: string): FileIconInfo => {
  const extension = fileName.split('.').pop()?.toLowerCase();

  switch (extension) {
    case 'pdf':
      return { icon: 'ri-file-pdf-line', color: 'text-red-600', bg: 'bg-red-100' };
    case 'xlsx':
    case 'xls':
      return { icon: 'ri-file-excel-line', color: 'text-green-600', bg: 'bg-green-100' };
    case 'jpg':
    case 'jpeg':
    case 'png':
    case 'gif':
    case 'bmp':
    case 'webp':
      return { icon: 'ri-image-line', color: 'text-purple-600', bg: 'bg-purple-100' };
    case 'md':
    case 'markdown':
      return { icon: 'ri-markdown-line', color: 'text-blue-600', bg: 'bg-blue-100' };
    case 'txt':
      return { icon: 'ri-file-text-line', color: 'text-gray-600', bg: 'bg-gray-100' };
    case 'doc':
    case 'docx':
      return { icon: 'ri-file-word-line', color: 'text-blue-600', bg: 'bg-blue-100' };
    default:
      return { icon: 'ri-file-line', color: 'text-gray-600', bg: 'bg-gray-100' };
  }
};
