import { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { FileText, Download, Edit3, Loader2, Sparkles, MessageSquare } from 'lucide-react';
import { generateCam } from '../api';
import { useAppContext } from '../context/AppContext';
import CreditChatbot from '../components/CreditChatbot';

export default function CAMGenerator() {
    const { sessionData, updateSession } = useAppContext();
    const location = useLocation();
    const state = location.state || {};

    const [isGenerating, setIsGenerating] = useState(false);
    const [camUrl, setCamUrl] = useState(sessionData.camUrl || null);
    const [analystNotes, setAnalystNotes] = useState('');
    const [pageindexStatus, setPageindexStatus] = useState('NOT_STARTED');

    const formatCrores = (absoluteRupees) => {
        if (!absoluteRupees && absoluteRupees !== 0) return "N/A";
        const crores = absoluteRupees / 10000000;
        return `₹${crores.toFixed(2)} Cr`;
    };

    const company =
        (state.companyName || sessionData.companyName || 'Unknown Company')
        .replace(/Annual Report|Financial Statement|FY\s?\d{2}-?\d{2}|FY\d{4}|Audited Report/gi, '')
        .trim();

    const finalScore =
        state.finalScore ??
        state.adjustedScore ??
        state.baseScore ??
        ((sessionData.scoreResult?.predicted_score ? Math.round(sessionData.scoreResult.predicted_score * 100) : 0) ||
        (sessionData.features?.final_risk_score ?? 0));

    const pollStatus = async () => {
        try {
            const sid = sessionData.sessionId || 'default_session';
            const res = await fetch(`${import.meta.env.VITE_API_BASE_URL}/api/v1/pageindex/status/${sid}`);
            const data = await res.json();
            setPageindexStatus(data.status);
            if (data.status === 'COMPLETED' || data.status === 'FAILED') return true;
        } catch (e) {
            console.error("Status check failed", e);
        }
        return false;
    };

    useEffect(() => {
        let interval;
        if (pageindexStatus !== 'COMPLETED' && pageindexStatus !== 'FAILED') {
            interval = setInterval(async () => {
                const done = await pollStatus();
                if (done) clearInterval(interval);
            }, 5000);
        }
        return () => clearInterval(interval);
    }, []);

    const handleGenerate = async () => {
        setIsGenerating(true);
        setCamUrl(null);
        try {
            const payload = {
                companyName: company,
                company_name: company,
                date: new Date().toISOString().split('T')[0],
                entity_id: 'L12345MH2024PLC009999',
                features: state.computedFeatures || sessionData.features || {},
                extractedFinancials: state.extractedFinancials || sessionData.features || {},
                ml_output: sessionData.scoreResult || {},
                entity_data: sessionData.nlpEntities || [],
                evidence: sessionData.evidence || [],
                notes: analystNotes,
                user_id: sessionData?.user?.id,
                analyst_name: sessionData?.user?.user_metadata?.full_name || sessionData?.user?.email || null,
                user_email: sessionData?.user?.email || null,
                analystInputs: state.analystInputs || {},
                loanLimit: state.loanLimit || state.loan_limit,
                interestRate: state.interestRate || state.interest_rate,
                tenure: state.tenure,
                baseScore: state.baseScore,
                adjustedScore: state.adjustedScore,
                qualitativeDelta: state.qualitativeDelta,
                regulatoryScore: state.regulatoryScore,
                gstFlags: state.gstFlags,
                reconciliationScore: state.reconciliationScore,
                finalScore: state.finalScore,
                // Fix 3: SHAP values for AI Risk Insights section
                shapValues: (
                    sessionData?.explanation?.top_features ||
                    sessionData?.scoreResult?.top_features ||
                    []
                ),
                // Fix 7: PageIndex enrichment fields
                auditor_qualification: sessionData?.features?.auditor_qualification || "Unqualified",
                revenue_trend: sessionData?.features?.revenue_trend || null,
                sector_name: sessionData?.features?.sector_name || "Textile Manufacturing"
            };

            const responseBlob = await generateCam(payload);

            // Create a URL for the downloaded PDF blob with an explicit MIME type
            const blob = new Blob([responseBlob], { type: 'application/pdf' });
            const url = window.URL.createObjectURL(blob);
            setCamUrl(url);
            updateSession({ camUrl: url });
        } catch (err) {
            console.error("CAM Generation Failed:", err);
        } finally {
            setIsGenerating(false);
        }
    };

    const getStatusColor = () => {
        switch (pageindexStatus) {
            case 'COMPLETED': return 'text-emerald-400 bg-emerald-400/10 border-emerald-500/30';
            case 'PROCESSING': return 'text-blue-400 bg-blue-400/10 border-blue-500/30';
            case 'FAILED': return 'text-red-400 bg-red-400/10 border-red-500/30';
            default: return 'text-slate-500 bg-slate-500/10 border-slate-700';
        }
    };

    return (
        <div className="grid grid-cols-1 xl:grid-cols-3 gap-8 w-full max-w-[1500px] mx-auto py-10 animate-in fade-in slide-in-from-bottom-8 duration-700 lg:px-6">
            
            {/* ── Left side: Document Synthesis and Preview (takes 2/3 space) ── */}
            <div className="xl:col-span-2 flex flex-col gap-8 w-full">
                <header className="flex justify-between items-end">
                    <div>
                        <h1 className="text-4xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-emerald-400 tracking-tight mb-2">
                            Generate Final Memo
                        </h1>
                        <p className="text-slate-400 text-lg">Bundle pipeline outputs into formatted Credit Appraisal PDF</p>
                    </div>
                </header>

                {/* Analyst Insights */}
            <div className="glass-panel p-8 relative overflow-hidden group">
                <div className="absolute -right-4 -top-8 text-blue-500/10 pointer-events-none group-hover:scale-110 transition-transform duration-700">
                    <Edit3 size={150} />
                </div>

                <h2 className="text-xl font-bold text-slate-200 mb-6 flex items-center gap-2">
                    <Edit3 size={20} className="text-blue-400" />
                    Analyst Overlay Notes (Optional)
                </h2>
                <textarea
                    value={analystNotes}
                    onChange={(e) => setAnalystNotes(e.target.value)}
                    placeholder="Add human-in-the-loop qualitative insights regarding repayment capacity, specific collateral structure..."
                    className="w-full bg-slate-900/50 text-slate-200 p-4 rounded-xl border border-slate-700 w-full min-h-[150px] focus:outline-none focus:ring-2 focus:ring-blue-500/50 resize-y mb-6 z-10 relative"
                />

                <div className="flex justify-between items-center z-10 relative">
                    <div className="flex gap-4">
                        <div className="flex flex-col">
                            <span className="text-xs font-bold uppercase tracking-widest text-slate-500">Target Entity</span>
                            <span className="text-slate-300 font-medium">{company}</span>
                        </div>
                        <div className="flex flex-col">
                            <span className="text-xs font-bold uppercase tracking-widest text-slate-500">System Score</span>
                            <span className="text-slate-300 font-medium">{finalScore} / 100</span>
                        </div>
                    </div>

                    <button
                        onClick={handleGenerate}
                        disabled={isGenerating}
                        className="btn-primary flex items-center gap-3 bg-gradient-to-r from-blue-600 to-emerald-600 hover:from-blue-500 hover:to-emerald-500 border-none shadow-[0_0_20px_rgba(16,185,129,0.3)] hover:shadow-[0_0_30px_rgba(16,185,129,0.5)] px-8 py-3 rounded-full font-bold text-lg"
                    >
                        {isGenerating ? (
                            <> <Loader2 className="animate-spin" size={24} /> Compiling LLM Drafts... </>
                        ) : (
                            <> <Sparkles size={24} /> Synthesize CAM Document </>
                        )}
                    </button>
                </div>
            </div>

            {/* PDF Preview & Download Action */}
            {camUrl && (
                <div className="glass-panel p-8 flex flex-col items-center justify-center animate-in zoom-in-95 duration-500 border border-emerald-500/50 relative overflow-hidden w-full">
                    <div className="absolute inset-0 bg-emerald-500/5 group-hover:bg-emerald-500/10 transition-colors pointer-events-none"></div>

                    <div className="flex items-center gap-3 mb-6 relative z-10">
                        <div className="w-12 h-12 rounded-full bg-emerald-500/20 text-emerald-400 flex items-center justify-center shadow-[0_0_30px_rgba(16,185,129,0.3)]">
                            <FileText size={24} />
                        </div>
                        <h3 className="text-2xl font-bold text-slate-200">Live CAM Preview</h3>
                    </div>

                    <p className="text-slate-400 max-w-lg text-center mb-6 relative z-10">
                        Review the fully assembled Credit Appraisal Memo below.
                    </p>

                    {/* Interactive PDF Preview Window */}
                    <div className="w-full h-[600px] mb-8 rounded-xl overflow-hidden border-2 border-slate-700/50 shadow-2xl relative z-10 bg-slate-900/50">
                        <iframe
                            src={camUrl}
                            className="w-full h-full border-none"
                            title="Credit Memo Preview"
                        />
                    </div>

                    <a
                        href={camUrl}
                        download={`Credit_Memo_${company.replace(/\s+/g, '_')}.pdf`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="btn-primary flex items-center gap-3 bg-emerald-600 hover:bg-emerald-500 border-none shadow-[0_0_20px_rgba(16,185,129,0.4)] px-8 py-4 rounded-full font-bold text-xl relative z-10 w-64 justify-center"
                    >
                        <Download size={24} /> Download PDF
                    </a>
                </div>
            )}
            
            </div> {/* End Left Column */}

            {/* ── Right side: Credit Intelligence Chatbot (always visible, side-by-side) ── */}
            <div className="xl:col-span-1 rounded-2xl bg-[#0B1120] border border-slate-700/50 shadow-2xl flex flex-col overflow-hidden h-[calc(100vh-140px)] sticky top-24 animate-in fade-in slide-in-from-right-8 duration-700 z-10">
                {/* Chat Header */}
                <div className="bg-slate-800/80 backdrop-blur-md p-5 border-b border-slate-700/50 flex items-center gap-3 shrink-0 relative overflow-hidden">
                    <div className="absolute -right-4 -top-8 text-cyan-500/10 pointer-events-none">
                        <MessageSquare size={100} />
                    </div>
                    
                    <div className="w-12 h-12 rounded-full bg-cyan-500/20 text-cyan-400 flex items-center justify-center shadow-[0_0_20px_rgba(6,182,212,0.3)] shrink-0 z-10">
                        <MessageSquare size={24} />
                    </div>
                    <div className="z-10">
                        <h2 className="text-lg font-bold text-slate-200 leading-tight">
                            Credit Assistant
                        </h2>
                        <div className="flex items-center gap-3 mt-1.5">
                            <div className="flex items-center gap-2">
                                <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
                                <span className="text-emerald-400 text-[10px] tracking-wider uppercase font-bold">
                                    Online
                                </span>
                            </div>
                            
                            {pageindexStatus !== 'NOT_FOUND' && (
                                <div className={`px-2 py-0.5 rounded-md border text-[10px] font-bold tracking-tight flex items-center gap-1.5 transition-colors ${getStatusColor()}`}>
                                    {pageindexStatus === 'PROCESSING' && <Loader2 size={10} className="animate-spin" />}
                                    PAGEINDEX: {pageindexStatus}
                                </div>
                            )}
                        </div>
                    </div>
                </div>

                {/* Chatbot Engine Container */}
                <div className="flex-grow w-full relative">
                    <div className="absolute inset-0 p-4">
                        <CreditChatbot
                        docId={
                            sessionData?.features?.pageindex_doc_id ||
                            state?.pageIndexDocId ||
                            'pi-cmmjo68xg04il9rqnht74lnr1'
                        }
                        creditContext={{
                            company_name: company,
                            sector: sessionData?.features?.sector_name || 'Textile Manufacturing',
                            final_score: state?.finalScore || state?.adjustedScore,
                            decision: state?.decision || (state?.finalScore >= 70 ? 'APPROVE' : 'WATCHLIST'),
                            loan_limit_cr: parseFloat(String(state?.loanLimit || '7.65').replace(/[^\d.]/g, '')) || 7.65,
                            interest_rate: parseFloat(String(state?.interestRate || '10').replace(/[^\d.]/g, '')) || 10,
                            tenure_months: parseInt(String(state?.tenure || '12').replace(/[^\d]/g, '')) || 12,
                            gst_bank_match_score: sessionData?.features?.gst_bank_match_score || 0.58,
                            gst_reconciliation_score: state?.reconciliationScore || 58,
                            gst_flags: state?.gstFlags || [],
                            debt_equity_ratio: sessionData?.features?.debt_equity_ratio || 0.586,
                            working_capital: sessionData?.features?.working_capital || 58000000,
                            auditor_qualification: sessionData?.features?.auditor_qualification || 'Unqualified',
                            revenue_trend: sessionData?.features?.revenue_trend || 'FY2023: Rs.35.0Cr → FY2024: Rs.38.0Cr → FY2025: Rs.42.5Cr',
                            sector_name: sessionData?.features?.sector_name || 'Textile Manufacturing',
                            base_ml_score: state?.baseScore || 91,
                            qualitative_penalty: state?.qualitativeDelta || -19,
                            regulatory_impact: 0,
                            gst_penalty: -8,
                            gst_formula: '100 - 20 - 7 - 15 = 58/100',
                            improvement_paths: [
                                { action: 'Resolve pending litigation', score_gain: '+18 pts', detail: '-18pt qualitative penalty' },
                                { action: 'Improve GST compliance score to 0.75+', score_gain: '+7 to +9 pts', detail: 'ITC gap below 20% threshold' },
                                { action: 'Reduce debt-equity ratio to below 0.470x', score_gain: '+5.8 pts', detail: 'Retire ~Rs.1.5Cr borrowings' },
                            ],
                            ml_features: {
                                working_capital: { 
                                    value: formatCrores(sessionData?.features?.working_capital || 0), 
                                    signal: (sessionData?.features?.working_capital || 0) > 0 ? 'GREEN' : 'RED', 
                                    meaning: (sessionData?.features?.working_capital || 0) > 0 ? 'positive liquidity buffer' : 'liquidity pressure' 
                                },
                                debt_equity_ratio: { 
                                    value: `${(sessionData?.features?.debt_equity_ratio || 0).toFixed(3)}x`, 
                                    signal: (sessionData?.features?.debt_equity_ratio || 0) < 1.5 ? 'GREEN' : 'RED', 
                                    meaning: (sessionData?.features?.debt_equity_ratio || 0) < 1.5 ? 'healthy leverage' : 'highly leveraged' 
                                },
                                gst_bank_match_score: { 
                                    value: `${sessionData?.features?.gst_bank_match_score || 0.0}`, 
                                    signal: (sessionData?.features?.gst_bank_match_score || 0) >= 0.7 ? 'GREEN' : 'RED', 
                                    meaning: (sessionData?.features?.gst_bank_match_score || 0) >= 0.7 ? 'reconciliation verified' : 'reconciliation gaps detected' 
                                },
                                legal_flag_count: { 
                                    value: String(sessionData?.features?.legal_flag_count || 0), 
                                    signal: (sessionData?.features?.legal_flag_count || 0) === 0 ? 'GREEN' : 'RED', 
                                    meaning: (sessionData?.features?.legal_flag_count || 0) === 0 ? 'no legal issues' : 'active legal flags' 
                                },
                                revenue_expense_ratio: { 
                                    value: String(sessionData?.features?.revenue_expense_ratio || 0), 
                                    signal: (sessionData?.features?.revenue_expense_ratio || 0) > 0.05 ? 'GREEN' : 'RED', 
                                    meaning: `${(Number(sessionData?.features?.revenue_expense_ratio || 0) * 100).toFixed(1)}% EBITDA margin` 
                                },
                                sector_risk_flag: { 
                                    value: String(sessionData?.features?.sector_risk_flag || 0), 
                                    signal: (sessionData?.features?.sector_risk_flag || 0) === 0 ? 'GREEN' : 'RED', 
                                    meaning: (sessionData?.features?.sector_risk_flag || 0) === 0 ? 'acceptable sector risk' : 'high-risk sector' 
                                },
                            },
                        }}
                        />
                    </div>
                </div>
            </div>
            
        </div>
    );
}
