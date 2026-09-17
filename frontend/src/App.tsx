import { useEffect } from "react";
import { Navigate, Route, Routes, useLocation, useNavigate } from "react-router-dom";
import { AUTH_REQUIRED_EVENT } from "./api";
import WorkspaceLayout from "./components/WorkspaceLayout";
import Receipts from "./pages/Receipts";
import Documents from "./pages/Documents";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import AssertionsList from "./pages/AssertionsList";
import AssertionDetail from "./pages/AssertionDetail";
import ReviewQueue from "./pages/ReviewQueue";
import DocumentViewer from "./pages/DocumentViewer";
import AuditTimeline from "./pages/AuditTimeline";
import Export from "./pages/Export";
import RiskRadar from "./pages/RiskRadar";
import Landing from "./pages/Landing";
import ChangeImpact from "./pages/ChangeImpact";
import AppGuide from "./pages/AppGuide";

function isAuthenticated() {
  return !!localStorage.getItem("token");
}

function RequireAuth({ children }: { children: JSX.Element }) {
  const location = useLocation();
  if (!isAuthenticated()) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }
  return children;
}

export default function App() {
  const location = useLocation();
  const navigate = useNavigate();
  useEffect(() => {
    const signInAgain = () => {
      if (location.pathname !== "/login") {
        navigate("/login", { replace: true, state: { from: location, sessionExpired: true } });
      }
    };
    window.addEventListener(AUTH_REQUIRED_EVENT, signInAgain);
    return () => window.removeEventListener(AUTH_REQUIRED_EVENT, signInAgain);
  }, [location, navigate]);
  return (
    <Routes>
      <Route path="/" element={isAuthenticated() ? <Navigate to="/dashboard" replace /> : <Landing />} />
      <Route path="/about-demo" element={isAuthenticated() ? <Navigate to="/guide" replace /> : <AppGuide publicView />} />
      <Route path="/login" element={isAuthenticated() ? <Navigate to="/dashboard" replace /> : <Login />} />
      <Route element={<RequireAuth><WorkspaceLayout /></RequireAuth>}>
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/receipts" element={<Receipts />} />
        <Route path="/documents" element={<Documents />} />
        <Route path="/documents/:id" element={<DocumentViewer />} />
        <Route path="/change-impact" element={<ChangeImpact />} />
        <Route path="/guide" element={<AppGuide />} />
        <Route path="/risk-radar" element={<RiskRadar />} />
        <Route path="/assertions" element={<AssertionsList />} />
        <Route path="/assertions/:id" element={<AssertionDetail />} />
        <Route path="/review" element={<ReviewQueue />} />
        <Route path="/audit-trail" element={<AuditTimeline />} />
        <Route path="/export" element={<Export />} />
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Route>
    </Routes>
  );
}
