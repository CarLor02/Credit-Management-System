
'use client';

import { useState, useEffect } from 'react';
import { projectService } from '@/services/projectService';

interface CreateProjectModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: () => void;
  editData?: {
    id: number;
    name: string;
    type: string;
    description: string;
    category: string;
    priority: string;
  } | null;
}

export default function CreateProjectModal({ isOpen, onClose, onSuccess, editData }: CreateProjectModalProps) {
  const [formData, setFormData] = useState({
    name: '',
    type: 'enterprise',
    description: '',
    category: '',
    priority: 'medium'
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (editData) {
      setFormData({
        name: editData.name,
        type: editData.type,
        description: editData.description,
        category: editData.category,
        priority: editData.priority
      });
    } else {
      setFormData({
        name: '',
        type: 'enterprise',
        description: '',
        category: '',
        priority: 'medium'
      });
    }
  }, [editData, isOpen]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      if (editData) {
        // 更新项目逻辑
        const response = await projectService.updateProject(editData.id, {
          name: formData.name,
          description: formData.description,
          category: formData.category,
          priority: formData.priority as 'low' | 'medium' | 'high',
          // 注意：type字段在后端模型中是不可变的，所以不包含在更新数据中
        });

        if (response.success) {
          onClose();
          if (onSuccess) {
            onSuccess();
          }
        } else {
          setError(response.error || '更新项目失败');
        }
      } else {
        // 创建新项目
        const response = await projectService.createProject({
          name: formData.name,
          type: formData.type as 'enterprise' | 'individual',
          description: formData.description
        });

        if (response.success) {
          onClose();
          if (onSuccess) {
            onSuccess();
          }
        } else {
          setError(response.error || '创建项目失败');
        }
      }
    } catch (err) {
      setError('网络错误，请稍后重试');
      console.error('Submit error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl max-w-md w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-semibold text-gray-800">
              {editData ? '编辑征信项目' : '新建征信项目'}
            </h2>
            <button
              onClick={onClose}
              className="w-8 h-8 flex items-center justify-center rounded-lg hover:bg-gray-100 transition-colors"
            >
              <i className="ri-close-line text-gray-600"></i>
            </button>
          </div>

          {/* 错误提示 */}
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-3 mb-4">
              <div className="flex items-center">
                <i className="ri-error-warning-line text-red-600 mr-2"></i>
                <span className="text-red-800 text-sm">{error}</span>
              </div>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                项目名称 *
              </label>
              <input
                type="text"
                name="name"
                value={formData.name}
                onChange={handleInputChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="请输入项目名称"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                征信类型 *
              </label>
              <div className="grid grid-cols-2 gap-3">
                <label className={`flex items-center p-3 border rounded-lg transition-colors ${editData ? 'bg-gray-100 cursor-not-allowed' : 'cursor-pointer hover:bg-gray-50'}`}>
                  <input
                    type="radio"
                    name="type"
                    value="enterprise"
                    checked={formData.type === 'enterprise'}
                    onChange={handleInputChange}
                    className="mr-3"
                    disabled={!!editData}
                  />
                  <div className="flex items-center">
                    <i className="ri-building-line text-blue-600 mr-2"></i>
                    <span className="text-sm font-medium">企业征信</span>
                  </div>
                </label>
                <label className={`flex items-center p-3 border rounded-lg transition-colors ${editData ? 'bg-gray-100 cursor-not-allowed' : 'cursor-pointer hover:bg-gray-50'}`}>
                  <input
                    type="radio"
                    name="type"
                    value="individual"
                    checked={formData.type === 'individual'}
                    onChange={handleInputChange}
                    className="mr-3"
                    disabled={!!editData}
                  />
                  <div className="flex items-center">
                    <i className="ri-user-line text-purple-600 mr-2"></i>
                    <span className="text-sm font-medium">个人征信</span>
                  </div>
                </label>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                行业分类
              </label>
              <select
                name="category"
                value={formData.category}
                onChange={handleInputChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 pr-8"
              >
                <option value="">请选择行业分类</option>
                <option value="technology">科技互联网</option>
                <option value="finance">金融服务</option>
                <option value="manufacturing">制造业</option>
                <option value="retail">零售贸易</option>
                <option value="healthcare">医疗健康</option>
                <option value="education">教育培训</option>
                <option value="other">其他</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                优先级
              </label>
              <select
                name="priority"
                value={formData.priority}
                onChange={handleInputChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 pr-8"
              >
                <option value="low">低优先级</option>
                <option value="medium">中优先级</option>
                <option value="high">高优先级</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                项目描述
              </label>
              <textarea
                name="description"
                value={formData.description}
                onChange={handleInputChange}
                rows={3}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                placeholder="请输入项目描述（可选）"
                maxLength={500}
              />
              <div className="text-xs text-gray-500 mt-1">
                {formData.description.length}/500
              </div>
            </div>

            <div className="flex space-x-3 pt-4">
              <button
                type="button"
                onClick={onClose}
                className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors whitespace-nowrap"
              >
                取消
              </button>
              <button
                type="submit"
                disabled={loading}
                className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors whitespace-nowrap disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? (
                  <div className="flex items-center justify-center">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    {editData ? '保存中...' : '创建中...'}
                  </div>
                ) : (
                  editData ? '保存修改' : '创建项目'
                )}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}