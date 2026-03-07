import { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { UploadCloud, FileType, CheckCircle, ArrowRight, Loader2 } from 'lucide-react';
import { uploadDocuments } from '../api';
import { useAppContext } from '../context/AppContext';

export default function UploadPage() {
    const [files, setFiles] = useState([]);
    const [progressStep, setProgressStep] = useState(0);
    const [parsedResults, setParsedResults] = useState([]);
    const [rawResponse, setRawResponse] = useState(null);
    const [error, setError] = useState(null);
    const { updateSession } = useAppContext();
    const navigate = useNavigate();

    const handleDrop = useCallback((e) => {
        e.preventDefault();
        const droppedFiles = Array.from(e.dataTransfer.files).filter(
            (f) => f.type === 'application/pdf' || f.name.endsWith('.pdf')
        );
        setFiles((prev) => [...prev, ...droppedFiles]);
    }, []);

    const handleFileChange = (e) => {
        if (e.target.files) {
            setFiles((prev) => [...prev, ...Array.from(e.target.files)]);
        }
    };

    const removeFile = (idx) => {
        const newFiles = [...files];
        newFiles.splice(idx, 1);
        setFiles(newFiles);
    };

    const handleUpload = async () => {
        if (files.length === 0) return;
        setProgressStep(1);
        setError(null);
        try {
            const response = await uploadDocuments(files);
            setRawResponse(response);

            // Mocking the downstream pipeline steps for the UI
            setProgressStep(2); // Type Detection
            await new Promise(r => setTimeout(r, 800));

            // Map backend results to frontend presentation format
            const results = response.processed_files.map((f) => {
                let type = f.document_type || "UNKNOWN";
                let conf = f.confidence || 0.0;
                let fields = f.extracted_fields?.display || ["No specific fields extracted yet"];

                return { file: f, type, conf, fields };
            });

            setProgressStep(3); // Field Extraction
            await new Promise(r => setTimeout(r, 800));

            setProgressStep(4); // Cross-Verification
            await new Promise(r => setTimeout(r, 800));

            setParsedResults(results);
            setProgressStep(5); // Complete

        } catch (err) {
            console.error(err);
            const detail = err?.response?.data?.detail || err?.message || 'Unknown error';
            setError(`Upload failed: ${detail}`);
            setProgressStep(0);
        }
    };

    const handleContinueToScore = () => {
        if (!rawResponse) return;
        const allText = rawResponse.processed_files.map(f => {
            let text = f.raw_ocr || "";
            if (f.extracted_text_blocks && f.extracted_text_blocks.length > 0) {
                text += " " + f.extracted_text_blocks.map(b => b.text).join(' ');
            }
            return text;
        }).join(' ');

        const firstLine = allText.split('\n').map(l => l.trim()).filter(l => l.length > 5)[0] || "Unknown Entity";
        const cleanCompanyName = firstLine.replace(/[^a-zA-Z0-9\s]/g, '').slice(0, 50).trim();

        updateSession({
            companyName: cleanCompanyName,
            uploadedDocuments: rawResponse.processed_files,
            rawText: allText,
            features: {},
            scoreResult: null,
            nlpEntities: [],
            evidence: [],
            camUrl: null
        });

        navigate('/score');
    };

    return (
        <div className="flex flex-col gap-8 w-full max-w-4xl mx-auto py-10">
            <header>
                <h1 className="text-4xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-emerald-400 tracking-tight mb-2">
                    Ingest Financial Documents
                </h1>
                <p className="text-slate-400 text-lg">
                    Upload PDF Annual Reports, GST Returns, or Bank Statements to trigger the smart OCR and Layout Extractor.
                </p>
            </header>

            {error && (
                <div className="p-4 bg-red-500/10 border border-red-500/20 text-red-400 rounded-xl flex items-center gap-3">
                    <div className="w-2 h-2 rounded-full bg-red-400 animate-pulse"></div>
                    {error}
                </div>
            )}

            {progressStep === 0 && (
                <div
                    className="glass-panel p-10 flex flex-col items-center justify-center border-dashed border-2 hover:border-blue-500/50 transition-colors duration-300 cursor-pointer min-h-[300px] relative overflow-hidden group"
                    onDragOver={(e) => e.preventDefault()}
                    onDrop={handleDrop}
                    onClick={() => document.getElementById('fileUpload').click()}
                >
                    <div className="absolute inset-0 bg-blue-500/5 opacity-0 group-hover:opacity-100 transition-opacity"></div>
                    <input
                        type="file"
                        id="fileUpload"
                        className="hidden"
                        multiple
                        accept="application/pdf"
                        onChange={handleFileChange}
                    />

                    <div className="w-20 h-20 rounded-full bg-blue-500/10 flex items-center justify-center mb-6 text-blue-400 group-hover:scale-110 group-hover:bg-blue-500/20 transition-all duration-300 shadow-[0_0_30px_rgba(59,130,246,0.2)]">
                        <UploadCloud size={40} />
                    </div>
                    <h3 className="text-2xl font-bold text-slate-200 mb-2">Drag & Drop PDFs here</h3>
                    <p className="text-slate-400 text-center max-w-md">
                        Support for scanned images, multiline tables, and unstructured layouts. PDF format only.
                    </p>
                    <div className="mt-8 px-6 py-2 rounded-full border border-slate-600 bg-slate-800/50 text-sm font-medium hover:bg-slate-700 transition">
                        Browse Files
                    </div>
                </div>
            )}

            {files.length > 0 && (
                <div className="glass-panel p-6 animate-in slide-in-from-bottom flex flex-col gap-6">
                    <div className="flex justify-between items-center">
                        <h3 className="text-xl font-bold text-slate-200 flex items-center gap-2">
                            <FileType className="text-emerald-400" />
                            Selected Documents ({files.length})
                        </h3>

                        {progressStep === 0 ? (
                            <button onClick={handleUpload} className="btn-primary flex items-center gap-2">
                                Run Smart Pipeline <ArrowRight size={20} />
                            </button>
                        ) : progressStep < 5 ? (
                            <div className="flex items-center gap-3 bg-blue-500/10 px-4 py-2 rounded-xl text-blue-300 font-medium">
                                <Loader2 className="animate-spin" size={20} />
                                {progressStep === 1 && "1/4 Extracting OCR Text..."}
                                {progressStep === 2 && "2/4 Type Detection..."}
                                {progressStep === 3 && "3/4 Field Extraction..."}
                                {progressStep === 4 && "4/4 Cross Verification..."}
                            </div>
                        ) : (
                            <button onClick={handleContinueToScore} className="btn-primary bg-emerald-500 hover:bg-emerald-400 border-none shadow-[0_0_20px_rgba(16,185,129,0.3)] flex items-center gap-2">
                                Check Eligibility Score <ArrowRight size={20} />
                            </button>
                        )}
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        {files.map((file, idx) => {
                            const parsed = parsedResults[idx];
                            return (
                                <div key={idx} className="flex flex-col bg-slate-800/60 rounded-xl p-5 border border-slate-700/50 relative">
                                    <div className="flex items-start gap-3 relative z-10 mb-2">
                                        <div className="p-2 bg-emerald-500/20 text-emerald-400 rounded-md">
                                            <CheckCircle size={20} />
                                        </div>
                                        <div className="overflow-hidden">
                                            <p className="text-sm font-semibold truncate text-slate-200 w-[150px]" title={file.name}>{file.name}</p>
                                            <p className="text-xs text-slate-500 mt-1">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
                                        </div>
                                    </div>

                                    {parsed && (
                                        <div className="mt-2 pt-4 border-t border-slate-700/50 flex flex-col gap-3">
                                            <div className="flex items-center justify-between">
                                                <span className={`text-xs font-bold px-2 py-1 flex items-center gap-1 rounded uppercase tracking-wider ${parsed.type !== "UNKNOWN" ? "bg-blue-500/20 text-blue-300" : "bg-slate-700 text-slate-300"}`}>
                                                    {parsed.type.replace('_', ' ')}
                                                </span>
                                                {parsed.type !== "UNKNOWN" && (
                                                    <span className="text-xs font-bold text-emerald-400 truncate ml-2">{Math.round(parsed.conf * 100)}% Match</span>
                                                )}
                                            </div>
                                            <div className="flex flex-wrap gap-2 mt-1">
                                                {parsed.fields.map((field, fidx) => (
                                                    <span key={fidx} className="bg-slate-900 border border-slate-700 px-2 py-1 rounded text-xs text-slate-300 shadow-inner">
                                                        {field}
                                                    </span>
                                                ))}
                                            </div>
                                        </div>
                                    )}

                                    {progressStep === 0 && (
                                        <button onClick={(e) => { e.stopPropagation(); removeFile(idx); }} className="absolute top-2 right-2 text-slate-500 hover:text-red-400 transition">✕</button>
                                    )}
                                </div>
                            );
                        })}
                    </div>
                </div>
            )}
        </div>
    );
}
