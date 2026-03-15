import { BrowserRouter, Routes, Route } from "react-router-dom";
import Layout from "./components/Layout";
import DashboardPage from "./pages/DashboardPage";
import GraphPage from "./pages/GraphPage";
import ScenariosPage from "./pages/ScenariosPage";
import ComparePage from "./pages/ComparePage";
import SensitivityPage from "./pages/SensitivityPage";
import DemoPage from "./pages/DemoPage";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<DashboardPage />} />
          <Route path="graph" element={<GraphPage />} />
          <Route path="scenarios" element={<ScenariosPage />} />
          <Route path="compare" element={<ComparePage />} />
          <Route path="sensitivity" element={<SensitivityPage />} />
          <Route path="demo" element={<DemoPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
