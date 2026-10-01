import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { History, Search, X } from "lucide-react";
import type { Tabela } from "../api";
import { Cabecalho } from "../components/Layout";
import { Cartao, Carregando, Erro, Selo, Vazio } from "../components/ui";
import { brl, data, FAIXAS, haQuantoTempo, num, pct } from "../formato";
import { useApi } from "../usarApi";

export function Tabelas() {
  const [busca, setBusca] = useState("");
  const [consulta, setConsulta] = useState("");
  const { dados, erro } = useApi<Tabela[]>(`tabelas${consulta ? `?q=${encodeURIComponent(consulta)}` : ""}`);
  const [historico, setHistorico] = useState<string | null>(null);

  return (
    <>
      <Cabecalho
        titulo="Tabelas publicadas"
        descricao="O que o corretor vê. Cada linha é a versão vigente do preço de um produto numa condição, ligada ao documento de origem. Versões antigas ficam no histórico."
      />
      <form className="mb-4 flex max-w-xl gap-2" onSubmit={(e) => { e.preventDefault(); setConsulta(busca.trim()); }}>
        <label className="relative flex-1">
          <span className="sr-only">Buscar por plano, operadora ou registro ANS</span>
          <Search size={16} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-400" aria-hidden />
          <input value={busca} onChange={(e) => setBusca(e.target.value)} placeholder="Plano, operadora ou registro ANS"
            className="min-h-10 w-full rounded-md border border-borda bg-white pl-8 pr-3 text-sm" />
        </label>
        <button type="submit" className="min-h-10 cursor-pointer rounded-md bg-marinho px-4 text-sm font-medium text-white hover:bg-marinho-2">Buscar</button>
      </form>
      <Cartao>
        {erro && <Erro mensagem={erro} />}
        {!dados ? <Carregando /> : dados.length === 0 ? <Vazio>Nenhuma tabela publicada encontrada.</Vazio> : (
          <div className="relative overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="border-b border-borda bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
                <tr>
                  <th className="px-4 py-2.5 font-medium">Registro ANS</th>
                  <th className="px-3 py-2.5 font-medium">Plano</th>
                  <th className="px-3 py-2.5 font-medium">Fonte</th>
                  <th className="px-3 py-2.5 text-right font-medium">0–18</th>
                  <th className="px-3 py-2.5 text-right font-medium">59+</th>
                  <th className="px-3 py-2.5 font-medium">Versão</th>
                  <th className="px-3 py-2.5 font-medium">Última confirmação</th>
                  <th className="px-4 py-2.5"><span className="sr-only">Ações</span></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-borda">
                {dados.map((t) => (
                  <tr key={t.id} className="hover:bg-slate-50">
                    <td className="px-4 py-2 font-mono text-xs">{t.registro_ans}</td>
                    <td className="max-w-72 px-3 py-2">
                      <p className="truncate text-slate-900">{t.plano}</p>
                      <p className="truncate text-xs text-slate-500">{t.operadora} · {t.tipo_contratacao}</p>
                    </td>
                    <td className="px-3 py-2 text-slate-700">{t.fonte}</td>
                    <td className="num px-3 py-2 text-right">{brl(t.precos["00-18"])}</td>
                    <td className="num px-3 py-2 text-right">{brl(t.precos["59+"])}</td>
                    <td className="px-3 py-2"><Selo tom={t.versao > 1 ? "leitura" : "info"}>v{t.versao}</Selo></td>
                    <td className="px-3 py-2 text-xs text-slate-600">{haQuantoTempo(t.dias_desde_confirmacao)}</td>
                    <td className="px-4 py-2 text-right">
                      <button type="button" onClick={() => setHistorico(t.registro_ans)}
                        className="inline-flex min-h-8 cursor-pointer items-center gap-1 rounded-md px-2 text-xs font-medium text-acao hover:bg-sky-50">
                        <History size={14} aria-hidden /> Histórico
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Cartao>
      {historico && <PainelHistorico registro={historico} fechar={() => setHistorico(null)} />}
    </>
  );
}

function PainelHistorico({ registro, fechar }: { registro: string; fechar: () => void }) {
  const { dados } = useApi<Tabela[]>(`tabelas/historico/${registro.replace(/\D/g, "")}`);
  const grupos = useMemo(() => {
    const g = new Map<string, Tabela[]>();
    for (const t of dados ?? []) {
      const chave = `${t.fonte} · ${t.cadeia ?? t.id}`;
      g.set(chave, [...(g.get(chave) ?? []), t]);
    }
    return [...g.entries()].map(([chave, versoes]) => {
      const atual = versoes[versoes.length - 1];
      const condicao = atual.marcas_condicao.join(" · ") || atual.condicao || `condição ${atual.ocorrencia + 1}`;
      return { chave, titulo: `${atual.fonte} · ${condicao}`, versoes };
    });
  }, [dados]);

  return (
    <div className="fixed inset-0 z-40 flex justify-end bg-slate-900/50" onClick={fechar}>
      <aside role="dialog" aria-modal="true" aria-label={`Histórico do registro ${registro}`}
        className="h-full w-full max-w-2xl overflow-y-auto bg-fundo p-5 shadow-xl" onClick={(e) => e.stopPropagation()}>
        <div className="mb-4 flex items-start justify-between">
          <div>
            <h2 className="text-lg font-semibold">Histórico de preços</h2>
            <p className="font-mono text-sm text-slate-600">{registro}</p>
          </div>
          <button type="button" onClick={fechar} aria-label="Fechar" className="grid size-9 cursor-pointer place-items-center rounded-md hover:bg-slate-200">
            <X size={18} aria-hidden />
          </button>
        </div>
        {!dados ? <Carregando /> : grupos.map(({ chave, titulo, versoes }) => (
          <Cartao key={chave} titulo={titulo} className="mb-4">
            <ol className="divide-y divide-borda">
              {versoes.map((v, i) => {
                const anterior = versoes[i - 1];
                return (
                  <li key={v.id} className="px-4 py-3">
                    <div className="flex flex-wrap items-center gap-2 text-sm">
                      <Selo tom={v.ativa ? "ok" : "info"}>v{v.versao}{v.ativa ? " · vigente" : ""}</Selo>
                      <Link to={`/documentos/${v.documento_id}`} className="truncate text-acao hover:underline">{v.documento}</Link>
                      <span className="text-xs text-slate-500">
                        {v.data_material ? `material de ${data(v.data_material)} · ` : ""}publicada {data(v.publicada_em)}
                      </span>
                    </div>
                    <div className="mt-2 grid grid-cols-5 gap-1 sm:grid-cols-10">
                      {FAIXAS.map((f) => {
                        const antes = anterior?.precos[f];
                        const agora = v.precos[f];
                        const mudou = antes !== undefined && agora !== undefined && Math.abs(antes - agora) >= 0.005;
                        return (
                          <div key={f} className={`rounded border px-1 py-1 text-center ${mudou ? "border-sky-200 bg-sky-50" : "border-borda bg-white"}`}>
                            <p className="text-[11px] text-slate-500">{f}</p>
                            <p className="num text-xs font-medium">{agora !== undefined ? agora.toLocaleString("pt-BR", { minimumFractionDigits: 2 }) : "—"}</p>
                            {mudou && <p className="num text-[10px] text-acao">{pct(agora! / antes! - 1)}</p>}
                          </div>
                        );
                      })}
                    </div>
                  </li>
                );
              })}
            </ol>
          </Cartao>
        ))}
        {dados && dados.length > 0 && (
          <p className="text-xs text-slate-500">{num(dados.length)} versões em {grupos.length} combinações de fonte e condição.</p>
        )}
      </aside>
    </div>
  );
}
