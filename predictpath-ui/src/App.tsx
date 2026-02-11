import { Routes, Route, Navigate } from "react-router-dom";
import Index from "./pages/Index";
import NonTechnicalMode from "./pages/NonTechnicalMode";
import Login from "./pages/Login";
import { AuthProvider } from "./contexts/AuthContext";
import { ProtectedRoute } from "./components/auth/ProtectedRoute";
import "./App.css";

function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/login" element={<Login />} />

        <Route element={<ProtectedRoute />}>
          <Route path="/" element={<Index />} />
          <Route path="/non-technical" element={<NonTechnicalMode />} />
        </Route>

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AuthProvider>
  );
}

export default App;
