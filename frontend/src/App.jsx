import { Route, Routes } from "react-router-dom";
import Layout from "./components/Layout";
import { ChatProvider } from "./context/ChatContext";
import HomePage from "./pages/HomePage";
import ImovelDetalhePage from "./pages/ImovelDetalhePage";
import ImoveisPage from "./pages/ImoveisPage";
import NotFoundPage from "./pages/NotFoundPage";

export default function App() {
  return (
    <ChatProvider>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<HomePage />} />
          <Route path="imoveis" element={<ImoveisPage />} />
          <Route path="imoveis/:id" element={<ImovelDetalhePage />} />
          <Route path="*" element={<NotFoundPage />} />
        </Route>
      </Routes>
    </ChatProvider>
  );
}
