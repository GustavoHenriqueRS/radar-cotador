import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter, HashRouter, Route, Routes } from "react-router-dom";
import "@fontsource/fira-sans/400.css";
import "@fontsource/fira-sans/500.css";
import "@fontsource/fira-sans/600.css";
import "@fontsource/fira-code/400.css";
import "@fontsource/fira-code/600.css";
import "./index.css";
import { Layout } from "./components/Layout";
import { Apresentacao } from "./pages/Apresentacao";
import { ESTATICO } from "./estatico";
import { Cotacao } from "./pages/Cotacao";
import { Documento } from "./pages/Documento";
import { Documentos } from "./pages/Documentos";
import { Fontes } from "./pages/Fontes";
import { Painel } from "./pages/Painel";
import { Radar } from "./pages/Radar";
import { Tabelas } from "./pages/Tabelas";

// O GitHub Pages só serve arquivos: na versão estática, a rota vai depois do # e o recarregamento não quebra.
const Roteador = ESTATICO ? HashRouter : BrowserRouter;
// Quem chega pelo link do GitHub Pages começa pela apresentação; daí o botão abre o protótipo.
if (ESTATICO && window.location.hash === "") window.location.replace("#/apresentacao");

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <Roteador>
      <Routes>
        <Route path="apresentacao" element={<Apresentacao />} />
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
    </Roteador>
  </StrictMode>,
);
