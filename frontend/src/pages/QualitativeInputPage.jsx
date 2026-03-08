import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import axios from 'axios';
import {
    Loader2, ArrowRight, Factory, ShieldAlert, FileText
} from 'lucide-react';

const mgtOptions = [
    { value: 'STRONG', label: 'Strong', sentiment: 'positive' },
    { value: 'AVERAGE', label: 'Average', sentiment: 'neutral' },
    { value: 'WEAK', label: 'Weak', sentiment: 'negative' }
];
const siteOptions = [
    { value: 'POSITIVE', label: 'Positive', sentiment: 'positive' },
    { value: 'NEUTRAL', label: 'Neutral', sentiment: 'neutral' },
    { value: 'NEGATIVE', label: 'Negative', sentiment: 'negative' }
];
const industryOptions = [
    { value: 'FAVORABLE', label: 'Favorable', sentiment: 'positive' },
    { value: 'STABLE', label: 'Stable', sentiment: 'neutral' },
    { value: 'ADVERSE', label: 'Adverse', sentiment: 'negative' }
];
const collateralOptions = [
    { value: 'PRIME', label: 'Prime', sentiment: 'positive' },
    { value: 'STANDARD', label: 'Standard', sentiment: 'neutral' },
    { value: 'SUBSTANDARD', label: 'Substandard', sentiment: 'negative' }
];
const promoterOptions = [
    { value: 'HIGH', label: 'High', sentiment: 'positive' },
    { value: 'MEDIUM', label: 'Medium', sentiment: 'neutral' },
    { value: 'LOW', label: 'Low', sentiment: 'negative' }
];
const litigationOptions = [
    { value: true, label: 'Yes', sentiment: 'negative' },
    { value: false, label: 'No', sentiment: 'positive' }
];

const SelectGroupBox = ({ options, value, onChange, cols = 3 }) => {
    const gridClass = cols === 2 ? "grid-cols-2" : "grid-cols-3";
    return (
        <div className={`grid ${gridClass} gap-3`}>
            {options.map((opt) => {
                const isSelected = value === opt.value;
                let colorClass = "border-white/10 hover:bg-white/5 text-white/80";
                if (isSelected) {
                    if (opt.sentiment === 'positive') colorClass = "border-green-500 bg-green-500/20 text-green-300 shadow-[0_0_10px_rgba(34,197,94,0.3)]";
                    else if (opt.sentiment === 'negative') colorClass = "border-red-500 bg-red-500/20 text-red-300 shadow-[0_0_10px_rgba(239,68,68,0.3)]";
                    else colorClass = "border-amber-500 bg-amber-500/20 text-amber-300 shadow-[0_0_10px_rgba(245,158,11,0.3)]";
                }

                return (
                    <div
                        key={String(opt.value)}
                        onClick={() => onChange(opt.value)}
                        className={`px-3 py-2.5 rounded-xl border cursor-pointer text-center text-sm font-medium transition-all ${colorClass}`}
                    >
                        {opt.label}
                    </div>
                )
            })}
        </div>
    )
};

const SectionCard = ({ title, icon: Icon, children }) => (
    <div className="bg-white/10 backdrop-blur-md rounded-2xl border border-white/20 p-6 mb-6">
        <h2 className="text-lg font-semibold flex items-center mb-5 text-white">
            <Icon className="mr-2 text-blue-400" size={20} />
            {title}
        </h2>
        {children}
    </div>
);

const FormGroup = ({ label, children }) => (
    <div className="mb-6 last:mb-0">
        <label className="block text-sm font-medium text-white/70 mb-2">{label}</label>
        {children}
    </div>
);

