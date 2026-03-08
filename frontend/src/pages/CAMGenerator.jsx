import { useState } from 'react';
import { useLocation } from 'react-router-dom';
import { FileText, Download, Edit3, Loader2, Sparkles } from 'lucide-react';
import { generateCam } from '../api';
import { useAppContext } from '../context/AppContext';

export default function CAMGenerator() {
    const { sessionData } = useAppContext();
    const location = useLocation();
    const state = location.state || {};

    const [isGenerating, setIsGenerating] = useState(false);
    const [camUrl, setCamUrl] = useState(null);
    const [analystNotes, setAnalystNotes] = useState('');

    const company =
        state.companyName ||
        sessionData.features?.company_name ||
        sessionData.nlpEntities?.find(e => e.type === 'ORG')?.text ||
        'Unknown Company';

    const finalScore =
        typeof state.adjustedScore === 'number'
            ? state.adjustedScore
            : Math.round((sessionData.scoreResult?.predicted_score || 0) * 100);

    const handleGenerate = async () => {
        setIsGenerating(true);
        setCamUrl(null);
        try {
            const payload = {
                companyName: company,
                company_name: company,
                date: new Date().toISOString().split('T')[0],
                entity_id: 'L12345MH2024PLC009999',
                features: sessionData.features || state.extractedFinancials || {},
                extractedFinancials: state.extractedFinancials || sessionData.features || {},
                ml_output: sessionData.scoreResult || {},
                entity_data: sessionData.nlpEntities || [],
                evidence: sessionData.evidence || [],
                notes: analystNotes,
                user_id: sessionData?.user?.id,
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
                finalScore: state.finalScore
            };

            const responseBlob = await generateCam(payload);

            // Create a URL for the downloaded PDF blob with an explicit MIME type
            const blob = new Blob([responseBlob], { type: 'application/pdf' });
            const url = window.URL.createObjectURL(blob);
            setCamUrl(url);
        } catch (err) {
            console.error("CAM Generation Failed:", err);
        } finally {
            setIsGenerating(false);
        }
    };

    return (
        <div className="flex flex-col gap-8 w-full max-w-4xl mx-auto py-10 animate-in fade-in slide-in-from-bottom-8 duration-700">
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
                        className="btn-primary flex items-center gap-3 bg-emerald-600 hover:bg-emerald-500 border-none shadow-[0_0_20px_rgba(16,185,129,0.4)] px-8 py-4 rounded-full font-bold text-xl relative z-10"
                    >
                        <Download size={24} /> Download Final PDF
                    </a>
                </div>
            )}
        </div>
    );
}
