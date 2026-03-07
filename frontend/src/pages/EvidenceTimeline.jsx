import { useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { Search, Globe, AlertTriangle, ArrowRight, Loader2, CheckCircle } from 'lucide-react';
import { fetchEvidence, checkRegulatoryIntelligence } from '../api';
import { useAppContext } from '../context/AppContext';

export default function EvidenceTimeline() {
    const { sessionData, updateSession } = useAppContext();
    const navigate = useNavigate();
    const location = useLocation();
    const state = location.state || {};

    const defaultEntity = state.companyName || sessionData.nlpEntities?.find(e => e.type === 'ORG')?.text || 'Orbit Holdings';

    const [searchTerm, setSearchTerm] = useState(defaultEntity);
    const [query, setQuery] = useState('');
    const [isSearching, setIsSearching] = useState(false);
    const [evidence, setEvidence] = useState(sessionData.evidence || []);

    const [regulatoryScore, setRegulatoryScore] = useState(null);
    const [regulatoryFlags, setRegulatoryFlags] = useState([]);
    const [regulatorySources, setRegulatorySources] = useState([]);

    const handleSearch = async (e) => {
        e.preventDefault();
        if (!searchTerm) return;

        setIsSearching(true);
        try {
            const [evidenceData, regulatoryData] = await Promise.all([
                fetchEvidence(searchTerm, query),
                checkRegulatoryIntelligence(searchTerm)
            ]);

            setEvidence(evidenceData.results || []);
            updateSession({ evidence: evidenceData.results || [] });

            if (regulatoryData) {
                setRegulatoryScore(regulatoryData.regulatory_risk_score);
                setRegulatoryFlags([...(regulatoryData.critical_flags || []), ...(regulatoryData.warnings || [])]);
                setRegulatorySources(regulatoryData.sources_checked || []);
            }
        } catch (err) {
            console.error(err);
        } finally {
            setIsSearching(false);
        }
    };

    const handleGenerateCAM = () => {
        let finalScore = state.adjustedScore || state.baseScore || 0;
        if (regulatoryScore !== null) {
            if (regulatoryScore < 60) finalScore -= 20;
            else if (regulatoryScore < 80) finalScore -= 5;
        }

        navigate('/cam', {
            state: {
                ...state,
                regulatoryScore,
                regulatoryFlags,
                regulatorySources,
                finalScore
            }
        });
    };

    const renderScoreImpact = () => {
        if (regulatoryScore === null) return null;

        let badgeColor = "bg-green-500/10 text-green-400 border-green-500/20";
        let title = "All Sources Clean";
        let text = "No adverse regulatory findings. Score impact: 0 points.";

        if (regulatoryScore < 60) {
            badgeColor = "bg-red-500/10 text-red-400 border-red-500/20";
            title = "Critical Flags";
            text = "Critical regulatory risk detected. Score impact: -20 points applied.";
        } else if (regulatoryScore < 80) {
            badgeColor = "bg-amber-500/10 text-amber-400 border-amber-500/20";
            title = "Minor Flags Found";
            text = `${regulatoryFlags.length} findings noted. Score impact: -5 points applied.`;
        }

        const sources = ["MCA", "eCourts", "RBI", "IBBI"];

        const getSourceStatusColor = (sourceName) => {
            const flagged = regulatoryFlags.some(f => f.source === sourceName);
            if (flagged) return "bg-red-500/10 text-red-400 border-red-500/20";
            if (regulatorySources.includes(sourceName)) return "bg-green-500/10 text-green-400 border-green-500/20";
            return "bg-amber-500/10 text-amber-500 border-amber-500/20";
        };

        return (
            <div className="glass-panel p-6 mb-8 mt-6 relative z-10 transition-all duration-500 animate-in fade-in slide-in-from-bottom-4">
                <h3 className="text-xl font-bold text-slate-200 mb-4">Regulatory Score Impact</h3>
                <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
                    <div className="flex items-start gap-4 flex-1">
                        <div className={`px-4 py-2 flex items-center gap-2 rounded-lg border font-bold ${badgeColor}`}>
                            {regulatoryScore >= 80 ? <CheckCircle size={20} /> : <AlertTriangle size={20} />}
                            {title}
                        </div>
                        <div>
                            <p className="text-slate-300 font-medium">{text}</p>
                            <p className="text-sm text-slate-500 mt-1">Raw regulatory score: {regulatoryScore}/100</p>
                        </div>
                    </div>
                    <div className="flex gap-2 flex-wrap md:justify-end">
                        {sources.map(s => (
                            <span key={s} className={`text-xs font-bold px-3 py-1 rounded border gap-1 flex items-center ${getSourceStatusColor(s)}`}>
                                {s}
                            </span>
                        ))}
                    </div>
                </div>
            </div>
        );
    };

    return (
        <div className="flex flex-col gap-8 w-full max-w-5xl mx-auto py-10 animate-in fade-in slide-in-from-bottom-8 duration-700">
            <header className="flex justify-between items-end">
                <div>
                    <h1 className="text-4xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-indigo-400 tracking-tight mb-2">
                        External Intelligence Vector Search
                    </h1>
                    <p className="text-slate-400 text-lg">Gather deep web and news evidence connected via NLP entities</p>
                </div>
                <button
                    className="btn-primary flex items-center gap-2"
                    onClick={handleGenerateCAM}
                >
                    Generate Final CAM <ArrowRight size={18} />
                </button>
            </header>

            {/* Search Input Panel */}
            <form onSubmit={handleSearch} className="glass-panel p-2 flex flex-col md:flex-row gap-4 items-center relative z-10">
                <div className="flex-1 w-full bg-slate-900/50 rounded-lg flex items-center px-4 py-3 border border-slate-700/50 focus-within:border-blue-500/50 transition duration-300">
                    <Globe className="text-slate-500 mr-3" size={20} />
                    <input
                        type="text"
                        placeholder="Entity Name (e.g. Orbit Holdings)"
                        className="bg-transparent border-none outline-none w-full text-slate-200 placeholder-slate-500 font-medium"
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                    />
                </div>

                <div className="flex-1 w-full bg-slate-900/50 rounded-lg flex items-center px-4 py-3 border border-slate-700/50 focus-within:border-blue-500/50 transition duration-300">
                    <Search className="text-slate-500 mr-3" size={20} />
                    <input
                        type="text"
                        placeholder="Semantic Query (optional, e.g. 'legal default')"
                        className="bg-transparent border-none outline-none w-full text-slate-200 placeholder-slate-500"
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                    />
                </div>

                <button type="submit" className="btn-primary md:w-auto w-full flex justify-center items-center py-3 px-8 mx-2" disabled={isSearching}>
                    {isSearching ? <Loader2 className="animate-spin" size={20} /> : 'Crawl & Index'}
                </button>
            </form>

            {/* Score Impact Panel */}
            {renderScoreImpact()}

            {/* Evidence Timeline */}
            {evidence.length > 0 ? (
                <div className="relative pl-8 md:pl-0 mt-6 before:absolute before:inset-0 before:ml-5 md:before:mx-auto md:before:translate-x-0 before:h-full before:w-0.5 before:bg-gradient-to-b before:from-blue-500/50 before:via-indigo-500/20 before:to-transparent z-0">
                    {evidence.map((item, idx) => (
                        <div key={idx} className="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group mb-8">
                            {/* Timeline marker */}
                            <div className="absolute left-0 md:left-1/2 -ml-3 md:-ml-4 w-6 h-6 md:w-8 md:h-8 rounded-full bg-slate-900 border-4 border-blue-500/50 shadow-[0_0_15px_rgba(59,130,246,0.5)] z-10 group-hover:bg-blue-500 group-hover:scale-125 transition-all duration-300"></div>

                            <div className="glass-panel w-full md:w-[45%] p-6 ml-6 md:ml-0 hover:-translate-y-1 transition duration-300 shadow-xl shadow-blue-900/10">
                                <div className="flex justify-between items-start mb-3 border-b border-slate-700/30 pb-3">
                                    <span className="text-xs font-bold uppercase tracking-wider text-blue-400 bg-blue-500/10 px-3 py-1 rounded-full">{item.source || 'News Source'}</span>
                                    <span className="text-xs text-slate-500">{new Date().toLocaleDateString()}</span>
                                </div>
                                <h3 className="text-lg font-bold text-slate-200 mb-2 leading-tight">
                                    <a href={item.url} target="_blank" rel="noreferrer" className="hover:text-blue-400 transition">{item.title}</a>
                                </h3>
                                <p className="text-sm text-slate-400 line-clamp-3 mb-4">{item.content}</p>

                                {/* Risk Tags */}
                                {item.tags && item.tags.length > 0 && (
                                    <div className="flex flex-wrap gap-2">
                                        {item.tags.map(tag => (
                                            <span key={tag} className="flex items-center gap-1 text-xs font-semibold px-2 py-1 rounded bg-red-500/10 text-red-400 border border-red-500/20">
                                                <AlertTriangle size={12} /> {tag}
                                            </span>
                                        ))}
                                    </div>
                                )}
                                {item.search_distance && (
                                    <div className="mt-3 text-right">
                                        <span className="text-[10px] text-slate-500 uppercase tracking-widest font-bold">L2 Distance: {item.search_distance}</span>
                                    </div>
                                )}
                            </div>
                        </div>
                    ))}
                </div>
            ) : (
                <div className="flex flex-col items-center justify-center p-20 text-slate-500 border border-dashed border-slate-700/50 rounded-2xl glass-panel">
                    <Globe size={48} className="mb-4 opacity-20" />
                    <h3 className="text-xl">No evidence found yet.</h3>
                    <p className="text-sm mt-2">Enter an entity name and crawl sources to build a risk profile.</p>
                </div>
            )}
        </div>
    );
}