export default function QualitativeInputPage() {
    const location = useLocation();
    const navigate = useNavigate();

    const state = location.state || {};
    const baseScore = state.baseScore ?? (state.data?.ml_output?.predicted_score ? parseFloat(state.data.ml_output.predicted_score) : 68);
    const companyName = location.state?.companyName || location.state?.company_name || location.state?.data?.company_name || location.state?.data?.extracted_data?.company_name || "Sharma Textile Mills Pvt. Ltd";
    const initialRiskTier = state.riskTier || state.data?.ml_output?.decision || "WATCHLIST";

    const [inputs, setInputs] = useState({
        capacity_utilization: null,
        management_quality: null,
        site_visit_outcome: null,
        pending_litigation: null,
        industry_outlook: null,
        collateral_quality: null,
        promoter_cooperation: null,
        free_text_notes: ""
    });

    const [apiResult, setApiResult] = useState(null);
    const [isLoading, setIsLoading] = useState(false);
    
    const [displayScore, setDisplayScore] = useState(baseScore);
    const debounceRef = useRef(null);
    const animationRef = useRef(null);

    const fetchAdjustment = useCallback(async (currentInputs) => {
        const filledCount = Object.values(currentInputs).filter(v => v !== null && v !== "").length;
        if (filledCount < 2) return;

        setIsLoading(true);
        try {
            const payload = {
                base_score: baseScore,
                company_name: companyName,
                inputs: currentInputs
            };
            const res = await axios.post(`${import.meta.env.VITE_API_BASE_URL}/api/v1/qualitative/adjust/`, payload);
            setApiResult(res.data);
        } catch (error) {
            console.error("Qualitative API failed silently", error);
        } finally {
            setIsLoading(false);
        }
    }, [baseScore, companyName]);

    const handleInputChange = (field, value) => {
        const newInputs = { ...inputs, [field]: value };
        setInputs(newInputs);

        if (debounceRef.current) {
            clearTimeout(debounceRef.current);
        }

        debounceRef.current = setTimeout(() => {
            fetchAdjustment(newInputs);
        }, 800);
    };

    useEffect(() => {
        const target = apiResult?.adjusted_score ?? baseScore;
        if (target == null) return;

        if (animationRef.current) {
            cancelAnimationFrame(animationRef.current);
        }

        const startValue = displayScore;
        const duration = 600;
        let startTime = null;

        const easeOutCubic = (t) => 1 - Math.pow(1 - t, 3);

        const step = (timestamp) => {
            if (startTime === null) startTime = timestamp;
            const elapsed = timestamp - startTime;
            const progress = Math.min(elapsed / duration, 1);
            const eased = easeOutCubic(progress);
            const nextValue = Math.round(startValue + (target - startValue) * eased);
            setDisplayScore(nextValue);

            if (progress < 1) {
                animationRef.current = requestAnimationFrame(step);
            }
        };

        animationRef.current = requestAnimationFrame(step);

        return () => {
            if (animationRef.current) {
                cancelAnimationFrame(animationRef.current);
            }
        };
    }, [apiResult, baseScore, displayScore]);

    const getTierColor = (score) => {
        if (score >= 70) return "#27ae60"; // APPROVE
        if (score >= 50) return "#e8a020"; // WATCHLIST
        return "#c0392b"; // REJECT
    };

    const tierColor = getTierColor(displayScore);
    const currentTier = apiResult?.risk_tier || initialRiskTier;

    const getChips = () => {
        if (!apiResult?.breakdown) return [];
        const chips = [];
        const bd = apiResult.breakdown;

        if (bd.capacity) chips.push({ val: bd.capacity, label: bd.capacity < 0 ? "Low Capacity" : "High Capacity" });
        if (bd.management) chips.push({ val: bd.management, label: bd.management < 0 ? "Weak Management" : "Strong Management" });
        if (bd.site_visit) chips.push({ val: bd.site_visit, label: bd.site_visit < 0 ? "Negative Site" : "Positive Site" });
        if (bd.litigation) chips.push({ val: bd.litigation, label: "Litigation" });
        if (bd.industry) chips.push({ val: bd.industry, label: bd.industry < 0 ? "Adverse Industry" : "Favorable Industry" });
        if (bd.collateral) chips.push({ val: bd.collateral, label: bd.collateral < 0 ? "Substandard Collat." : "Prime Collat." });
        if (bd.promoter) chips.push({ val: bd.promoter, label: bd.promoter < 0 ? "Low Coop." : "High Coop." });
        if (bd.free_text_nlp) chips.push({ val: bd.free_text_nlp, label: bd.free_text_nlp < 0 ? "Negative Notes" : "Positive Notes" });

        return chips.filter(c => c.val !== 0).map(c => ({
            ...c,
            text: `${c.val > 0 ? '+' : ''}${c.val} \u00B7 ${c.label}`
        }));
    };

    const chips = getChips();
    const visibleChips = chips.slice(0, 5);
    const hiddenCount = chips.length - 5;

    const handleSkip = () => {
        navigate('/evidence', {
            state: {
                ...state,
                adjustedScore: baseScore,
                baseScore: baseScore,
                companyName: companyName,
                qualitativeDelta: 0,
                qualitativeChips: [],
                analystInputs: inputs,
                adjustments: null,
                summary_paragraph: ""
            }
        });
    };

    const handleApply = () => {
        navigate('/evidence', {
            state: {
                ...state,
                adjustedScore: displayScore,
                baseScore: baseScore,
                companyName: companyName,
                qualitativeDelta: apiResult ? apiResult.final_delta : 0,
                qualitativeChips: apiResult ? apiResult.breakdown : [],
                analystInputs: inputs,
                adjustments: apiResult ? apiResult.breakdown : null,
                summary_paragraph: apiResult ? apiResult.summary_paragraph : ""
            }
        });
    };

    return (
        <div className="container mx-auto px-4 py-10 text-white min-h-[calc(100vh-80px)]">
            <div className="mb-8">
                <h1 className="text-3xl font-bold tracking-tight">Qualitative Adjustments</h1>
                <p className="text-white/60 mt-2 text-lg">Refine the purely quantitative ML score for <span className="text-white font-medium">{companyName}</span> using manual analyst observations.</p>
            </div>

            <div className="flex flex-col lg:flex-row gap-8">
                {/* Left Form */}
                <div className="flex-1 max-w-2xl">
                    <SectionCard title="Operations & Management" icon={Factory}>
                        <FormGroup label="Capacity Utilization">
                            <div className="flex items-center gap-4">
                                <input
                                    type="range"
                                    min="0" max="100" step="5"
                                    value={inputs.capacity_utilization ?? 0}
                                    onChange={(e) => handleInputChange('capacity_utilization', parseFloat(e.target.value))}
                                    className="flex-1 h-2 rounded-lg appearance-none cursor-pointer outline-none"
                                    style={{ background: 'linear-gradient(to right, #ef4444 50%, #f59e0b 50%, #f59e0b 70%, #10b981 70%)' }}
                                />
                                <span className="bg-white/10 px-4 py-1.5 rounded-lg text-sm font-semibold min-w-[3.5rem] text-center shadow-inner">
                                    {inputs.capacity_utilization === null ? '--' : `${inputs.capacity_utilization}%`}
                                </span>
                            </div>
                        </FormGroup>

                        <FormGroup label="Management Quality">
                            <SelectGroupBox
                                options={mgtOptions}
                                value={inputs.management_quality}
                                onChange={(v) => handleInputChange('management_quality', v)}
                            />
                        </FormGroup>

                        <FormGroup label="Promoter Cooperation">
                            <SelectGroupBox
                                options={promoterOptions}
                                value={inputs.promoter_cooperation}
                                onChange={(v) => handleInputChange('promoter_cooperation', v)}
                            />
                        </FormGroup>
                    </SectionCard>

                    <SectionCard title="Risk & Outlook" icon={ShieldAlert}>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-x-8">
                            <FormGroup label="Site Visit Outcome">
                                <SelectGroupBox
                                    options={siteOptions}
                                    value={inputs.site_visit_outcome}
                                    onChange={(v) => handleInputChange('site_visit_outcome', v)}
                                    cols={1}
                                />
                            </FormGroup>
                            <FormGroup label="Collateral Quality">
                                <SelectGroupBox
                                    options={collateralOptions}
                                    value={inputs.collateral_quality}
                                    onChange={(v) => handleInputChange('collateral_quality', v)}
                                    cols={1}
                                />
                            </FormGroup>
                            <FormGroup label="Industry Outlook">
                                <SelectGroupBox
                                    options={industryOptions}
                                    value={inputs.industry_outlook}
                                    onChange={(v) => handleInputChange('industry_outlook', v)}
                                    cols={1}
                                />
                            </FormGroup>
                            <FormGroup label="Pending Litigation">
                                <div className="mt-1">
                                    <SelectGroupBox
                                        options={litigationOptions}
                                        value={inputs.pending_litigation}
                                        onChange={(v) => handleInputChange('pending_litigation', v)}
                                        cols={2}
                                    />
                                </div>
                            </FormGroup>
                        </div>
                    </SectionCard>

                    <SectionCard title="Analyst Notes (Free Text NLP Analysis)" icon={FileText}>
                        <FormGroup label="Enter specific observational keywords to be analyzed by the NLP engine. Negative keywords natively reduce score.">
                            <textarea
                                className="w-full bg-white/5 border border-white/10 rounded-xl p-4 text-sm text-white focus:outline-none focus:ring-2 focus:ring-blue-500/50 h-32 resize-none shadow-inner"
                                placeholder="E.g. Factory found idle in second shift. Some dispute with workers noted. Order book looks healthy."
                                value={inputs.free_text_notes}
                                onChange={(e) => handleInputChange('free_text_notes', e.target.value)}
                            />
                        </FormGroup>
                    </SectionCard>
                </div>

                {/* Right Sticky Preview */}
                <div className="lg:w-[420px]">
                    <div className="bg-white/10 backdrop-blur-md rounded-2xl border border-white/20 p-8 sticky top-8 flex flex-col items-center shadow-2xl">

                        {isLoading && (
                            <div className="absolute top-4 right-4 bg-black/40 p-2 rounded-full shadow-lg">
                                <Loader2 className="animate-spin text-white" size={18} />
                            </div>
                        )}

                        <div className="text-white/60 font-medium tracking-widest text-sm uppercase mb-8">
                            Adjusted Score
                        </div>

                        {/* Animated Score Circle */}
                        <div
                            className="w-64 h-64 rounded-full border-8 flex items-center justify-center flex-col transition-all duration-300 bg-white/5"
                            style={{ borderColor: tierColor, boxShadow: `0 0 40px ${tierColor}40`, textShadow: `0 0 20px ${tierColor}80` }}
                        >
                            <div className="text-8xl font-black tracking-tighter" style={{ color: tierColor }}>
                                {displayScore}
                            </div>
                            <div className="text-sm font-bold uppercase tracking-[0.2em] mt-3 opacity-90" style={{ color: tierColor }}>
                                {currentTier}
                            </div>
                        </div>

                        {/* Adjustment Chips */}
                        <div className="flex flex-wrap gap-2 justify-center mt-10 min-h-[60px]">
                            {visibleChips.map((chip, idx) => (
                                <span key={idx} className={`px-3 py-1.5 text-xs font-bold rounded-full border shadow-sm ${chip.val > 0 ? 'bg-green-500/20 border-green-500/50 text-green-300' : 'bg-red-500/20 border-red-500/50 text-red-300'}`}>
                                    {chip.text}
                                </span>
                            ))}
                            {hiddenCount > 0 && (
                                <span className="px-3 py-1.5 text-xs font-bold rounded-full bg-white/10 border border-white/20 text-white/50 shadow-sm">
                                    +{hiddenCount} more
                                </span>
                            )}
                            {chips.length === 0 && (
                                <span className="text-white/40 text-sm font-medium italic">No adjustments applied yet</span>
                            )}
                        </div>

                        {/* Summary preview optionally */}
                        {apiResult?.summary_paragraph && (
                            <div className="mt-8 p-4 bg-white/5 rounded-xl border border-white/10 text-sm text-white/80 leading-relaxed italic text-center w-full shadow-inner">
                                "{apiResult.summary_paragraph}"
                            </div>
                        )}

                        {/* Action Buttons */}
                        <div className="flex w-full gap-4 mt-8">
                            <button onClick={handleSkip} className="flex-1 bg-white/5 hover:bg-white/10 border border-white/20 py-3.5 rounded-xl font-semibold flex items-center justify-center transition-all focus:outline-none focus:ring-2 focus:ring-white/50 text-sm">
                                Skip
                            </button>
                            <button onClick={handleApply} className="flex-1 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 py-3.5 rounded-xl font-bold flex items-center justify-center shadow-lg shadow-blue-500/30 transition-all focus:outline-none focus:ring-2 focus:ring-blue-500/50 text-sm">
                                Apply & Continue <ArrowRight size={18} className="ml-2" />
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
