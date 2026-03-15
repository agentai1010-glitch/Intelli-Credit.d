import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
    ComposedChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, ReferenceLine, Cell,
    RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, Legend,
    RadialBarChart, RadialBar
} from 'recharts';
import { Activity, ShieldAlert, Cpu, ArrowRight, TrendingUp, DollarSign, Calendar } from 'lucide-react';
import { scoreCompany } from '../api';
import { useAppContext } from '../context/AppContext';

export default function ScoreView() {
    const { sessionData, updateSession } = useAppContext();
    const [data, setData] = useState(sessionData.scoreResult ? {
        score_result: sessionData.scoreResult,
        nlp_entities: sessionData.nlpEntities || [],
        explanation: sessionData.explanation || null
    } : null);

    const [loading, setLoading] = useState(!sessionData.scoreResult);
    const [termsData, setTermsData] = useState(null);
    const [counterfactuals, setCounterfactuals] = useState([]);
    const navigate = useNavigate();

    // Animated Score State
    const [displayScore, setDisplayScore] = useState(0);

    const formatCrores = (absoluteRupees) => {
        if (!absoluteRupees && absoluteRupees !== 0) return "N/A";
        const crores = absoluteRupees / 10000000;
        return `₹${crores.toFixed(2)} Cr`;
    };

    const runScore = async () => {
        if (!sessionData.features || Object.keys(sessionData.features).length === 0) {
            setLoading(false);
            return;
        }

        const f = sessionData.features;
        try {
            // Task 1: COMPUTE FRESH FEATURES (Clear Stale Values)
            const revenue = Number(f.revenue || 0);
            const ebitda = Number(f.ebitda || 0);
            const netWorth = Number(f.net_worth || 0);
            const debt = Number(f.existing_debt || 0);

            // Recompute from base fields to avoid stale values
            const wc = netWorth - debt;
            const deRatio = netWorth > 0 ? debt / netWorth : 0;
            const revExpRatio = revenue > 0 ? ebitda / revenue : 0;

            const gstScore = Number(
                f.gst_bank_match_score != null
                    ? f.gst_bank_match_score * 100
                    : sessionData.gst_reconciliation?.reconciliation_score ?? 100
            );

            const payload = {
                document_data: {
                    revenue,
                    ebitda,
                    net_worth: netWorth,
                    existing_debt: debt,
                    working_capital: wc,
                    debt_equity_ratio: deRatio,
                    revenue_expense_ratio: revExpRatio,
                    gst_reconciliation_score: gstScore,
                    sector_risk: Number(f.sector_risk_flag || 0),
                    auditor_qualification: f.auditor_qualification || 'Unqualified',
                    legal_flag_count: Number(f.legal_flag_count || 0),
                },
                gst_reconciliation_score: gstScore
            };
            const response = await scoreCompany(payload);
            setData(response);
            updateSession({
                scoreResult: response.score_result,
                nlpEntities: response.nlp_entities,
                explanation: response.explanation
            });
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        // ALWAYS run score recalculation on page load to prevent 
        // cached "23" REJECT scores from invalidating user sessions
        runScore();
    }, []);

    useEffect(() => {
        const curData = data || sessionData;
        const targetScore = curData?.score_result?.predicted_score || curData?.predicted_score || 0;
        const scoreInt = Math.round(targetScore * 100);

        let start = 0;
        const duration = 1500;
        const increment = scoreInt / (duration / 16);

        const timer = setInterval(() => {
            start += increment;
            if (start >= scoreInt) {
                setDisplayScore(scoreInt);
                clearInterval(timer);
            } else {
                setDisplayScore(Math.floor(start));
            }
        }, 16);
        return () => clearInterval(timer);
    }, [data, sessionData]);

    // Fetch Recommendation Terms & Counterfactuals
    useEffect(() => {
        const fetchInsights = async () => {
            const curData = data || sessionData;
            const score = curData?.score_result?.predicted_score || curData?.predicted_score || 0;
            const scoreInt = Math.round(score * 100);

            if (scoreInt > 0) {
                try {
                    // Utility to ensure we have Crores for the pricing engine
                    const normalizeToCr = (val) => {
                        if (!val) return 0;
                        const n = Number(val);
                        // If it's already a small number (e.g. 42.5), it's likely already in Crores.
                        // If it's huge (e.g. 425000000), it's raw rupees.
                        return n > 1000000 ? n / 1e7 : n;
                    };

                    const fData = sessionData.features || {};
                    const revCr = normalizeToCr(fData.revenue);
                    const debtCr = normalizeToCr(fData.existing_debt);
                    const ebitdaCr = normalizeToCr(fData.ebitda);
                    const collateralCr = normalizeToCr(fData.collateral_value);
                    
                    const gstScore = Number(
                        fData.gst_bank_match_score != null
                            ? fData.gst_bank_match_score * 100
                            : sessionData.gst_reconciliation?.reconciliation_score ?? 100
                    );

                    const termsPayload = {
                        risk_score: scoreInt,
                        revenue: revCr || 42.5,
                        debt: debtCr || 8.2,
                        ebitda: ebitdaCr || 6.1,
                        collateral_value: collateralCr || 12.0,
                        gst_reconciliation_score: gstScore,
                        qualitative_delta: {
                            pending_litigation: false,
                            management_quality: "AVERAGE",
                            industry_outlook: "STABLE",
                            collateral_quality: "STANDARD"
                        }
                    };

                    const termRes = await fetch(`${import.meta.env.VITE_API_BASE_URL}/api/v1/recommendation/terms`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(termsPayload)
                    });
                    if (termRes.ok) setTermsData(await termRes.json());

                    // Prepare Shap values format properly for dict
                    const shapArray = curData?.explanation?.top_features || [];
                    const shapDict = {};
                    shapArray.forEach(s => { shapDict[s.feature] = s.impact; });

                    // Only send the 6 numeric ML features (not strings like sector/auditor)
                    const f = sessionData.features || {};
                    const nw = Number(f.net_worth || 0);
                    const dt = Number(f.existing_debt || 0);
                    const numericFeatures = {
                        revenue_expense_ratio: nw && f.revenue ? Number(f.ebitda || 0) / Number(f.revenue) : 0,
                        working_capital: nw - dt,
                        debt_equity_ratio: nw > 0 ? dt / nw : 0,
                        gst_bank_match_score: Number(f.gst_bank_match_score || 0.58),
                        legal_flag_count: Number(f.legal_flag_count || 0),
                        sector_risk_flag: Number(f.sector_risk_flag || 0)
                    };

                    const cfPayload = {
                        features: numericFeatures,
                        risk_score: scoreInt,
                        shap_values: shapDict
                    };

                    const cfRes = await fetch(`${import.meta.env.VITE_API_BASE_URL}/api/v1/recommendation/counterfactual`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(cfPayload)
                    });

                    if (cfRes.ok) {
                        const cfData = await cfRes.json();
                        setCounterfactuals(cfData.counterfactuals || []);
                    }
                } catch (e) { console.error("Failed fetching enhanced insights", e); }
            }
        };
        fetchInsights();
    }, [data, sessionData]);

    if (!sessionData.features || Object.keys(sessionData.features).length === 0) {
        return (
            <div className="flex w-full h-[60vh] flex-col items-center justify-center text-slate-400 font-bold gap-4">
                <ShieldAlert className="w-16 h-16 text-slate-500 mb-2" />
                <h2 className="text-2xl">Please upload documents first</h2>
                <button onClick={() => navigate('/')} className="btn-primary mt-4">Go to Upload</button>
            </div>
        );
    }

    if (loading) {
        return (
            <div className="flex w-full h-[60vh] flex-col items-center justify-center text-slate-400 font-bold gap-4">
                <Cpu className="animate-spin text-blue-500 w-16 h-16" />
                <h2 className="text-2xl mt-4 animate-pulse">Running ML Engine...</h2>
                <p>Extracting Features • Analyzing NLP Flags • SHAP Explainers</p>
            </div>
        );
    }

    const curData = data || sessionData;
    const getTier = (score) => score >= 70 ? "APPROVE" : score >= 50 ? "WATCHLIST" : "REJECT";
    const decision = getTier(displayScore);
    const shapFeatures = curData?.explanation?.top_features || curData?.score_result?.top_features || [];

    const formatLimitCr = (val) => {
        if (val === null || val === undefined || isNaN(val)) return '—';
        const num = Number(val);
        const cr = num / 10_000_000; // backend returns raw rupees
        return `₹${cr.toFixed(1)}Cr`;
    };

    const formatCounterfactualValue = (factor, value) => {
        if (value === null || value === undefined || isNaN(value)) return 'N/A';
        const num = Number(value);
        const key = (factor || '').toLowerCase();

        if (key === 'working_capital') {
            return formatCrores(num);
        }

        let unit = 'raw';
        if (key === 'working_capital') {
            unit = 'currency';
        } else if (key.includes('ratio')) {
            unit = 'ratio';
        } else if (key.includes('capacity') || key.includes('utilization')) {
            unit = 'percent';
        } else if (
            key.includes('revenue') ||
            key.includes('turnover') ||
            key.includes('credits') ||
            key.includes('net_worth') ||
            key.includes('collateral') ||
            key.includes('debt') ||
            key.includes('liability') ||
            key.includes('ebitda')
        ) {
            unit = 'currency';
        }

        if (unit === 'currency') {
            const cr = num / 10_000_000;
            return `₹${cr.toFixed(2)}Cr`;
        }

        if (unit === 'ratio') {
            return num.toFixed(2);
        }

        if (unit === 'percent') {
            return `${num.toFixed(0)}%`;
        }

        return num;
    };

    // Waterfall prep (flip SHAP sign so positive = lift towards APPROVE)
    let currentShapBase = 50;
    const waterfallData = shapFeatures.map(s => {
        const approvalImpact = -1 * (s.impact || 0); // model SHAP is on default risk
        const isPos = approvalImpact > 0;
        return {
            name: s.feature.replace(/_/g, ' '),
            rawImpact: approvalImpact,
            start: currentShapBase,
            end: currentShapBase + (approvalImpact * 100), // Scale up visual
            fill: isPos ? '#10b981' : '#ef4444' // Emerald / Red
        };
    });

    const radialData = [{ name: 'Score', value: displayScore, fill: decision === 'APPROVE' ? '#10b981' : decision === 'WATCHLIST' ? '#f59e0b' : '#ef4444' }];

    // 5Cs Radar Prep
    const dscr = (sessionData.features?.ebitda || 8) / ((sessionData.features?.existing_debt || 10) * 0.15 || 1);
    const radarData = [
        { subject: 'Character', A: 85, B: 65 },
        { subject: 'Capacity', A: Math.min(dscr * 25, 100), B: 65 },
        { subject: 'Capital', A: 80, B: 65 },
        { subject: 'Collateral', A: 90, B: 65 },
        { subject: 'Conditions', A: 60, B: 65 },
    ];

    return (
        <div className="flex flex-col gap-8 w-full max-w-6xl mx-auto py-10 animate-in fade-in slide-in-from-bottom-8 duration-700">
            <header className="flex justify-between items-end">
                <div>
                    <h1 className="text-4xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 to-cyan-400 tracking-tight mb-2">
                        AI Credit Intelligence Dashboard
                    </h1>
                    <p className="text-slate-400 text-lg">Multi-model consensus output & interpretability maps</p>
                </div>
                <button className="btn-primary" onClick={() => navigate('/qualitative-input', {
                    state: {
                        baseScore: displayScore,
                        companyName: sessionData.features?.company_name || sessionData?.companyName || 'Company',
                        riskTier: decision,
                        loanLimit: formatLimitCr(termsData?.recommended_limit_cr),
                        interestRate: termsData?.recommended_rate_pct + "%",
                        tenure: termsData?.sanction_terms?.tenure_months + "m",
                        gstFlags: sessionData.gst_reconciliation?.flags || [],
                        reconciliationScore: sessionData.gst_reconciliation?.reconciliation_score ?? 58,
                        shapValues: curData?.explanation?.top_features || [],
                        extractedFinancials: sessionData.features || {}
                    }
                })}>Next: Qualitative Review</button>
            </header>

            {/* Top Score Section Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

                {/* 1. SCORE CARD */}
                <div className="glass-panel p-6 flex flex-col items-center justify-center relative col-span-1 border border-white/20 rounded-2xl bg-white/5 backdrop-blur-md">
                    <h2 className="text-sm uppercase tracking-widest text-slate-300 mb-2 font-bold">Predicted Risk Score</h2>

                    <div className="relative w-48 h-48 mb-4">
                        <ResponsiveContainer width="100%" height="100%">
                            <RadialBarChart
                                cx="50%" cy="50%" innerRadius="70%" outerRadius="100%"
                                barSize={15} data={radialData} startAngle={180} endAngle={-180}
                            >
                                <RadialBar minAngle={15} background={{ fill: '#1e293b' }} clockWise dataKey="value" cornerRadius={10} />
                            </RadialBarChart>
                        </ResponsiveContainer>
                        <div className="absolute inset-0 flex items-center justify-center flex-col">
                            <span className="text-5xl font-black text-white">{displayScore}</span>
                        </div>
                    </div>

                    <div className={`px-6 py-2 rounded-full font-bold text-sm tracking-wider shadow-lg animate-[pulse_2s_ease-in-out_infinite] border ${decision === 'APPROVE' ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/50' :
                        decision === 'WATCHLIST' ? 'bg-amber-500/20 text-amber-400 border-amber-500/50' :
                            'bg-red-500/20 text-red-400 border-red-500/50'
                        }`}>
                        {decision.toUpperCase()}
                    </div>

                    {/* 3 Mini Cards */}
                    {termsData && (
                        <div className="w-full grid grid-cols-3 gap-2 mt-6">
                            <div className="bg-slate-900/50 rounded-lg p-3 text-center border border-slate-700/50">
                                <DollarSign className="w-5 h-5 mx-auto text-emerald-400 mb-1" />
                                <div className="text-[10px] text-slate-400 uppercase">Limit</div>
                                <div className="font-bold text-sm text-slate-100">{formatLimitCr(termsData.recommended_limit_cr)}</div>
                            </div>
                            <div className="bg-slate-900/50 rounded-lg p-3 text-center border border-slate-700/50">
                                <TrendingUp className="w-5 h-5 mx-auto text-blue-400 mb-1" />
                                <div className="text-[10px] text-slate-400 uppercase">Rate</div>
                                <div className="font-bold text-sm text-slate-100">{termsData.recommended_rate_pct}%</div>
                            </div>
                            <div className="bg-slate-900/50 rounded-lg p-3 text-center border border-slate-700/50">
                                <Calendar className="w-5 h-5 mx-auto text-purple-400 mb-1" />
                                <div className="text-[10px] text-slate-400 uppercase">Tenure</div>
                                <div className="font-bold text-sm text-slate-100">{termsData.sanction_terms?.tenure_months}m</div>
                            </div>
                        </div>
                    )}
                </div>

                {/* 2. SHAP WATERFALL */}
                <div className="glass-panel p-6 col-span-1 lg:col-span-2 border border-white/20 rounded-2xl bg-white/5 backdrop-blur-md flex flex-col">
                    <div className="flex items-center gap-3 mb-4">
                        <ShieldAlert className="text-blue-400 w-6 h-6" />
                        <h2 className="text-lg font-bold text-white tracking-wide">SHAP Factor Waterfall</h2>
                    </div>
                    <div className="flex-grow w-full h-[250px]">
                        <ResponsiveContainer width="100%" height="100%">
                            <ComposedChart data={waterfallData} layout="vertical" margin={{ top: 0, right: 20, left: 30, bottom: 0 }}>
                                <XAxis
                                    type="number"
                                    stroke="#94a3b8"
                                    domain={['dataMin - 10', 'dataMax + 10']}
                                    tickFormatter={(val) => Number(val).toFixed(1)}
                                />
                                <YAxis dataKey="name" type="category" width={120} tick={{ fill: '#cbd5e1', fontSize: 11 }} />
                                <Tooltip
                                    cursor={{ fill: 'rgba(255,255,255,0.05)' }}
                                    contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #334155', borderRadius: '8px' }}
                                    formatter={(val, name, props) => [`If ${props.payload.name} improved, score ${(props.payload.rawImpact > 0 ? "+" : "")}${(props.payload.rawImpact * 100).toFixed(1)} points`, 'SHAP Impact']}
                                />
                                <Bar dataKey="end" barSize={20} radius={[0, 4, 4, 0]}>
                                    {waterfallData.map((e, idx) => (
                                        <Cell key={`cell-${idx}`} fill={e.fill} />
                                    ))}
                                </Bar>
                                <ReferenceLine x={50} stroke="#475569" strokeDasharray="3 3" />
                            </ComposedChart>
                        </ResponsiveContainer>
                    </div>
                    <p className="text-xs text-slate-500 mt-2 text-right">Green = Positive Lift • Red = Negative Drag</p>
                </div>

            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

                {/* 3. COUNTERFACTUAL PANEL */}
                <div className="glass-panel p-6 border border-white/20 rounded-2xl bg-white/5 backdrop-blur-md flex flex-col h-full">
                    <h2 className="text-lg font-bold text-white mb-6 uppercase tracking-wider flex items-center gap-2">
                        <TrendingUp className="text-emerald-400" /> Improvement Counterfactuals
                    </h2>

                    <div className="flex flex-col gap-4">
                        {counterfactuals.length > 0 ? counterfactuals.map((cf, idx) => (
                            <div key={idx} className="bg-slate-900/60 p-4 rounded-xl border border-slate-700/50">
                                <div className="flex justify-between items-center mb-2">
                                    <span className="font-bold text-slate-200 uppercase text-xs tracking-wider">{cf.factor.replace(/_/g, ' ')}</span>
                                    <span className="text-xs font-bold bg-emerald-500/20 text-emerald-400 px-2 py-1 rounded">+{cf.score_improvement.toFixed(1)} Pts</span>
                                </div>
                                <div className="text-sm text-slate-400 mb-3">
                                    {cf.action} (
                                    {formatCounterfactualValue(cf.factor, cf.current_value)}
                                    {" → "}
                                    {formatCounterfactualValue(cf.factor, cf.target_value)}
                                    )
                                </div>
                                <div className="w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
                                    <div className="bg-emerald-500 h-1.5 rounded-full relative" style={{ width: `${cf.new_projected_score}%` }}>
                                        <div className="absolute top-0 right-0 h-full bg-white opacity-40 w-1 animate-pulse"></div>
                                    </div>
                                </div>
                            </div>
                        )) : (
                            <div className="text-slate-500 italic p-4 text-center">Simulating pathways...</div>
                        )}
                    </div>
                </div>

                {/* 4. FIVE Cs RADAR CHART */}
                <div className="glass-panel p-6 border border-white/20 rounded-2xl bg-white/5 backdrop-blur-md flex flex-col h-[400px]">
                    <h2 className="text-lg font-bold text-white mb-2 uppercase tracking-wider">Five C's Evaluation</h2>
                    <ResponsiveContainer width="100%" height="100%">
                        <RadarChart cx="50%" cy="50%" outerRadius="70%" data={radarData}>
                            <PolarGrid stroke="#334155" />
                            <PolarAngleAxis dataKey="subject" tick={{ fill: '#cbd5e1', fontSize: 12 }} />
                            <PolarRadiusAxis angle={30} domain={[0, 100]} tick={false} stroke="#334155" />
                            <Radar name="This Company" dataKey="A" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.5} />
                            <Radar name="Industry Benchmark" dataKey="B" stroke="#64748b" fill="#64748b" fillOpacity={0.3} />
                            <Legend wrapperStyle={{ zIndex: 10 }} />
                            <Tooltip contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #334155', borderRadius: '8px' }} />
                        </RadarChart>
                    </ResponsiveContainer>
                </div>
            </div>
        </div>
    );
}
