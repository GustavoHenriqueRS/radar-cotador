import { NavLink, Outlet } from "react-router-dom";
import { Activity, Calculator, FileStack, Gauge, Library, Presentation, TableProperties } from "lucide-react";
import { ESTATICO } from "../estatico";

const ITENS = [
  { para: "/", rotulo: "Painel", Icone: Gauge, fim: true },
  { para: "/documentos", rotulo: "Documentos", Icone: FileStack },
  { para: "/tabelas", rotulo: "Tabelas publicadas", Icone: TableProperties },
  { para: "/radar", rotulo: "Radar", Icone: Activity },
  { para: "/cotacao", rotulo: "Cotação", Icone: Calculator },
  { para: "/fontes", rotulo: "Fontes", Icone: Library },
  { para: "/apresentacao", rotulo: "Apresentação", Icone: Presentation },
];

export function Layout() {
  return (
    <div className="min-h-dvh lg:flex">
      {/* Com o roteador por #, um link para #conteudo trocaria de rota: o foco vai direto para o conteúdo. */}
      <a href="#conteudo" onClick={(e) => { e.preventDefault(); document.getElementById("conteudo")?.focus(); }} className="sr-only focus:not-sr-only focus:absolute focus:left-2 focus:top-2 focus:z-50 focus:rounded focus:bg-white focus:p-2">
        Pular para o conteúdo
      </a>
      <aside className="bg-marinho text-slate-300 lg:sticky lg:top-0 lg:h-dvh lg:w-60 lg:shrink-0">
        <div className="flex items-center gap-2 px-5 py-4">
          <div className="grid size-8 place-items-center rounded-md bg-acao text-white">
            <Activity size={18} aria-hidden />
          </div>
          <div>
            <p className="text-sm font-semibold text-white">Radar do Cotador</p>
            <p className="text-xs text-slate-400">dados de operadoras</p>
          </div>
        </div>
        <nav aria-label="Principal" className="flex gap-1 overflow-x-auto px-3 pb-3 lg:flex-col lg:overflow-visible">
          {ITENS.map(({ para, rotulo, Icone, fim }) => (
            <NavLink
              key={para}
              to={para}
              end={fim}
              className={({ isActive }) =>
                `flex min-h-10 shrink-0 items-center gap-2.5 rounded-md px-3 text-sm transition-colors duration-150 ${
                  isActive ? "bg-marinho-2 font-medium text-white" : "hover:bg-marinho-2/60 hover:text-white"
                }`
              }
            >
              <Icone size={17} aria-hidden />
              {rotulo}
            </NavLink>
          ))}
        </nav>
        <p className="hidden px-5 pt-6 text-xs leading-relaxed text-slate-500 lg:block">
          Protótipo com dados públicos reais (ANS, operadoras e administradoras) e um PDF escaneado simulado.
        </p>
      </aside>
      <main id="conteudo" tabIndex={-1} className="min-w-0 flex-1 px-4 py-5 outline-none sm:px-6 lg:px-8">
        {ESTATICO && (
          <p role="note" className="mb-5 rounded-md border border-amber-200 bg-amber-50 px-4 py-3 text-sm leading-relaxed text-amber-900">
            Versão estática do protótipo: o acervo de demonstração como estava em {import.meta.env.VITE_DEMO_DATA ?? "sua exportação"}, com a
            cotação calculada no próprio navegador. Revisar, publicar e coletar ficam desligados aqui; o protótipo completo sobe com{" "}
            <code className="rounded bg-amber-100 px-1 font-mono text-xs">docker compose up</code>.{" "}
            <a href="https://github.com/GustavoHenriqueRS/radar-cotador" className="font-medium underline underline-offset-2">Código e documentação no GitHub</a>.
          </p>
        )}
        <Outlet />
      </main>
    </div>
  );
}

export function Cabecalho({ titulo, descricao, acoes }: { titulo: string; descricao?: string; acoes?: React.ReactNode }) {
  return (
    <div className="mb-5 flex flex-wrap items-end justify-between gap-3">
      <div className="min-w-0">
        <h1 className="break-words text-xl font-semibold text-slate-900">{titulo}</h1>
        {descricao && <p className="mt-1 max-w-3xl text-sm text-slate-600">{descricao}</p>}
      </div>
      {acoes && <div className="flex flex-wrap gap-2">{acoes}</div>}
    </div>
  );
}
