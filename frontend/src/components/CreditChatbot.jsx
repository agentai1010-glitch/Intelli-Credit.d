import { useState, useRef, useEffect } from 'react';
import { Send, MessageSquare, Loader2, AlertCircle, ChevronRight } from 'lucide-react';
import { askChatbot } from '../api';

// ── Icon helpers ────────────────────────────────────────────────────────────
const SOURCE_META = {
    'Annual Report': { icon: '📄', color: '#38bdf8' },
    'GST Analysis': { icon: '📊', color: '#fb923c' },
    'Credit Score Data': { icon: '🎯', color: '#34d399' },
    'Annual Report + CAM PDF': { icon: '📄', color: '#38bdf8' },
    'CAM PDF': { icon: '📋', color: '#a78bfa' },
};
const CONF_COLORS = { HIGH: '#22c55e', MEDIUM: '#f59e0b', LOW: '#ef4444' };

const STARTERS = [
    'Why was the GST score 0.58?',
    'What is the revenue trend?',
    'How can the score improve?',
    'What did the auditor say?',
];

const DEFAULT_DOC_ID = 'pi-cmmjo68xg04il9rqnht74lnr1';

// ── Individual bubble components ────────────────────────────────────────────
function UserBubble({ text }) {
    return (
        <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '12px' }}>
            <div style={{
                background: 'linear-gradient(135deg, #0ea5e9, #00d4ff)',
                color: '#0d1b2a',
                borderRadius: '18px 18px 4px 18px',
                padding: '10px 16px',
                maxWidth: '70%',
                fontWeight: 600,
                fontSize: '14px',
                boxShadow: '0 0 12px rgba(0,212,255,0.25)',
            }}>
                {text}
            </div>
        </div>
    );
}

function AIBubble({ answer, source, confidence, isLoading, isError }) {
    const srcMeta = SOURCE_META[source] || { icon: '🤖', color: '#94a3b8' };
    const confColor = CONF_COLORS[confidence] || '#94a3b8';

    return (
        <div style={{ display: 'flex', justifyContent: 'flex-start', marginBottom: '12px' }}>
            {/* Avatar */}
            <div style={{
                width: 32, height: 32, borderRadius: '50%',
                background: 'linear-gradient(135deg, #1e3a5f, #0ea5e9)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: 14, flexShrink: 0, marginRight: 10, marginTop: 4,
                boxShadow: '0 0 10px rgba(14,165,233,0.3)',
            }}>
                🤖
            </div>

            <div style={{
                background: 'rgba(255,255,255,0.04)',
                border: '1px solid rgba(255,255,255,0.08)',
                borderRadius: '4px 18px 18px 18px',
                padding: '12px 16px',
                maxWidth: '72%',
                backdropFilter: 'blur(8px)',
            }}>
                {isLoading ? (
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: '#94a3b8' }}>
                        <Loader2 size={14} style={{ animation: 'spin 1s linear infinite' }} />
                        <span style={{ fontSize: 13, fontStyle: 'italic' }}>Analyzing document context…</span>
                    </div>
                ) : isError ? (
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: '#ef4444' }}>
                        <AlertCircle size={14} />
                        <span style={{ fontSize: 13 }}>Unable to fetch answer. Please try again.</span>
                    </div>
                ) : (
                    <>
                        {/* Answer text */}
                        <p style={{ color: '#e2e8f0', fontSize: 14, lineHeight: 1.6, margin: 0, marginBottom: 10 }}>
                            {answer}
                        </p>
                        {/* Badges row */}
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
                            {/* Source badge */}
                            <span style={{
                                background: 'rgba(255,255,255,0.06)',
                                border: `1px solid ${srcMeta.color}44`,
                                color: srcMeta.color,
                                borderRadius: 20,
                                padding: '2px 10px',
                                fontSize: 11,
                                fontWeight: 600,
                                letterSpacing: '0.03em',
                            }}>
                                {srcMeta.icon} {source}
                            </span>
                            {/* Confidence badge */}
                            <span style={{
                                background: `${confColor}18`,
                                border: `1px solid ${confColor}55`,
                                color: confColor,
                                borderRadius: 20,
                                padding: '2px 10px',
                                fontSize: 11,
                                fontWeight: 700,
                            }}>
                                {confidence} confidence
                            </span>
                        </div>
                    </>
                )}
            </div>
        </div>
    );
}

