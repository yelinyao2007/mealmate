import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Camera, History, Loader2, Utensils } from 'lucide-react';

import api from '../api';
import ImageRecognitionResult from '../components/ImageRecognitionResult';
import ImageUpload from '../components/ImageUpload';
import IngredientInput from '../components/IngredientInput';
import { useLanguage } from '../context/LanguageContext';

export default function ImageRecognitionPage() {
  const navigate = useNavigate();
  const { t, language } = useLanguage();
  const [mode, setMode] = useState('ingredients');
  const [image, setImage] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [editingIngredients, setEditingIngredients] = useState([]);
  const [history, setHistory] = useState([]);

  const handleRecognize = async () => {
    if (!image) return;

    setLoading(true);
    setResult(null);

    try {
      const res = await api.post('/image/recognize', {
        image_data: image,
        recognition_type: mode,
      });
      setResult(res.data);
      if (res.data.ingredients) {
        setEditingIngredients(res.data.ingredients);
      }
    } catch (err) {
      alert(err.response?.data?.detail || '\u8bc6\u522b\u5931\u8d25\uff0c\u8bf7\u91cd\u8bd5');
    } finally {
      setLoading(false);
    }
  };

  const handleConfirm = () => {
    if (editingIngredients.length > 0) {
      navigate('/ai', { state: { ingredients: editingIngredients } });
    }
  };

  const loadHistory = async () => {
    try {
      const res = await api.get('/image/history');
      setHistory(res.data);
    } catch (err) {
      console.error('Failed to load history', err);
    }
  };

  return (
    <div className="max-w-2xl mx-auto px-4 py-8">
      <div className="text-center mb-8">
        <h1 className="font-heading text-4xl flex items-center justify-center gap-2">
          <Camera className="text-terracotta" size={32} />
          {'\u56fe\u50cf\u8bc6\u522b'}
        </h1>
        <p className="text-charcoal/60 mt-1">
          {'\u4e0a\u4f20\u98df\u7269\u7167\u7247\uff0cAI \u5e2e\u4f60\u8bc6\u522b\u98df\u6750\u6216\u53cd\u63a8\u83dc\u54c1\u505a\u6cd5'}
        </p>
      </div>

      <div className="flex gap-2 mb-6">
        <button
          onClick={() => {
            setMode('ingredients');
            setResult(null);
          }}
          className={`flex-1 py-3 px-4 rounded-lg font-medium flex items-center justify-center gap-2 transition-colors ${
            mode === 'ingredients'
              ? 'bg-terracotta text-white'
              : 'bg-cream text-charcoal/70 hover:bg-terracotta/10'
          }`}
        >
          <Utensils size={18} />
          {'\u8bc6\u522b\u98df\u6750'}
        </button>
        <button
          onClick={() => {
            setMode('dish');
            setResult(null);
          }}
          className={`flex-1 py-3 px-4 rounded-lg font-medium flex items-center justify-center gap-2 transition-colors ${
            mode === 'dish'
              ? 'bg-terracotta text-white'
              : 'bg-cream text-charcoal/70 hover:bg-terracotta/10'
          }`}
        >
          <Camera size={18} />
          {'\u53cd\u63a8\u505a\u6cd5'}
        </button>
      </div>

      <div className="card mb-6">
        <ImageUpload onImageChange={setImage} disabled={loading} />

        <button
          onClick={handleRecognize}
          disabled={!image || loading}
          className="btn-primary w-full mt-4 flex items-center justify-center gap-2"
        >
          {loading ? (
            <>
              <Loader2 size={18} className="animate-spin" />
              {'\u8bc6\u522b\u4e2d...'}
            </>
          ) : (
            <>
              <Camera size={18} />
              {mode === 'ingredients' ? '\u8bc6\u522b\u98df\u6750' : '\u53cd\u63a8\u505a\u6cd5'}
            </>
          )}
        </button>
      </div>

      {result && (
        <ImageRecognitionResult
          result={result}
          onConfirm={handleConfirm}
          onEdit={() => {
            if (result.ingredients) {
              setEditingIngredients(result.ingredients);
              setMode('ingredients');
            }
          }}
          loading={loading}
        />
      )}

      {editingIngredients.length > 0 && (
        <div className="card mb-6">
          <h3 className="font-heading text-lg mb-3">{'\u8bc6\u522b\u5230\u7684\u98df\u6750'}</h3>
          <IngredientInput
            ingredients={editingIngredients}
            onChange={setEditingIngredients}
          />
          <button
            onClick={handleConfirm}
            className="btn-primary w-full mt-4"
          >
            {'\u7528\u8fd9\u4e9b\u98df\u6750\u751f\u6210\u83dc\u8c31'}
          </button>
        </div>
      )}

      <div className="card">
        <h3 className="font-heading text-lg mb-3 flex items-center gap-2">
          <History size={18} />
          {'\u8bc6\u522b\u5386\u53f2'}
        </h3>
        <button onClick={loadHistory} className="btn-secondary w-full">
          {'\u52a0\u8f7d\u5386\u53f2\u8bb0\u5f55'}
        </button>

        {history.length > 0 && (
          <div className="mt-4 space-y-2">
            {history.slice(0, 5).map((item) => (
              <div key={item.id} className="p-3 bg-cream rounded-lg">
                <div className="text-sm font-medium">{item.recognition_type}</div>
                <div className="text-xs text-charcoal/50">
                  {new Date(item.created_at).toLocaleString(language === 'zh' ? 'zh-CN' : undefined)}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
