import { useState, useEffect } from 'react';
import { Outlet, NavLink, useLocation } from 'react-router-dom';
import {
    UploadCloud, CheckCircle, Search, FileText,
    History, LogOut, User, BarChart2, Sliders
} from 'lucide-react';
import { useAppContext } from '../context/AppContext';

const Sidebar = () => {
    const { sessionData, updateSession } = useAppContext();
    const location = useLocation();

    // Manage routing cache locally to remember state when revisiting
    const [visitedStates, setVisitedStates] = useState(() => {
        try {
            const saved = sessionStorage.getItem('intelli_visited_routes');
            if (saved) return JSON.parse(saved);
        } catch (e) { }
        return { '/': null }; // Ingestion is always unlocked
    });

    useEffect(() => {
        // Only update if we are visiting a new path, or if we want to update the state of a current path
        if (!visitedStates[location.pathname] || location.state) {
            setVisitedStates(prev => {
                const next = { ...prev, [location.pathname]: location.state || prev[location.pathname] };
                sessionStorage.setItem('intelli_visited_routes', JSON.stringify(next));
                return next;
            });
        }
    }, [location.pathname, location.state]);

    const steps = [
        { name: 'Document Ingestion', path: '/', icon: UploadCloud },
        { name: 'Feature Intelligence', path: '/feature-intelligence', icon: BarChart2 },
        { name: 'Credit Scoring', path: '/score', icon: CheckCircle },
        { name: 'Qualitative Adjustments', path: '/qualitative-input', icon: Sliders },
        { name: 'External Evidence', path: '/evidence', icon: Search },
        { name: 'CAM Generation', path: '/cam', icon: FileText },
        { name: 'Report History', path: '/history', icon: History },
    ];

    const isUnlocked = (path) => Object.prototype.hasOwnProperty.call(visitedStates, path) || path === '/history'; // Allow history manually if needed

    return (
        <div className="w-64 h-full bg-slate-900 border-r border-slate-700/50 flex flex-col pt-8 px-4 flex-shrink-0 relative overflow-hidden">
            {/* Decorative gradient blob */}
            <div className="absolute top-0 left-0 w-64 h-64 bg-blue-500/10 rounded-full blur-3xl pointer-events-none -translate-x-1/2 -translate-y-1/2"></div>

            <div className="mb-10 z-10 flex items-center gap-2">
                <div className="p-2 bg-blue-500/20 rounded-lg text-blue-400">
                    <FileText size={24} />
                </div>
                <h1 className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-indigo-300 tracking-tight">
                    Intelli-Credit
                </h1>
            </div>

            <nav className="flex-1 z-10 relative">
                {/* Vertical timeline connector */}
                <div className="absolute left-[21px] top-6 bottom-6 w-0.5 bg-slate-800 -z-10"></div>

                <div className="space-y-2 relative">
                    {steps.map((step) => {
                        const unlocked = isUnlocked(step.path);
                        const isCurrent = location.pathname === step.path;

                        return (
                            <div key={step.path} className="relative">
                                {/* Timeline Dot */}
                                <div className={`absolute left-[18px] top-1/2 -translate-y-1/2 w-2 h-2 rounded-full border-2 z-10 transition-colors duration-300
                                    ${isCurrent ? 'bg-blue-400 border-blue-400 shadow-[0_0_10px_rgba(59,130,246,0.5)]'
                                        : unlocked ? 'bg-emerald-400 border-emerald-400'
                                            : 'bg-slate-800 border-slate-700'}
                                `}></div>

                                {unlocked ? (
                                    <NavLink
                                        to={step.path}
                                        state={visitedStates[step.path]}
                                        className={({ isActive }) =>
                                            `flex items-center gap-3 pl-10 pr-4 py-3 rounded-lg transition-all duration-300 font-medium overflow-hidden relative group ` +
                                            (isActive
                                                ? 'bg-blue-600/10 text-blue-400 shadow-[0_0_10px_rgba(59,130,246,0.1)] border border-blue-500/10'
                                                : 'text-slate-300 hover:text-white hover:bg-white/5 border border-transparent')
                                        }
                                    >
                                        <step.icon size={18} className="z-10" />
                                        <span className="z-10 text-[13px]">{step.name}</span>
                                        <div className="absolute top-0 left-0 w-full h-full bg-gradient-to-r from-white/0 via-white/5 to-white/0 translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-700 pointer-events-none"></div>
                                    </NavLink>
                                ) : (
                                    <div
                                        className="flex items-center gap-3 pl-10 pr-4 py-3 rounded-lg font-medium text-slate-600 cursor-not-allowed border border-transparent"
                                        title="Complete previous steps first"
                                    >
                                        <step.icon size={18} />
                                        <span className="text-[13px]">{step.name}</span>
                                    </div>
                                )}
                            </div>
                        );
                    })}
                </div>
            </nav>

            <div className="mt-auto mb-6 text-xs text-slate-500 z-10">
                <div className="flex items-center gap-2 justify-between bg-slate-800/50 py-2 px-3 rounded-lg border border-slate-700/80 mb-4 shadow-sm">
                    <div className="flex items-center gap-2 overflow-hidden text-slate-300">
                        <User size={14} className="text-slate-400 flex-shrink-0" />
                        <span className="truncate max-w-[120px] font-medium" title={sessionData?.user?.email}>
                            {sessionData?.user?.email?.split('@')[0] || "Analyst"}
                        </span>
                    </div>
                    <button
                        onClick={() => updateSession({ user: null })}
                        className="text-slate-500 hover:text-rose-400 p-1.5 transition-colors cursor-pointer rounded-md hover:bg-rose-500/10"
                        title="Sign Out"
                    >
                        <LogOut size={16} />
                    </button>
                </div>
                <div className="px-1 space-y-1">
                    <p>AI Appraised • Secure</p>
                    <p>Intelli-Credit Engine v1.0</p>
                </div>
            </div>
        </div>
    );
};

export default function Layout() {
    return (
        <div className="flex h-screen w-full bg-[#0a0f1d] overflow-hidden text-slate-200 selection:bg-blue-500/30">
            {/* Global decorative background elements */}
            <div className="fixed top-1/4 right-0 w-96 h-96 bg-indigo-500/5 rounded-full blur-[100px] pointer-events-none"></div>
            <div className="fixed bottom-0 left-1/4 w-[30rem] h-[30rem] bg-emerald-500/5 rounded-full blur-[120px] pointer-events-none"></div>

            <Sidebar />
            <div className="flex-1 flex flex-col h-full relative z-10 overflow-hidden">
                <main className="flex-1 overflow-x-hidden overflow-y-auto w-full p-8 custom-scrollbar">
                    <div className="max-w-6xl mx-auto h-full animate-in fade-in duration-500">
                        <Outlet />
                    </div>
                </main>
            </div>
        </div>
    );
}
