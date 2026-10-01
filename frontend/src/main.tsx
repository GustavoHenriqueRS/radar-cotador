import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import "@fontsource/fira-sans/400.css";
import "@fontsource/fira-sans/500.css";
import "@fontsource/fira-sans/600.css";
import "@fontsource/fira-code/400.css";
import "@fontsource/fira-code/600.css";
import "./index.css";
import { Layout } from "./components/Layout";
import { Cotacao } from "./pages/Cotacao";
import { Documento } from "./pages/Documento";
import { Documentos } from "./pages/Documentos";
import { Fontes } from "./pages/Fontes";
import { Painel } from "./pages/Painel";
import { Radar } from "./pages/Radar";
import { Tabelas } from "./pages/Tabelas";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<Painel />} />
          <Route path="documentos" element={<Documentos />} />
          <Route path="documentos/:id" element={<Documento />} />
          <Route path="tabelas" element={<Tabelas />} />
          <Route path="radar" element={<Radar />} />
          <Route path="cotacao" element={<Cotacao />} />
          <Route path="fontes" element={<Fontes />} />
        </Route>
      </Routes>
    </BrowserRouter>
  </StrictMode>,
);
