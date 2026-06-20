import { ChefHat, User } from 'lucide-react';

export default function ChatBubble({ role, content }) {
  const isUser = role === 'user';
  return (
    <div className={`flex gap-3 ${isUser ? 'flex-row-reverse' : ''}`}>
      <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${isUser ? 'bg-sage/20' : 'bg-terracotta/10'}`}>
        {isUser ? <User size={16} className="text-sage" /> : <ChefHat size={16} className="text-terracotta" />}
      </div>
      <div
        className={`max-w-[80%] px-4 py-3 rounded-2xl text-sm leading-relaxed whitespace-pre-wrap ${
          isUser
            ? 'bg-sage text-white rounded-br-md'
            : 'bg-white border border-gold/20 text-charcoal rounded-bl-md'
        }`}
      >
        {content}
      </div>
    </div>
  );
}
