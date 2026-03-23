import { BrowserRouter, Routes, Route } from "react-router-dom";
import Layout from "./components/Layout";
import { ToastProvider } from "./components/Toast";
import ScenarioDashboardPage from "./pages/ScenarioDashboardPage";
import GraphPage from "./pages/GraphPage";
import ScenariosPage from "./pages/ScenariosPage";
import SensitivityPage from "./pages/SensitivityPage";
import DemoPage from "./pages/DemoPage";

export default function App() {
  return (
    <BrowserRouter>
      <ToastProvider>
        <Routes>
          <Route element={<Layout />}>
            <Route index element={<ScenarioDashboardPage />} />
            <Route path="graph" element={<GraphPage />} />
            <Route path="scenarios" element={<ScenariosPage />} />
            <Route path="compare" element={<ScenarioDashboardPage />} />
            <Route path="sensitivity" element={<SensitivityPage />} />
            <Route path="demo" element={<DemoPage />} />
          </Route>
        </Routes>
      </ToastProvider>
    </BrowserRouter>
  );
}
