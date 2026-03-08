import { Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import UploadPage from './pages/UploadPage';
import ScoreView from './pages/ScoreView';
import QualitativeInputPage from './pages/QualitativeInputPage';
import EvidenceTimeline from './pages/EvidenceTimeline';
import CAMGenerator from './pages/CAMGenerator';
import FeatureIntelligenceReport from './pages/FeatureIntelligenceReport';

import HistoryView from './pages/HistoryView';
import LoginPage from './pages/LoginPage';
import { useAppContext } from './context/AppContext';

function App() {
  const { sessionData } = useAppContext();

  if (!sessionData?.user) {
    return <LoginPage />;
  }

  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<UploadPage />} />
        <Route path="/feature-intelligence" element={<FeatureIntelligenceReport />} />
        <Route path="/score" element={<ScoreView />} />
        <Route path="/qualitative-input" element={<QualitativeInputPage />} />
        <Route path="/evidence" element={<EvidenceTimeline />} />
        <Route path="/cam" element={<CAMGenerator />} />
        <Route path="/history" element={<HistoryView />} />
      </Route>
    </Routes>
  );
}

export default App;
