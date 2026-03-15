import { useNavigate, useLocation } from 'react-router-dom';
import { ShieldAlert, ArrowRight, ShieldCheck, Activity, CheckCircle, Search, DollarSign, AlertTriangle } from 'lucide-react';
import { useAppContext } from '../context/AppContext';

export default function FeatureIntelligenceReport() {
    const navigate = useNavigate();
    const { sessionData } = useAppContext();
    const location = useLocation();

    // Real data from UploadPage -> navigate state
    const stateData = location.state || {};
    const computedFeatures = stateData.computedFeatures || {};
    const extractedFinancials = stateData.extractedFinancials || {};
    const gstFlags = stateData.gstFlags || [];
    const legalAdverseFlags = stateData.legalAdverseFlags || [];

    const features = sessionData?.features || extractedFinancials;

    // Real computed values from extractedFinancials
    const revenue = features.revenue || 0;
    const ebitda = features.ebitda || 0;
    const netWorth = features.net_worth || 0;
    const existingDebt = features.existing_debt || 0;
    const totalCredits = features.total_credits || 0;
    const closingBalance = features.closing_balance || 0;
    const turnover = features.turnover || 0;
    const itcClaimed = features.itc_claimed;
    const itcAvailable = features.itc_available;
    const sectorName = features.sector || 'Unknown';
    const auditorQual = features.auditor_qualification || 'Not available';

    // Task 2: Ensure live data from sessionData.features
    const dRaw = features.net_worth ? (features.existing_debt || 0) / features.net_worth : 0;
    const debtEquity = features.debt_equity_ratio ?? dRaw;
    const revExp = features.revenue_expense_ratio ?? (features.revenue > 0 ? (features.ebitda || 0) / features.revenue : 0);
    const workingCap = features.working_capital ?? (Number(features.net_worth || 0) - Number(features.existing_debt || 0));
    const gstMatch = features.gst_bank_match_score ?? 0.58;
    const legalFlags = features.legal_flag_count ?? 0;
    const sectorRisk = features.sector_risk_flag ?? 0;
    const reconciliationScore = Math.round(gstMatch * 100);

    const formatCrores = (absoluteRupees) => {
        if (!absoluteRupees && absoluteRupees !== 0) return "N/A";
        const crores = absoluteRupees / 10000000;
        return `₹${crores.toFixed(2)} Cr`;
    };

    const formatCr = (val) => {
        if (val === 0) return '₹0';
        if (Math.abs(val) >= 1e7) return `₹${(val / 1e7).toFixed(2)}Cr`;
        if (Math.abs(val) >= 1e5) return `₹${(val / 1e5).toFixed(2)}L`;
        return `₹${val.toLocaleString('en-IN')}`;
    };

    // Dynamic badge logic
    const gstBadge = gstMatch >= 0.8
        ? { label: 'Clean Match', color: '#27ae60', textColor: '#4ade80', icon: ShieldCheck }
        : gstMatch >= 0.6
            ? { label: 'Moderate Risk', color: '#f39c12', textColor: '#fbbf24', icon: AlertTriangle }
            : { label: 'Fraud Risk Detected', color: '#c0392b', textColor: '#ff4d4d', icon: ShieldAlert };

    const deBadge = debtEquity < 1.0
        ? { label: 'Healthy Leverage', color: '#27ae60', textColor: '#4ade80' }
        : debtEquity < 2.0
            ? { label: 'Moderate Leverage', color: '#f39c12', textColor: '#fbbf24' }
            : { label: 'High Leverage', color: '#c0392b', textColor: '#ff4d4d' };

    const revBadge = revExp >= 0.15
        ? { label: 'Strong Margin', color: '#27ae60', textColor: '#4ade80' }
        : revExp >= 0.05
            ? { label: 'Decent Margin', color: '#27ae60', textColor: '#4ade80' }
            : { label: 'Thin Margin', color: '#f39c12', textColor: '#fbbf24' };

    const legalBadge = legalFlags === 0
        ? { label: 'No Legal Risk', color: '#27ae60', textColor: '#4ade80' }
        : { label: `${legalFlags} Flag(s)`, color: '#c0392b', textColor: '#ff4d4d' };

    const sectorBadge = sectorRisk === 0
        ? { label: 'Acceptable Sector', color: '#27ae60', textColor: '#4ade80' }
        : { label: 'High-Risk Sector', color: '#c0392b', textColor: '#ff4d4d' };

    // Count healthy features
    const healthyCount = [gstMatch >= 0.7, debtEquity < 1.5, revExp > 0.05, workingCap > 0, legalFlags === 0, sectorRisk === 0].filter(Boolean).length;
    const riskCount = 6 - healthyCount;

    const handleRunML = () => {
        navigate('/score', { state: location.state });
    };

    return (
        <div className="flex flex-col gap-8 w-full max-w-6xl mx-auto py-10 animate-in fade-in slide-in-from-bottom-8 duration-700">
            <header className="flex justify-between items-end">
                <div>
                    <h1 className="text-4xl font-extrabold text-[#00d4ff] tracking-tight mb-2">
                        Feature Intelligence Report
                    </h1>
                    <p className="text-[#8892a4] text-lg">
                        How your documents translate into ML features for {sessionData?.companyName || 'Unknown Company'}
                    </p>
                </div>
                <button onClick={handleRunML} className="btn-primary flex items-center gap-2 px-6 py-3 font-bold bg-[#00d4ff] text-slate-900 shadow-[0_0_20px_rgba(0,212,255,0.3)] hover:bg-[#00b8e6]">
                    Run ML Scoring <ArrowRight size={20} />
                </button>
            </header>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

                {/* CARD 1: GST Bank Match Score */}
                <div className={`glass-panel p-6 border-l-4 rounded-2xl bg-[#1a2744]`} style={{ borderColor: gstBadge.color }}>
                    <div className="flex justify-between items-start mb-4">
                        <h2 className="text-xl font-bold text-slate-100">GST Bank Match Score</h2>
                        <div className="px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider flex items-center gap-2"
                             style={{ backgroundColor: `${gstBadge.color}33`, borderColor: `${gstBadge.color}80`, color: gstBadge.textColor, border: '1px solid' }}>
                            <gstBadge.icon size={14} /> {gstBadge.label}
                        </div>
                    </div>
                    <div className="text-4xl font-black text-white mb-6">{gstMatch.toFixed(2)} / 1.00</div>

                    <div className="flex gap-2 mb-6">
                        <span className="text-xs bg-slate-800 border border-slate-600 px-2 py-1 rounded text-slate-300">GSTR-3B</span>
                        <span className="text-xs bg-slate-800 border border-slate-600 px-2 py-1 rounded text-slate-300">GSTR-2A</span>
                        <span className="text-xs bg-slate-800 border border-slate-600 px-2 py-1 rounded text-slate-300">Bank Statement</span>
                    </div>

                    <div className="bg-slate-900/50 rounded-xl p-4 border border-slate-700/50 mb-4">
                        <h3 className="text-sm font-bold text-[#8892a4] uppercase mb-4 tracking-wider">Reconciliation Data</h3>

                        <div className="grid grid-cols-2 gap-2 text-sm text-slate-300 mb-4">
                            <div>GST Turnover (GSTR-3B):</div>
                            <div className="text-right font-mono">{turnover > 0 ? formatCr(turnover) : 'N/A'}</div>
                            <div>Bank Credits (Statement):</div>
                            <div className="text-right font-mono">{totalCredits > 0 ? formatCr(totalCredits) : 'N/A'}</div>
                            {turnover > 0 && totalCredits > 0 && (
                                <>
                                    <div>Revenue Gap:</div>
                                    <div className="text-right font-mono">{(Math.abs(turnover - totalCredits) / Math.max(turnover, totalCredits) * 100).toFixed(1)}%</div>
                                </>
                            )}
                        </div>

                        {itcClaimed != null && itcAvailable != null && (
                            <div className="grid grid-cols-2 gap-2 text-sm text-slate-300 mb-4 pt-3 border-t border-slate-700/50">
                                <div>ITC Claimed (GSTR-3B):</div>
                                <div className="text-right font-mono">{formatCr(itcClaimed)}</div>
                                <div>ITC Available (GSTR-2A):</div>
                                <div className="text-right font-mono">{formatCr(itcAvailable)}</div>
                                {Math.max(itcClaimed, itcAvailable) > 0 && (
                                    <>
                                        <div>ITC Gap:</div>
                                        <div className="text-right font-mono">{(Math.abs(itcClaimed - itcAvailable) / Math.max(itcClaimed, itcAvailable) * 100).toFixed(1)}%</div>
                                    </>
                                )}
                            </div>
                        )}

                        {gstFlags.length > 0 && (
                            <div className="pt-3 border-t border-slate-700/50">
                                <div className="text-xs font-bold text-amber-400 uppercase mb-2">Structural Risks Detected</div>
                                {gstFlags.map((flag, i) => (
                                    <div key={i} className="text-xs text-amber-300 mb-1">⚠️ {flag}</div>
                                ))}
                            </div>
                        )}

                        <div className="mt-4 pt-4 border-t border-slate-700/50 font-mono text-xs text-slate-300 space-y-1">
                            <div>Reconciliation Score: {reconciliationScore}/100</div>
                            <div className="text-[#00d4ff]">Feature value passed to ML: {reconciliationScore}/100 = {gstMatch.toFixed(2)}</div>
                        </div>
                    </div>
                </div>

                {/* CARD 2: Debt-Equity Ratio */}
                <div className={`glass-panel p-6 border-l-4 rounded-2xl bg-[#1a2744]`} style={{ borderColor: deBadge.color }}>
                    <div className="flex justify-between items-start mb-4">
                        <h2 className="text-xl font-bold text-slate-100">Debt-Equity Ratio</h2>
                        <div className="px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider flex items-center gap-2"
                             style={{ backgroundColor: `${deBadge.color}33`, borderColor: `${deBadge.color}80`, color: deBadge.textColor, border: '1px solid' }}>
                            <ShieldCheck size={14} /> {deBadge.label}
                        </div>
                    </div>
                    <div className="text-4xl font-black text-white mb-6">{typeof debtEquity === 'number' ? debtEquity.toFixed(3) : debtEquity}</div>

                    <div className="flex gap-2 mb-6">
                        <span className="text-xs bg-slate-800 border border-slate-600 px-2 py-1 rounded text-slate-300">Annual Report</span>
                    </div>

                    <div className="bg-slate-900/50 rounded-xl p-4 border border-slate-700/50 mb-4">
                        <h3 className="text-sm font-bold text-[#8892a4] uppercase mb-4 tracking-wider">Balance Sheet Computation</h3>

                        <div className="grid grid-cols-2 gap-2 text-sm text-slate-300 mb-4">
                            <div>Total Debt (from balance sheet):</div>
                            <div className="text-right font-mono">{formatCr(existingDebt)}</div>
                            <div>Net Worth (from balance sheet):</div>
                            <div className="text-right font-mono">{formatCr(netWorth)}</div>
                        </div>

                        <div className="border-t border-slate-700/50 pt-3 pb-4">
                            <div className="text-xs text-[#8892a4] mb-1">Formula: Debt / Net Worth</div>
                            <div className="font-mono text-sm text-[#00d4ff]">{formatCr(existingDebt)} / {formatCr(netWorth)} = {typeof debtEquity === 'number' ? debtEquity.toFixed(4) : debtEquity}</div>
                        </div>

                        <div className="pt-3 border-t border-slate-700/50">
                            <div className="grid grid-cols-[1fr_auto] gap-2 items-center text-xs mb-2">
                                <span className="text-slate-300">This company: {typeof debtEquity === 'number' ? debtEquity.toFixed(3) : debtEquity}</span>
                                <div className="text-[#4ade80] font-mono tracking-tighter">{debtEquity < 1 ? '████░░░░░░' : debtEquity < 2 ? '██████░░░░' : '████████░░'}</div>
                            </div>
                            <div className="grid grid-cols-[1fr_auto] gap-2 items-center text-xs text-[#8892a4] mb-1">
                                <span>Industry avg:</span>
                                <span className="font-mono">1.20</span>
                            </div>
                            <div className="grid grid-cols-[1fr_auto] gap-2 items-center text-xs text-[#8892a4]">
                                <span>Healthy range:</span>
                                <span className="font-mono">&lt; 1.0</span>
                            </div>
                        </div>
                    </div>

                    <p className="text-sm text-[#8892a4]">
                        {debtEquity < 1
                            ? `✅ Debt is ${(debtEquity * 100).toFixed(1)}% of net worth. Company owns more than it owes. Strong capital structure.`
                            : `⚠️ Debt is ${(debtEquity * 100).toFixed(1)}% of net worth. Leverage is elevated.`}
                    </p>
                </div>

                {/* CARD 3: Revenue-Expense Ratio */}
                <div className={`glass-panel p-6 border-l-4 rounded-2xl bg-[#1a2744]`} style={{ borderColor: revBadge.color }}>
                    <div className="flex justify-between items-start mb-4">
                        <div>
                            <h2 className="text-xl font-bold text-slate-100">Revenue-Expense Ratio</h2>
                            <p className="text-xs text-[#8892a4] uppercase tracking-wider mt-1">(EBITDA Margin)</p>
                        </div>
                        <div className="px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider flex items-center gap-2"
                             style={{ backgroundColor: `${revBadge.color}33`, borderColor: `${revBadge.color}80`, color: revBadge.textColor, border: '1px solid' }}>
                            <Activity size={14} /> {revBadge.label}
                        </div>
                    </div>
                    <div className="text-4xl font-black text-white mb-6">{typeof revExp === 'number' ? revExp.toFixed(3) : revExp} <span className="text-lg font-normal text-slate-400">({(revExp * 100).toFixed(1)}%)</span></div>

                    <div className="flex gap-2 mb-6">
                        <span className="text-xs bg-slate-800 border border-slate-600 px-2 py-1 rounded text-slate-300">Annual Report</span>
                    </div>

                    <div className="bg-slate-900/50 rounded-xl p-4 border border-slate-700/50 mb-4">
                        <h3 className="text-sm font-bold text-[#8892a4] uppercase mb-4 tracking-wider">P&amp;L Computation</h3>

                        <div className="grid grid-cols-2 gap-2 text-sm text-slate-300 mb-4">
                            <div>EBITDA:</div>
                            <div className="text-right font-mono">{formatCr(ebitda)}</div>
                            <div>Revenue:</div>
                            <div className="text-right font-mono">{formatCr(revenue)}</div>
                        </div>

                        <div className="border-t border-slate-700/50 pt-3 pb-4">
                            <div className="text-xs text-[#8892a4] mb-1">Formula: EBITDA / Revenue</div>
                            <div className="font-mono text-sm text-[#00d4ff]">{formatCr(ebitda)} / {formatCr(revenue)} = {typeof revExp === 'number' ? revExp.toFixed(4) : revExp}</div>
                        </div>
                    </div>

                    <p className="text-sm text-[#8892a4]">
                        {revExp >= 0.15
                            ? `✅ ${(revExp * 100).toFixed(1)}% EBITDA margin indicates strong operational efficiency.`
                            : revExp >= 0.05
                                ? `✅ ${(revExp * 100).toFixed(1)}% EBITDA margin is acceptable for the sector.`
                                : `⚠️ ${(revExp * 100).toFixed(1)}% EBITDA margin is thin. Operational efficiency needs improvement.`}
                    </p>
                </div>

                {/* CARD 4: Working Capital */}
                <div className="glass-panel p-6 border-l-4 border-[#27ae60] rounded-2xl bg-[#1a2744]">
                    <div className="flex justify-between items-start mb-4">
                        <h2 className="text-xl font-bold text-slate-100">Working Capital</h2>
                        <div className={`px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider flex items-center gap-2 ${workingCap > 0 ? 'bg-[#27ae60]/20 border-[#27ae60]/50 text-[#4ade80]' : 'bg-[#c0392b]/20 border-[#c0392b]/50 text-[#ff4d4d]'}`} style={{ border: '1px solid' }}>
                            <DollarSign size={14} /> {workingCap > 0 ? 'Positive Buffer' : 'Negative'}
                        </div>
                    </div>
                    <div className="text-4xl font-black text-white mb-6">{formatCrores(workingCap)}</div>

                    <div className="flex gap-2 mb-6">
                        <span className="text-xs bg-slate-800 border border-slate-600 px-2 py-1 rounded text-slate-300">Annual Report</span>
                    </div>

                    <div className="bg-slate-900/50 rounded-xl p-4 border border-slate-700/50 mb-4">
                        <h3 className="text-sm font-bold text-[#8892a4] uppercase mb-4 tracking-wider">Liquidity Computation</h3>

                        <div className="grid grid-cols-2 gap-2 text-sm text-slate-300 mb-4">
                            <div>Net Worth:</div>
                            <div className="text-right font-mono">{formatCr(netWorth)}</div>
                            <div>Existing Debt:</div>
                            <div className="text-right font-mono">{formatCr(existingDebt)}</div>
                        </div>

                        <div className="border-t border-slate-700/50 pt-3 pb-4">
                            <div className="text-xs text-[#8892a4] mb-1">Formula: Net Worth - Existing Debt</div>
                            <div className="font-mono text-sm text-[#00d4ff]">{formatCr(netWorth)} - {formatCr(existingDebt)} = {formatCrores(workingCap)}</div>
                        </div>

                        {(totalCredits > 0 || closingBalance > 0) && (
                            <div className="pt-3 border-t border-slate-700/50">
                                <div className="grid grid-cols-2 gap-2 text-xs text-slate-300 font-mono">
                                    {closingBalance > 0 && (
                                        <>
                                            <div>Closing Balance (bank):</div>
                                            <div className="text-right">{formatCr(closingBalance)}</div>
                                        </>
                                    )}
                                    {totalCredits > 0 && (
                                        <>
                                            <div>Total Credits (period):</div>
                                            <div className="text-right">{formatCr(totalCredits)}</div>
                                        </>
                                    )}
                                </div>
                            </div>
                        )}
                    </div>

                    <p className="text-sm text-[#8892a4]">
                        {workingCap > 0
                            ? `✅ ${formatCrores(workingCap)} working capital buffer. Company can comfortably service short-term obligations.`
                            : `⚠️ Negative working capital. Company may face liquidity pressure.`}
                    </p>
                </div>

                {/* CARD 5: Legal Flag Count */}
                <div className={`glass-panel p-6 border-l-4 rounded-2xl bg-[#1a2744]`} style={{ borderColor: legalBadge.color }}>
                    <div className="flex justify-between items-start mb-4">
                        <h2 className="text-xl font-bold text-slate-100">Legal Flag Count</h2>
                        <div className="px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider flex items-center gap-2"
                             style={{ backgroundColor: `${legalBadge.color}33`, borderColor: `${legalBadge.color}80`, color: legalBadge.textColor, border: '1px solid' }}>
                            {legalFlags === 0 ? <CheckCircle size={14} /> : <ShieldAlert size={14} />} {legalBadge.label}
                        </div>
                    </div>
                    <div className="text-4xl font-black text-white mb-6">{legalFlags}</div>

                    <div className="flex gap-2 mb-6">
                        <span className="text-xs bg-slate-800 border border-slate-600 px-2 py-1 rounded text-slate-300">All Documents</span>
                        <span className="text-xs bg-slate-800 border border-slate-600 px-2 py-1 rounded text-slate-300">Keyword Scan</span>
                    </div>

                    <div className="bg-slate-900/50 rounded-xl p-4 border border-slate-700/50 mb-4">
                        <h3 className="text-sm font-bold text-[#8892a4] uppercase mb-4 tracking-wider">Document Adverse Keyword Scan</h3>

                        {legalAdverseFlags.length > 0 ? (
                            <div className="flex flex-col gap-2 text-sm text-slate-300 mb-4">
                                {legalAdverseFlags.map((flag, i) => (
                                    <div key={i} className="grid grid-cols-[20px_1fr] gap-2 items-center">
                                        <span>🔴</span>
                                        <div className="text-xs text-red-300">{flag}</div>
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <div className="flex flex-col gap-2 text-sm text-slate-300 mb-4">
                                <div className="grid grid-cols-[20px_1fr] gap-2 items-center">
                                    <span>✅</span>
                                    <div>No adverse keywords (NPA, insolvency, fraud, NCLT, etc.) found in uploaded documents</div>
                                </div>
                            </div>
                        )}

                        <div className="pt-3 pb-1 border-t border-slate-700/50 text-xs font-mono text-[#00d4ff] flex flex-col items-end">
                            <div>Adverse keywords found: {legalFlags}</div>
                            <div className="font-bold mt-1 text-sm bg-[#00d4ff]/10 px-2 py-1 rounded">Total legal flag count: {legalFlags}</div>
                        </div>
                    </div>

                    <p className="text-sm text-[#8892a4]">
                        {legalFlags === 0
                            ? '✅ No adverse keywords detected in any uploaded documents. Clean signal.'
                            : `⚠️ ${legalFlags} adverse keyword(s) detected. This will negatively impact the credit score.`}
                    </p>
                </div>

                {/* CARD 6: Sector Risk Flag */}
                <div className={`glass-panel p-6 border-l-4 rounded-2xl bg-[#1a2744]`} style={{ borderColor: sectorBadge.color }}>
                    <div className="flex justify-between items-start mb-4">
                        <h2 className="text-xl font-bold text-slate-100">Sector Risk Flag</h2>
                        <div className="px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider flex items-center gap-2"
                             style={{ backgroundColor: `${sectorBadge.color}33`, borderColor: `${sectorBadge.color}80`, color: sectorBadge.textColor, border: '1px solid' }}>
                            <Search size={14} /> {sectorBadge.label}
                        </div>
                    </div>
                    <div className="text-4xl font-black text-white mb-6">{sectorRisk} <span className="text-lg font-normal text-slate-400">({sectorRisk === 0 ? 'Low Risk' : 'High Risk'})</span></div>

                    <div className="flex gap-2 mb-6">
                        <span className="text-xs bg-slate-800 border border-slate-600 px-2 py-1 rounded text-slate-300">Annual Report</span>
                    </div>

                    <div className="bg-slate-900/50 rounded-xl p-4 border border-slate-700/50 mb-4">
                        <h3 className="text-sm font-bold text-[#8892a4] uppercase mb-4 tracking-wider">Sector Classification</h3>

                        <div className="grid grid-cols-[110px_1fr] gap-2 text-sm text-slate-300 mb-4 font-mono">
                            <div className="text-[#8892a4]">Detected sector:</div>
                            <div className="text-white">"{sectorName}"</div>
                            <div className="text-[#8892a4]">Auditor opinion:</div>
                            <div className="text-white">{auditorQual}</div>
                        </div>

                        <div className="border-t border-slate-700/50 pt-4">
                            <div className="grid grid-cols-3 gap-2 text-xs font-bold text-[#8892a4] border-b border-slate-700 pb-2 mb-2">
                                <div>Sector</div>
                                <div>Risk Level</div>
                                <div>Flag Value</div>
                            </div>
                            <div className="flex flex-col gap-1 text-xs font-mono">
                                <div className={`grid grid-cols-3 gap-2 rounded px-1 py-1 ${sectorRisk === 0 ? 'text-[#00d4ff] bg-slate-800' : 'text-red-400 bg-red-950/30'}`}>
                                    <div>{sectorName}</div><div>{sectorRisk === 0 ? 'LOW/MEDIUM' : 'HIGH'}</div><div>{sectorRisk} ← This company</div>
                                </div>
                                <div className="grid grid-cols-3 gap-2 text-slate-400 px-1">
                                    <div>Real Estate</div><div>HIGH</div><div>1</div>
                                </div>
                                <div className="grid grid-cols-3 gap-2 text-slate-400 px-1">
                                    <div>Crypto / Web3</div><div>VERY HIGH</div><div>1</div>
                                </div>
                                <div className="grid grid-cols-3 gap-2 text-slate-400 px-1">
                                    <div>FMCG / IT</div><div>LOW</div><div>0</div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <p className="text-sm text-[#8892a4]">
                        {sectorRisk === 0
                            ? `✅ "${sectorName}" classified as acceptable risk sector. Flag = 0.`
                            : `⚠️ "${sectorName}" classified as high-risk sector. Flag = 1, score will decrease by ~8 pts.`}
                    </p>
                </div>
            </div>

            {/* BOTTOM SUMMARY BAR */}
            <div className="glass-panel p-6 border-t-2 border-[#00d4ff] rounded-2xl bg-[#1a2744] mt-4 flex flex-col md:flex-row justify-between items-center gap-6">
                <div className="flex-grow">
                    <h2 className="text-lg font-bold text-white mb-4">Feature Summary — Ready for ML Engine</h2>

                    <div className="flex flex-wrap gap-3 mb-4 font-mono text-sm">
                        <div className="bg-slate-900 border border-slate-700 px-3 py-1.5 rounded flex items-center gap-2">
                            <span className="text-slate-400">gst_bank_match:</span>
                            <span className="text-white">{gstMatch.toFixed(2)}</span>
                            <span>{gstMatch >= 0.7 ? '🟢' : '🔴'}</span>
                        </div>
                        <div className="bg-slate-900 border border-slate-700 px-3 py-1.5 rounded flex items-center gap-2">
                            <span className="text-slate-400">debt_equity:</span>
                            <span className="text-white">{typeof debtEquity === 'number' ? debtEquity.toFixed(3) : debtEquity}</span>
                            <span>{debtEquity < 1.5 ? '🟢' : '🔴'}</span>
                        </div>
                        <div className="bg-slate-900 border border-slate-700 px-3 py-1.5 rounded flex items-center gap-2">
                            <span className="text-slate-400">revenue_exp:</span>
                            <span className="text-white">{typeof revExp === 'number' ? revExp.toFixed(3) : revExp}</span>
                            <span>{revExp > 0.05 ? '🟢' : '🔴'}</span>
                        </div>
                        <div className="bg-slate-900 border border-slate-700 px-3 py-1.5 rounded flex items-center gap-2">
                            <span className="text-slate-400">working_cap:</span>
                            <span className="text-white">{formatCrores(workingCap)}</span>
                            <span>{workingCap > 0 ? '🟢' : '🔴'}</span>
                        </div>
                        <div className="bg-slate-900 border border-slate-700 px-3 py-1.5 rounded flex items-center gap-2">
                            <span className="text-slate-400">legal_flags:</span>
                            <span className="text-white">{legalFlags}</span>
                            <span>{legalFlags === 0 ? '🟢' : '🔴'}</span>
                        </div>
                        <div className="bg-slate-900 border border-slate-700 px-3 py-1.5 rounded flex items-center gap-2">
                            <span className="text-slate-400">sector_risk:</span>
                            <span className="text-white">{sectorRisk}</span>
                            <span>{sectorRisk === 0 ? '🟢' : '🔴'}</span>
                        </div>
                    </div>

                    <p className="text-sm text-[#8892a4] max-w-2xl leading-relaxed">
                        <strong className="text-white">{healthyCount} of 6 features show healthy signals.</strong><br />
                        {riskCount > 0 ? `${riskCount} feature(s) show risk signals.` : 'All features are in healthy range.'}<br />
                        These 6 values will now be passed to the LightGBM model to compute the credit score.
                    </p>
                </div>

                <div className="flex-shrink-0">
                    <button onClick={handleRunML} className="btn-primary w-full md:w-auto flex items-center gap-2 px-8 py-4 text-lg font-bold bg-[#00d4ff] text-slate-900 hover:bg-[#00b8e6] shadow-[0_0_20px_rgba(0,212,255,0.3)] transition-all hover:scale-105">
                        Run ML Scoring Engine <ArrowRight size={24} />
                    </button>
                </div>
            </div>

        </div>
    );
}
