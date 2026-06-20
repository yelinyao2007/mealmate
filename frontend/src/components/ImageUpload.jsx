import { useState, useRef } from 'react';
import { Upload, X, Image as ImageIcon, Loader2 } from 'lucide-react';

export default function ImageUpload({ onImageChange, disabled = false }) {
  const [preview, setPreview] = useState(null);
  const [loading, setLoading] = useState(false);
  const fileInputRef = useRef(null);

  const handleFile = async (file) => {
    if (!file || disabled) return;
    
    if (!file.type.startsWith('image/')) {
      alert('请上传图片文件');
      return;
    }
    
    if (file.size > 5 * 1024 * 1024) {
      alert('图片不超过5MB');
      return;
    }

    setLoading(true);
    
    const reader = new FileReader();
    reader.onload = (e) => {
      setPreview(e.target.result);
      onImageChange?.(e.target.result);
      setLoading(false);
    };
    reader.onerror = () => {
      alert('读取图片失败');
      setLoading(false);
    };
    reader.readAsDataURL(file);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    const file = e.dataTransfer.files[0];
    handleFile(file);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
  };

  const handleChange = (e) => {
    const file = e.target.files[0];
    handleFile(file);
  };

  const handleClear = () => {
    setPreview(null);
    onImageChange?.(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  if (preview) {
    return (
      <div className="relative">
        <img 
          src={preview} 
          alt="预览" 
          className="w-full h-48 object-cover rounded-lg"
        />
        <button
          onClick={handleClear}
          className="absolute top-2 right-2 p-1 bg-black/50 rounded-full text-white hover:bg-black/70"
        >
          <X size={16} />
        </button>
      </div>
    );
  }

  return (
    <div
      onDrop={handleDrop}
      onDragOver={handleDragOver}
      onClick={() => fileInputRef.current?.click()}
      className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
        disabled 
          ? 'border-charcoal/20 cursor-not-allowed' 
          : 'border-charcoal/30 hover:border-terracotta hover:bg-cream/50'
      }`}
    >
      <input
        ref={fileInputRef}
        type="file"
        accept="image/*"
        onChange={handleChange}
        className="hidden"
        disabled={disabled}
      />
      
      {loading ? (
        <div className="flex items-center justify-center gap-2 text-charcoal/50">
          <Loader2 size={24} className="animate-spin" />
          <span>处理中...</span>
        </div>
      ) : (
        <div className="flex flex-col items-center gap-2 text-charcoal/50">
          <ImageIcon size={32} />
          <span className="text-sm">点击或拖拽上传图片</span>
          <span className="text-xs">支持 JPEG/PNG，不超过5MB</span>
        </div>
      )}
    </div>
  );
}