/* ─────────────────────────────────────────────────────────────────────────── */
export default function CreditChatbot({ docId, creditContext }) {
    const [messages, setMessages] = useState([]);   // [{role:'user'|'ai', ...data}]
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const bottomRef = useRef(null);
    const inputRef = useRef(null);

    const effectiveDocId = docId || DEFAULT_DOC_ID;
    const effectiveCtx = creditContext || {};

    // Auto-scroll to latest message
    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    const sendQuestion = async (question) => {
        const q = question.trim();
        if (!q || loading) return;

        setInput('');
        setLoading(true);

        // 1. Append user bubble + placeholder AI bubble
        const newId = Date.now();
        setMessages(prev => [
            ...prev,
            { id: `u_${newId}`, role: 'user', text: q },
            { id: `a_${newId}`, role: 'ai', loading: true },
        ]);

        try {
            // 2. Real API call — only triggered by explicit Send
            const data = await askChatbot(q, effectiveDocId, effectiveCtx);

            // 3. Replace loading bubble with real answer
            setMessages(prev => prev.map(m =>
                m.id === `a_${newId}`
                    ? { id: m.id, role: 'ai', answer: data.answer, source: data.source, confidence: data.confidence }
                    : m
            ));
        } catch (err) {
            console.error('[CreditChatbot] API error:', err);
            setMessages(prev => prev.map(m =>
                m.id === `a_${newId}` ? { id: m.id, role: 'ai', isError: true } : m
            ));
        } finally {
            setLoading(false);
            inputRef.current?.focus();
        }
    };

    const handleKeyDown = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendQuestion(input);
        }
    };

    /* ── JSX ─────────────────────────────────────────────────────────────── */
    return (
        <div style={{
            background: 'rgba(13,27,42,0.85)',
            border: '1px solid rgba(0,212,255,0.15)',
            borderRadius: 16,
            overflow: 'hidden',
            boxShadow: '0 0 40px rgba(0,212,255,0.06)',
            backdropFilter: 'blur(12px)',
        }}>
            {/* Header */}
            <div style={{
                padding: '14px 20px',
                background: 'linear-gradient(90deg, rgba(0,212,255,0.08), transparent)',
                borderBottom: '1px solid rgba(0,212,255,0.12)',
                display: 'flex', alignItems: 'center', gap: 10,
            }}>
                <MessageSquare size={18} color="#00d4ff" />
                <span style={{ color: '#00d4ff', fontWeight: 700, fontSize: 15, letterSpacing: '0.02em' }}>
                    Credit Intelligence Assistant
                </span>
                <span style={{
                    marginLeft: 'auto',
                    background: 'rgba(0,212,255,0.1)',
                    border: '1px solid rgba(0,212,255,0.25)',
                    color: '#00d4ff',
                    borderRadius: 20,
                    padding: '2px 10px',
                    fontSize: 11,
                    fontWeight: 600,
                }}>
                    GPT-4o Mini + PageIndex
                </span>
            </div>

            {/* Chat window */}
            <div style={{
                height: 400,
                overflowY: 'auto',
                padding: '16px 20px',
                display: 'flex',
                flexDirection: 'column',
                scrollbarWidth: 'thin',
                scrollbarColor: 'rgba(0,212,255,0.2) transparent',
            }}>
                {/* Empty state */}
                {messages.length === 0 && (
                    <div style={{
                        flex: 1, display: 'flex', flexDirection: 'column',
                        alignItems: 'center', justifyContent: 'center',
                        color: '#475569', textAlign: 'center', gap: 8,
                    }}>
                        <MessageSquare size={32} style={{ opacity: 0.3 }} />
                        <p style={{ fontSize: 14, margin: 0 }}>
                            Ask questions about this credit decision.
                        </p>
                        <p style={{ fontSize: 12, margin: 0, opacity: 0.6 }}>
                            Grounded answers from the annual report &amp; credit analysis.
                        </p>
                    </div>
                )}

                {/* Message bubbles */}
                {messages.map(m => (
                    m.role === 'user'
                        ? <UserBubble key={m.id} text={m.text} />
                        : <AIBubble
                            key={m.id}
                            answer={m.answer}
                            source={m.source}
                            confidence={m.confidence}
                            isLoading={m.loading}
                            isError={m.isError}
                        />
                ))}
                <div ref={bottomRef} />
            </div>

            {/* Starter chips */}
            <div style={{
                padding: '8px 20px 0',
                display: 'flex', gap: 8, flexWrap: 'wrap',
                borderTop: '1px solid rgba(255,255,255,0.04)',
            }}>
                {STARTERS.map(s => (
                    <button
                        key={s}
                        onClick={() => { setInput(s); inputRef.current?.focus(); }}
                        disabled={loading}
                        style={{
                            background: 'rgba(0,212,255,0.07)',
                            border: '1px solid rgba(0,212,255,0.2)',
                            color: '#94a3b8',
                            borderRadius: 20,
                            padding: '4px 12px',
                            fontSize: 12,
                            cursor: loading ? 'not-allowed' : 'pointer',
                            display: 'flex', alignItems: 'center', gap: 4,
                            transition: 'all 0.2s',
                            opacity: loading ? 0.5 : 1,
                        }}
                        onMouseEnter={e => { if (!loading) { e.target.style.color = '#00d4ff'; e.target.style.borderColor = 'rgba(0,212,255,0.5)'; } }}
                        onMouseLeave={e => { e.target.style.color = '#94a3b8'; e.target.style.borderColor = 'rgba(0,212,255,0.2)'; }}
                    >
                        <ChevronRight size={10} /> {s}
                    </button>
                ))}
            </div>

            {/* Input bar */}
            <div style={{
                padding: '12px 16px 16px',
                display: 'flex', gap: 10, alignItems: 'flex-end',
            }}>
                <input
                    ref={inputRef}
                    type="text"
                    value={input}
                    onChange={e => setInput(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder="Ask about the credit decision…"
                    disabled={loading}
                    style={{
                        flex: 1,
                        background: 'rgba(255,255,255,0.05)',
                        border: '1px solid rgba(0,212,255,0.2)',
                        borderRadius: 12,
                        padding: '10px 14px',
                        color: '#e2e8f0',
                        fontSize: 14,
                        outline: 'none',
                        transition: 'border-color 0.2s',
                    }}
                    onFocus={e => { e.target.style.borderColor = 'rgba(0,212,255,0.5)'; }}
                    onBlur={e => { e.target.style.borderColor = 'rgba(0,212,255,0.2)'; }}
                />
                <button
                    onClick={() => sendQuestion(input)}
                    disabled={loading || !input.trim()}
                    style={{
                        width: 42, height: 42, borderRadius: 12,
                        background: (loading || !input.trim())
                            ? 'rgba(0,212,255,0.1)'
                            : 'linear-gradient(135deg, #0369a1, #00d4ff)',
                        border: 'none',
                        cursor: (loading || !input.trim()) ? 'not-allowed' : 'pointer',
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                        flexShrink: 0,
                        boxShadow: (!loading && input.trim()) ? '0 0 16px rgba(0,212,255,0.3)' : 'none',
                        transition: 'all 0.2s',
                        color: (loading || !input.trim()) ? '#475569' : '#0d1b2a',
                    }}
                >
                    {loading
                        ? <Loader2 size={18} style={{ animation: 'spin 1s linear infinite' }} />
                        : <Send size={18} />
                    }
                </button>
            </div>
        </div>
    );
}
