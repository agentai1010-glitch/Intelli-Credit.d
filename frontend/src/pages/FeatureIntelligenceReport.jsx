import { useNavigate, useLocation } from 'react-router-dom';
import { ShieldAlert, ArrowRight, ShieldCheck, Activity, CheckCircle, Search, DollarSign } from 'lucide-react';
import { useAppContext } from '../context/AppContext';

export default function FeatureIntelligenceReport() {
    const navigate = useNavigate();
    const { sessionData } = useAppContext();
    const location = useLocation();

    // The raw data from context or state
    const features = sessionData?.features || {};

    // Computation placeholders aligned with Sharma Textile mock
    const debtEquity = features.net_worth ? ((features.existing_debt || 82000000) / features.net_worth).toFixed(3) : 0.586;
    const revExp = features.revenue ? ((features.ebitda || 6100000) / features.revenue).toFixed(3) : 0.143;
    const workingCap = features.net_worth ? (features.net_worth - (features.existing_debt || 82000000)) : 58000000;
    const formatCr = (val) => `₹${(val / 10000000).toFixed(2)}Cr`;

    const handleRunML = () => {
        // Pass the state forward just in case, though ScoreView relies on Session Context
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
                        How your documents translate into ML features for {sessionData?.companyName || 'Sharma Textile Mills Pvt. Ltd.'}
                    </p>
                </div>
                <button onClick={handleRunML} className="btn-primary flex items-center gap-2 px-6 py-3 font-bold bg-[#00d4ff] text-slate-900 shadow-[0_0_20px_rgba(0,212,255,0.3)] hover:bg-[#00b8e6]">
                    Run ML Scoring <ArrowRight size={20} />
                </button>
            </header>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

                {/* CARD 1: GST Bank Match Score */}
                <div className="glass-panel p-6 border-l-4 border-[#c0392b] rounded-2xl bg-[#1a2744]">
                    <div className="flex justify-between items-start mb-4">
                        <div>
                            <h2 className="text-xl font-bold text-slate-100">GST Bank Match Score</h2>
                        </div>
                        <div className="bg-[#c0392b]/20 border border-[#c0392b]/50 text-[#ff4d4d] px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider flex items-center gap-2">
                            <ShieldAlert size={14} /> Fraud Risk Detected
                        </div>
                    </div>
                    <div className="text-4xl font-black text-white mb-6">0.58 / 1.00</div>

                    <div className="flex gap-2 mb-6">
                        <span className="text-xs bg-slate-800 border border-slate-600 px-2 py-1 rounded text-slate-300">GSTR-3B</span>
                        <span className="text-xs bg-slate-800 border border-slate-600 px-2 py-1 rounded text-slate-300">GSTR-2A</span>
                        <span className="text-xs bg-slate-800 border border-slate-600 px-2 py-1 rounded text-slate-300">Bank Statement</span>
                    </div>

                    <div className="bg-slate-900/50 rounded-xl p-4 border border-slate-700/50 mb-4">
                        <h3 className="text-sm font-bold text-[#8892a4] uppercase mb-4 tracking-wider">Reconciliation Findings</h3>

                        <div className="flex flex-col gap-4">
                            <div className="flex justify-between items-start gap-4">
                                <div className="text-red-400 mt-1">🔴</div>
                                <div className="flex-grow">
                                    <div className="flex justify-between">
                                        <span className="font-bold text-slate-200 uppercase text-sm">CIRCULAR_TRADING_RISK</span>
                                        <span className="text-red-400 font-bold text-sm">HIGH</span>
                                        <span className="font-mono text-slate-400 text-sm">-20 pts</span>
                                    </div>
                                    <p className="text-xs text-slate-400 mt-1">ITC claimed ₹58L vs available ₹42L</p>
                                    <p className="text-xs text-slate-400">Gap: 38.1% (threshold: &gt;20% = HIGH)</p>
                                </div>
                            </div>

                            <div className="flex justify-between items-start gap-4">
                                <div className="text-amber-400 mt-1">🟡</div>
                                <div className="flex-grow">
                                    <div className="flex justify-between">
                                        <span className="font-bold text-slate-200 uppercase text-sm">REVENUE_MISMATCH</span>
                                        <span className="text-amber-400 font-bold text-sm">MEDIUM</span>
                                        <span className="font-mono text-slate-400 text-sm">-7 pts</span>
                                    </div>
                                    <p className="text-xs text-slate-400 mt-1">GST turnover ₹3.85Cr vs Bank credits ₹3.55Cr</p>
                                    <p className="text-xs text-slate-400">Gap: 8.45% (threshold: 5-15% = MEDIUM)</p>
                                </div>
                            </div>

                            <div className="flex justify-between items-start gap-4">
                                <div className="text-red-400 mt-1">🔴</div>
                                <div className="flex-grow">
                                    <div className="flex justify-between">
                                        <span className="font-bold text-slate-200 uppercase text-sm">SUSPICIOUS_TRANSACTIONS</span>
                                        <span className="text-red-400 font-bold text-sm">HIGH</span>
                                        <span className="font-mono text-slate-400 text-sm">-15 pts</span>
                                    </div>
                                    <p className="text-xs text-slate-400 mt-1">3x round ₹50,00,000 transactions detected</p>
                                    <p className="text-xs text-slate-400">Jun-12, Jul-11, Sep-04 (same amount, same period)</p>
                                </div>
                            </div>
                        </div>

                        <div className="mt-4 pt-4 border-t border-slate-700/50 font-mono text-xs text-slate-300 space-y-1">
                            <div>Reconciliation Score: 100 - 20 - 7 - 15 = 58/100</div>
                            <div className="text-[#00d4ff]">Feature value passed to ML: 58/100 = 0.58</div>
                        </div>
                    </div>

                    <p className="text-sm text-[#8892a4]">
                        ⚠️ This is the only feature showing risk. GST fraud signals detected will reduce the credit score by approximately 8-12 points.
                    </p>
                </div>

                {/* CARD 2: Debt-Equity Ratio */}
                <div className="glass-panel p-6 border-l-4 border-[#27ae60] rounded-2xl bg-[#1a2744]">
                    <div className="flex justify-between items-start mb-4">
                        <div>
                            <h2 className="text-xl font-bold text-slate-100">Debt-Equity Ratio</h2>
                        </div>
                        <div className="bg-[#27ae60]/20 border border-[#27ae60]/50 text-[#4ade80] px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider flex items-center gap-2">
                            <ShieldCheck size={14} /> Healthy Leverage
                        </div>
                    </div>
                    <div className="text-4xl font-black text-white mb-6">{debtEquity}</div>

                    <div className="flex gap-2 mb-6">
                        <span className="text-xs bg-slate-800 border border-slate-600 px-2 py-1 rounded text-slate-300">Annual Report</span>
                    </div>

                    <div className="bg-slate-900/50 rounded-xl p-4 border border-slate-700/50 mb-4">
                        <h3 className="text-sm font-bold text-[#8892a4] uppercase mb-4 tracking-wider">Balance Sheet Computation</h3>

                        <div className="grid grid-cols-2 gap-2 text-sm text-slate-300 mb-4">
                            <div>Total Debt (from balance sheet):</div>
                            <div className="text-right font-mono">₹8.20 Cr</div>
                            <div>Net Worth (from balance sheet):</div>
                            <div className="text-right font-mono">₹14.00 Cr</div>
                        </div>

                        <div className="border-t border-slate-700/50 pt-3 pb-4">
                            <div className="text-xs text-[#8892a4] mb-1">Formula: Debt ÷ Net Worth</div>
                            <div className="font-mono text-sm text-[#00d4ff]">₹8.2Cr ÷ ₹14Cr = 0.586</div>
                        </div>

                        <div className="pt-3 border-t border-slate-700/50">
                            <div className="grid grid-cols-[1fr_auto] gap-2 items-center text-xs mb-2">
                                <span className="text-slate-300">This company: {debtEquity}</span>
                                <div className="text-[#4ade80] font-mono tracking-tighter">████░░░░░░</div>
                            </div>
                            <div className="grid grid-cols-[1fr_auto] gap-2 items-center text-xs text-[#8892a4] mb-1">
                                <span>Industry avg (textile sector):</span>
                                <span className="font-mono">1.20</span>
                            </div>
                            <div className="grid grid-cols-[1fr_auto] gap-2 items-center text-xs text-[#8892a4]">
                                <span>Healthy range:</span>
                                <span className="font-mono">&lt; 1.0</span>
                            </div>
                        </div>
                    </div>

                    <p className="text-sm text-[#8892a4]">
                        ✅ Debt is 58.6% of net worth. Company owns more than it owes. Strong capital structure.
                    </p>
                </div>

                {/* CARD 3: Revenue-Expense Ratio */}
                <div className="glass-panel p-6 border-l-4 border-[#27ae60] rounded-2xl bg-[#1a2744]">
                    <div className="flex justify-between items-start mb-4">
                        <div>
                            <h2 className="text-xl font-bold text-slate-100">Revenue-Expense Ratio</h2>
                            <p className="text-xs text-[#8892a4] uppercase tracking-wider mt-1">(EBITDA Margin)</p>
                        </div>
                        <div className="bg-[#27ae60]/20 border border-[#27ae60]/50 text-[#4ade80] px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider flex items-center gap-2">
                            <Activity size={14} /> Decent Margin
                        </div>
                    </div>
                    <div className="text-4xl font-black text-white mb-6">{revExp} <span className="text-lg font-normal text-slate-400">({(revExp * 100).toFixed(1)}%)</span></div>

                    <div className="flex gap-2 mb-6">
                        <span className="text-xs bg-slate-800 border border-slate-600 px-2 py-1 rounded text-slate-300">Annual Report</span>
                    </div>

                    <div className="bg-slate-900/50 rounded-xl p-4 border border-slate-700/50 mb-4">
                        <h3 className="text-sm font-bold text-[#8892a4] uppercase mb-4 tracking-wider">P&amp;L Computation</h3>

                        <div className="grid grid-cols-2 gap-2 text-sm text-slate-300 mb-4">
                            <div>EBITDA (FY2025):</div>
                            <div className="text-right font-mono">₹6.10 Cr</div>
                            <div>Revenue (FY2025):</div>
                            <div className="text-right font-mono">₹42.50 Cr</div>
                        </div>

                        <div className="border-t border-slate-700/50 pt-3 pb-4">
                            <div className="text-xs text-[#8892a4] mb-1">Formula: EBITDA ÷ Revenue</div>
                            <div className="font-mono text-sm text-[#00d4ff]">₹6.1Cr ÷ ₹42.5Cr = 0.1435</div>
                        </div>

                        <div className="pt-3 border-t border-slate-700/50 text-xs font-mono space-y-2">
                            <div className="text-[#8892a4]">FY2023: ₹4.2Cr / ₹35Cr = 12.0% →</div>
                            <div className="text-[#8892a4]">FY2024: ₹4.8Cr / ₹38Cr = 12.6% →</div>
                            <div className="text-[#4ade80]">FY2025: ₹6.1Cr / ₹42.5Cr = 14.3% ↑ improving</div>
                        </div>
                    </div>

                    <p className="text-sm text-[#8892a4]">
                        ✅ 14.3% EBITDA margin with improving 3-year trend. Revenue growing ₹35Cr → ₹42.5Cr over 3 years (+21%). Positive operating leverage.
                    </p>
                </div>

                {/* CARD 4: Working Capital */}
                <div className="glass-panel p-6 border-l-4 border-[#27ae60] rounded-2xl bg-[#1a2744]">
                    <div className="flex justify-between items-start mb-4">
                        <div>
                            <h2 className="text-xl font-bold text-slate-100">Working Capital</h2>
                        </div>
                        <div className="bg-[#27ae60]/20 border border-[#27ae60]/50 text-[#4ade80] px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider flex items-center gap-2">
                            <DollarSign size={14} /> Positive Buffer
                        </div>
                    </div>
                    <div className="text-4xl font-black text-white mb-6">{formatCr(workingCap)}</div>

                    <div className="flex gap-2 mb-6">
                        <span className="text-xs bg-slate-800 border border-slate-600 px-2 py-1 rounded text-slate-300">Annual Report</span>
                    </div>

                    <div className="bg-slate-900/50 rounded-xl p-4 border border-slate-700/50 mb-4">
                        <h3 className="text-sm font-bold text-[#8892a4] uppercase mb-4 tracking-wider">Liquidity Computation</h3>

                        <div className="grid grid-cols-2 gap-2 text-sm text-slate-300 mb-4">
                            <div>Net Worth:</div>
                            <div className="text-right font-mono">₹14.00 Cr</div>
                            <div>Existing Debt:</div>
                            <div className="text-right font-mono">₹8.20 Cr</div>
                        </div>

                        <div className="border-t border-slate-700/50 pt-3 pb-4">
                            <div className="text-xs text-[#8892a4] mb-1">Formula: Net Worth - Existing Debt</div>
                            <div className="font-mono text-sm text-[#00d4ff]">₹14Cr - ₹8.2Cr = ₹5.80Cr</div>
                        </div>

                        <div className="pt-3 border-t border-slate-700/50">
                            <div className="grid grid-cols-2 gap-2 text-xs text-slate-300 font-mono">
                                <div>Closing Balance (bank):</div>
                                <div className="text-right">₹12.45 L  ← actual cash</div>
                                <div>Total Credits (period):</div>
                                <div className="text-right">₹3.55 Cr  ← inflow</div>
                                <div>Total Debits (period):</div>
                                <div className="text-right">₹3.43 Cr  ← outflow</div>
                                <div className="font-bold text-[#4ade80] pt-1">Net cash flow:</div>
                                <div className="font-bold text-right text-[#4ade80] pt-1">+₹0.12 Cr ← positive</div>
                            </div>
                        </div>
                    </div>

                    <p className="text-sm text-[#8892a4]">
                        ✅ ₹5.8Cr working capital buffer. Company can comfortably service short-term obligations. Bank statement confirms positive cash flow.
                    </p>
                </div>

                {/* CARD 5: Legal Flag Count */}
                <div className="glass-panel p-6 border-l-4 border-[#27ae60] rounded-2xl bg-[#1a2744]">
                    <div className="flex justify-between items-start mb-4">
                        <div>
                            <h2 className="text-xl font-bold text-slate-100">Legal Flag Count</h2>
                        </div>
                        <div className="bg-[#27ae60]/20 border border-[#27ae60]/50 text-[#4ade80] px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider flex items-center gap-2">
                            <CheckCircle size={14} /> No Legal Risk
                        </div>
                    </div>
                    <div className="text-4xl font-black text-white mb-6">0</div>

                    <div className="flex gap-2 mb-6">
                        <span className="text-xs bg-slate-800 border border-slate-600 px-2 py-1 rounded text-slate-300">All Documents</span>
                        <span className="text-xs bg-slate-800 border border-slate-600 px-2 py-1 rounded text-slate-300">Regulatory Crawl</span>
                    </div>

                    <div className="bg-slate-900/50 rounded-xl p-4 border border-slate-700/50 mb-4">
                        <h3 className="text-sm font-bold text-[#8892a4] uppercase mb-4 tracking-wider">Legal Check Sources</h3>

                        <div className="flex flex-col gap-2 text-sm text-slate-300 mb-4">
                            <div className="grid grid-cols-[20px_1fr_auto] gap-2 items-center">
                                <span>✅</span>
                                <div>MCA Portal</div>
                                <div className="text-xs text-[#8892a4]">No compliance violations</div>
                            </div>
                            <div className="grid grid-cols-[20px_1fr_auto] gap-2 items-center">
                                <span>✅</span>
                                <div>eCourts Services</div>
                                <div className="text-xs text-[#8892a4]">No active cases found</div>
                            </div>
                            <div className="grid grid-cols-[20px_1fr_auto] gap-2 items-center">
                                <span>✅</span>
                                <div>RBI Defaulter List</div>
                                <div className="text-xs text-[#8892a4]">Not listed</div>
                            </div>
                            <div className="grid grid-cols-[20px_1fr_auto] gap-2 items-center">
                                <span>✅</span>
                                <div>IBBI Insolvency</div>
                                <div className="text-xs text-[#8892a4]">No insolvency proceedings</div>
                            </div>
                            <div className="grid grid-cols-[20px_1fr_auto] gap-2 pt-2 border-t border-slate-700/50">
                                <span>✅</span>
                                <div>Document Scan</div>
                                <div className="text-xs text-[#8892a4] text-right">No LEGAL_NOTICE type detected<br />in uploaded documents</div>
                            </div>
                        </div>

                        <div className="pt-3 pb-1 border-t border-slate-700/50 text-xs font-mono text-[#00d4ff] flex flex-col items-end">
                            <div>Legal documents found: 0</div>
                            <div>Regulatory alerts: 0</div>
                            <div className="font-bold mt-1 text-sm bg-[#00d4ff]/10 px-2 py-1 rounded">Total legal flag count: 0</div>
                        </div>
                    </div>

                    <p className="text-sm text-[#8892a4]">
                        ✅ Clean legal record across all 4 regulatory databases. No litigation risk detected. This is a strong positive signal.
                    </p>
                </div>

                {/* CARD 6: Sector Risk Flag */}
                <div className="glass-panel p-6 border-l-4 border-[#27ae60] rounded-2xl bg-[#1a2744]">
                    <div className="flex justify-between items-start mb-4">
                        <div>
                            <h2 className="text-xl font-bold text-slate-100">Sector Risk Flag</h2>
                        </div>
                        <div className="bg-[#27ae60]/20 border border-[#27ae60]/50 text-[#4ade80] px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider flex items-center gap-2">
                            <Search size={14} /> Acceptable Sector
                        </div>
                    </div>
                    <div className="text-4xl font-black text-white mb-6">0 <span className="text-lg font-normal text-slate-400">(Low Risk)</span></div>

                    <div className="flex gap-2 mb-6">
                        <span className="text-xs bg-slate-800 border border-slate-600 px-2 py-1 rounded text-slate-300">Annual Report</span>
                    </div>

                    <div className="bg-slate-900/50 rounded-xl p-4 border border-slate-700/50 mb-4">
                        <h3 className="text-sm font-bold text-[#8892a4] uppercase mb-4 tracking-wider">Sector Classification</h3>

                        <div className="grid grid-cols-[110px_1fr] gap-2 text-sm text-slate-300 mb-4 font-mono">
                            <div className="text-[#8892a4]">Detected sector:</div>
                            <div className="text-white">"Textile Manufacturing"</div>
                            <div className="text-[#8892a4]">Detection source:</div>
                            <div>Annual Report header + NLP</div>
                            <div className="text-[#8892a4]">Detected keywords:</div>
                            <div className="text-[#00d4ff]">["textile", "fabric", "manufacturing", "Surat"]</div>
                        </div>

                        <div className="border-t border-slate-700/50 pt-4">
                            <div className="grid grid-cols-3 gap-2 text-xs font-bold text-[#8892a4] border-b border-slate-700 pb-2 mb-2">
                                <div>Sector</div>
                                <div>Risk Level</div>
                                <div>Flag Value</div>
                            </div>
                            <div className="flex flex-col gap-1 text-xs font-mono">
                                <div className="grid grid-cols-3 gap-2 text-[#00d4ff] bg-slate-800 rounded px-1 py-1">
                                    <div>Textile Manuf.</div><div>MEDIUM</div><div>0  ← This company</div>
                                </div>
                                <div className="grid grid-cols-3 gap-2 text-slate-400 px-1">
                                    <div>FMCG / Consumer</div><div>LOW</div><div>0</div>
                                </div>
                                <div className="grid grid-cols-3 gap-2 text-slate-400 px-1">
                                    <div>IT / Software</div><div>LOW</div><div>0</div>
                                </div>
                                <div className="grid grid-cols-3 gap-2 text-slate-400 px-1">
                                    <div>Real Estate</div><div>HIGH</div><div>1</div>
                                </div>
                                <div className="grid grid-cols-3 gap-2 text-slate-400 px-1">
                                    <div>Crypto / Web3</div><div>VERY HIGH</div><div>1</div>
                                </div>
                                <div className="grid grid-cols-3 gap-2 text-slate-400 px-1">
                                    <div>Infrastructure</div><div>HIGH</div><div>1</div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <p className="text-sm text-[#8892a4]">
                        ✅ Textile manufacturing classified as medium risk sector. Flag = 0 (acceptable). If sector were Real Estate or Crypto, flag = 1 and score would decrease by ~8 pts.
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
                            <span className="text-white">0.58</span>
                            <span className="text-red-500">🔴</span>
                        </div>
                        <div className="bg-slate-900 border border-slate-700 px-3 py-1.5 rounded flex items-center gap-2">
                            <span className="text-slate-400">debt_equity:</span>
                            <span className="text-white">{debtEquity}</span>
                            <span className="text-emerald-500">🟢</span>
                        </div>
                        <div className="bg-slate-900 border border-slate-700 px-3 py-1.5 rounded flex items-center gap-2">
                            <span className="text-slate-400">revenue_exp:</span>
                            <span className="text-white">{revExp}</span>
                            <span className="text-emerald-500">🟢</span>
                        </div>
                        <div className="bg-slate-900 border border-slate-700 px-3 py-1.5 rounded flex items-center gap-2">
                            <span className="text-slate-400">working_cap:</span>
                            <span className="text-white">{formatCr(workingCap)}</span>
                            <span className="text-emerald-500">🟢</span>
                        </div>
                        <div className="bg-slate-900 border border-slate-700 px-3 py-1.5 rounded flex items-center gap-2">
                            <span className="text-slate-400">legal_flags:</span>
                            <span className="text-white">0</span>
                            <span className="text-emerald-500">🟢</span>
                        </div>
                        <div className="bg-slate-900 border border-slate-700 px-3 py-1.5 rounded flex items-center gap-2">
                            <span className="text-slate-400">sector_risk:</span>
                            <span className="text-white">0</span>
                            <span className="text-emerald-500">🟢</span>
                        </div>
                    </div>

                    <p className="text-sm text-[#8892a4] max-w-2xl leading-relaxed">
                        <strong className="text-white">5 of 6 features show healthy signals.</strong><br />
                        1 feature (GST Bank Match) shows fraud risk.<br />
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
