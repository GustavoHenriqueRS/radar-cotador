import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { ArrowLeft, Check, CheckCircle2, Download, EyeOff, RefreshCw, Send } from "lucide-react";
import { post, type Coluna, type DocumentoDetalhe, type ResultadoPublicacao } from "../api";
import { Cabecalho } from "../components/Layout";
import { ItemEvento } from "../components/Eventos";
import { VisorPagina } from "../components/VisorPagina";
import { urlPdf } from "../estatico";
import { Botao, Cartao, Carregando, Erro, estadoCelula, IconeSeveridade, Selo, SeloLeitura, SeloStatusDocumento, Vazio, useDeslizante } from "../components/ui";
import { brl, data, FAIXAS, num } from "../formato";
import { useApi } from "../usarApi";

const CLASSE_CELULA: Record<string, string> = {
  ok: "border-green-200 bg-ok-fundo text-ok",
  revisar: "border-amber-300 bg-revisar-fundo text-revisar",
  erro: "border-red-300 bg-erro-fundo text-erro",
  leitura: "border-borda bg-white text-slate-800",
};

export function Documento() {
  const { id } = useParams();
  const { dados: doc, erro, recarregar } = useApi<DocumentoDetalhe>(`documentos/${id}`, 2500, (d) => d.status === "processando");
  const [pagina, setPagina] = useState(1);
  const [selecionada, setSelecionada] = useState<{ coluna: number; celula?: number } | null>(null);
  const [filtro, setFiltro] = useState<"revisar" | "todas">("revisar");
  const [ocupado, setOcupado] = useState<string | null>(null);
  const [aviso, setAviso] = useState<string | null>(null);

  const colunasRevisar = useMemo(() => doc?.colunas.filter((c) => c.celulas.some((x) => x.revisar) && c.status !== "ignorada") ?? [], [doc]);
  const abas = useDeslizante<HTMLDivElement>(filtro, doc?.id, doc?.status, colunasRevisar.length);
  const visiveis = filtro === "revisar" ? colunasRevisar : doc?.colunas ?? [];

  useEffect(() => {
    if (doc && colunasRevisar.length === 0) setFiltro("todas");
  }, [doc, colunasRevisar.length]);

  useEffect(() => {
    const primeira = (colunasRevisar[0] ?? doc?.colunas[0])?.pagina;
    if (primeira) setPagina(primeira);
    // só ao carregar o documento
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [doc?.id, doc?.status]);

  if (erro) return <Erro mensagem={erro} />;
  if (!doc) return <Carregando />;

  async function acao(nome: string, fn: () => Promise<unknown>, mensagem?: (r: unknown) => string) {
    setOcupado(nome);
    setAviso(null);
    try {
      const r = await fn();
      if (mensagem) setAviso(mensagem(r));
      await recarregar();
    } catch (e) {
      setAviso((e as Error).message);
    } finally {
      setOcupado(null);
    }
  }

  function selecionar(coluna: number, celula?: number) {
    setSelecionada({ coluna, celula });
    const c = doc!.colunas.find((x) => x.id === coluna);
    if (c) setPagina(c.pagina);
    document.getElementById(`coluna-${coluna}`)?.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }

  const pendentes = doc.colunas.filter((c) => c.status !== "ignorada" && c.registro_ans && !c.publicavel).length;
  const r = doc.resumo;
  const processando = doc.status === "processando";

  return (
    <>
      <Link to="/documentos" className="mb-3 inline-flex items-center gap-1 text-sm text-slate-600 hover:text-acao">
        <ArrowLeft size={15} aria-hidden /> Documentos
      </Link>
      <Cabecalho
        titulo={doc.nome}
        descricao={[doc.operadora, doc.administradora && `via ${doc.administradora}`, doc.tipo_contratacao, doc.vigencia_fim && `vigência até ${data(doc.vigencia_fim)}`].filter(Boolean).join(" · ")}
        acoes={
          <>
            <a href={urlPdf(doc.id)} download={doc.nome} title="Baixar o PDF original, como chegou"
              className="inline-flex min-h-9 items-center gap-1.5 rounded-md border border-borda bg-white px-3 py-1.5 text-sm font-medium text-slate-800 transition-colors duration-150 hover:bg-slate-50">
              <Download size={15} aria-hidden /> Baixar PDF
            </a>
            <Botao onClick={() => acao("reprocessar", () => post(`documentos/${doc.id}/reprocessar`))} carregando={ocupado === "reprocessar"} disabled={processando}>
              <RefreshCw size={15} aria-hidden /> Reprocessar
            </Botao>
            <Botao
              tipo="primario"
              disabled={processando || doc.status === "publicado" || (doc.status === "historico" && pendentes === 0)}
              carregando={ocupado === "publicar"}
              title={pendentes ? `${pendentes} coluna(s) ainda precisam de revisão e ficarão de fora` : "Publicar as colunas conferidas"}
              onClick={() =>
                acao("publicar", () => post<ResultadoPublicacao>(`documentos/${doc.id}/publicar`), (x) => {
                  const res = x as ResultadoPublicacao;
                  if (res.historico) {
                    return `Versão antiga (já existe a de ${data(res.versao_mais_nova ?? null)}): ${res.publicadas} tabela(s) entraram no histórico, ` +
                      `${res.sem_mudanca} com o mesmo preço da versão vizinha, ${res.bloqueadas} retidas para revisão. A cotação não muda.`;
                  }
                  return `Publicado: ${res.publicadas} versões novas, ${res.sem_mudanca} sem mudança, ${res.bloqueadas} colunas retidas para revisão.`;
                })
              }
            >
              <Send size={15} aria-hidden /> {doc.status === "publicado" ? "Publicado" : doc.status === "historico" ? (pendentes ? "Publicar o que falta no histórico" : "No histórico") : "Publicar"}
            </Botao>
          </>
        }
      />

      <div className="mb-4 flex flex-wrap items-center gap-2">
        <SeloStatusDocumento status={doc.status} />
        <SeloLeitura leitura={doc.leitura_llm} ocr={doc.ocr} />
        {doc.fonte && <Selo tom="info">Fonte: {doc.fonte}</Selo>}
        <span className="num text-sm text-slate-600">
          {num(r.celulas ?? 0)} preços em {num(r.colunas ?? 0)} colunas
          {(doc.leitura_llm === "ao_vivo" || doc.leitura_llm === "gravada") && <> · <span className="text-ok">{num(r.confirmado ?? 0)} confirmados pelas duas leituras</span></>}
          {(r.confirmado_calculo ?? 0) > 0 && <> · <span className="text-ok">{num(r.confirmado_calculo ?? 0)} pelo cálculo do padrão de faixas</span></>}
          {" · "}<span className={r.revisar ? "font-medium text-revisar" : "text-ok"}>{num(r.revisar ?? 0)} para revisar</span>
          {doc.custo_llm_usd && <> · LLM US$ {Number(doc.custo_llm_usd).toFixed(3)}</>}
        </span>
      </div>
      {aviso && <p role="status" className="mb-4 rounded-md border border-borda bg-white px-3 py-2 text-sm text-slate-700">{aviso}</p>}
      {doc.erro && <Erro mensagem={doc.erro} />}
      {doc.extra_llm.falha && (
        <p role="status" className="mb-4 rounded-md border border-revisar/40 bg-revisar-fundo px-3 py-2 text-sm text-slate-700">
          A segunda leitura (LLM) não rodou: <span className="font-mono text-xs">{doc.extra_llm.falha}</span>. O documento seguiu com a
          leitura {doc.ocr ? "por OCR" : "geométrica"}; Reprocessar tenta de novo.
        </p>
      )}

      {processando ? (
        <Carregando texto="Lendo o PDF: leitura geométrica, OCR se não houver texto e, com chave configurada, a segunda leitura por LLM…" />
      ) : (
        <div className="grid gap-5 xl:grid-cols-[minmax(0,1.15fr)_minmax(0,1fr)]">
          <div className="xl:sticky xl:top-5 xl:self-start">
            <VisorPagina
              documentoId={doc.id}
              pagina={pagina}
              totalPaginas={doc.paginas || 1}
              tamanho={doc.tamanhos_paginas[pagina - 1]}
              colunas={doc.colunas}
              selecionada={selecionada}
              aoSelecionar={selecionar}
              aoMudarPagina={setPagina}
            />
            <Legenda />
          </div>

          <div className="min-w-0 space-y-4">
            <div ref={abas.grupo} role="tablist" className="relative inline-flex rounded-md border border-borda bg-white p-0.5 text-sm">
              <span aria-hidden className={`${abas.classe} rounded bg-marinho`} style={abas.estilo} />
              {(["revisar", "todas"] as const).map((f) => (
                <button key={f} role="tab" aria-selected={filtro === f} data-ativo={filtro === f} type="button" onClick={() => setFiltro(f)}
                  className={`relative min-h-8 cursor-pointer rounded px-3 transition-colors duration-200 ${filtro === f ? "text-white" : "text-slate-700 hover:bg-slate-100"}`}>
                  {f === "revisar" ? `Precisam de revisão (${colunasRevisar.length})` : `Todas as colunas (${doc.colunas.length})`}
                </button>
              ))}
            </div>
            {visiveis.length === 0 && (
              <Cartao><Vazio>Nenhuma coluna precisa de revisão: as leituras e as regras da ANS fecharam. Pode publicar.</Vazio></Cartao>
            )}
            {visiveis.slice(0, 120).map((c) => (
              <CartaoColuna key={c.id} coluna={c} selecionada={selecionada} aoSelecionar={selecionar}
                ocupado={ocupado} acao={acao} />
            ))}
            {visiveis.length > 120 && <p className="text-sm text-slate-500">Mostrando 120 de {visiveis.length} colunas.</p>}
            <InformacoesLLM doc={doc} />
            {doc.eventos.length > 0 && (
              <Cartao titulo="Eventos gerados por este documento">
                <ul className="divide-y divide-borda">{doc.eventos.map((e) => <ItemEvento key={e.id} e={e} />)}</ul>
              </Cartao>
            )}
          </div>
        </div>
      )}
    </>
  );
}

function CartaoColuna({ coluna: c, selecionada, aoSelecionar, ocupado, acao }: {
  coluna: Coluna;
  selecionada: { coluna: number; celula?: number } | null;
  aoSelecionar: (coluna: number, celula?: number) => void;
  ocupado: string | null;
  acao: (nome: string, fn: () => Promise<unknown>) => void;
}) {
  const [valor, setValor] = useState("");
  const ativa = selecionada?.coluna === c.id;
  const celulaEscolhida = ativa ? c.celulas.find((x) => x.id === selecionada?.celula) : undefined;
  const porFaixa = Object.fromEntries(c.celulas.map((x) => [x.faixa, x]));
  const revisar = c.celulas.some((x) => x.revisar);
  const graves = c.achados.filter((a) => a.severidade !== "info");
  const infos = c.achados.filter((a) => a.severidade === "info");

  useEffect(() => {
    setValor(celulaEscolhida?.valor ? Number(celulaEscolhida.valor).toFixed(2).replace(".", ",") : "");
  }, [celulaEscolhida?.id, celulaEscolhida?.valor]);

  return (
    <article id={`coluna-${c.id}`} className={`rounded-lg border bg-white transition-shadow duration-150 ${ativa ? "border-acao shadow-[0_0_0_1px_var(--color-acao)]" : "border-borda"} ${c.status === "ignorada" ? "opacity-60" : ""}`}>
      <header className="flex flex-wrap items-start justify-between gap-2 px-4 pt-3">
        <div className="min-w-0">
          <p className="flex flex-wrap items-center gap-2">
            <span className="font-mono text-sm font-semibold text-slate-900">{c.registro_ans || "sem registro ANS"}</span>
            {c.plano_ans && (
              <Selo tom={c.plano_ans.situacao === "Ativo" ? "ok" : "revisar"}>ANS: {c.plano_ans.situacao}</Selo>
            )}
            {c.status === "aprovada" && <Selo tom="ok" icone={<CheckCircle2 size={12} aria-hidden />}>Aprovada</Selo>}
            {c.status === "ignorada" && <Selo tom="info">Ignorada</Selo>}
          </p>
          <p className="mt-0.5 truncate text-sm text-slate-700">{c.plano_ans?.nome ?? c.coluna}</p>
          <p className="truncate text-xs text-slate-500" title={c.tabela}>
            p. {c.pagina} · {c.tabela || c.coluna}
            {c.plano_ans && ` · ${c.plano_ans.contratacao} · ${c.plano_ans.acomodacao === "Coletiva" ? "enfermaria" : c.plano_ans.acomodacao === "Individual" ? "apartamento" : c.plano_ans.acomodacao}`}
          </p>
        </div>
        <div className="flex gap-1.5">
          {revisar && c.status !== "ignorada" && (
            <Botao onClick={() => acao(`aprovar-${c.id}`, () => post(`colunas/${c.id}/aprovar`))} carregando={ocupado === `aprovar-${c.id}`}
              title="Conferi no PDF: os valores estão certos">
              <Check size={15} aria-hidden /> Aprovar
            </Botao>
          )}
          {c.status !== "ignorada" && (
            <Botao tipo="fantasma" onClick={() => acao(`ignorar-${c.id}`, () => post(`colunas/${c.id}/ignorar`))} title="Não publicar esta coluna">
              <EyeOff size={15} aria-hidden /> Ignorar
            </Botao>
          )}
        </div>
      </header>

      <div className="grid grid-cols-5 gap-1.5 px-4 py-3 sm:grid-cols-10">
        {FAIXAS.map((f) => {
          const cel = porFaixa[f];
          if (!cel) {
            return (
              <div key={f} className="rounded border border-dashed border-slate-200 px-1 py-1.5 text-center">
                <p className="text-[11px] text-slate-400">{f}</p>
                <p className="text-xs text-slate-300">—</p>
              </div>
            );
          }
          const estado = estadoCelula(cel);
          const escolhida = celulaEscolhida?.id === cel.id;
          return (
            <button key={f} type="button" onClick={() => aoSelecionar(c.id, cel.id)}
              title={`${estado.rotulo}${cel.llm && cel.geometrico && cel.llm !== cel.geometrico ? ` · geométrica ${brl(cel.geometrico)} × LLM ${brl(cel.llm)}` : ""}`}
              className={`cursor-pointer rounded border px-1 py-1.5 text-center transition-colors duration-150 ${CLASSE_CELULA[estado.tom]} ${escolhida ? "ring-2 ring-acao" : ""}`}>
              <p className="flex items-center justify-center gap-0.5 text-[11px] opacity-80">
                <estado.Icone size={10} aria-hidden /> {f}
              </p>
              <p className="num text-xs font-semibold">{cel.valor ? Number(cel.valor).toLocaleString("pt-BR", { minimumFractionDigits: 2 }) : "—"}</p>
            </button>
          );
        })}
      </div>

      {celulaEscolhida && (
        <form
          className="mx-4 mb-3 flex flex-wrap items-end gap-2 rounded-md bg-slate-50 p-3"
          onSubmit={(e) => { e.preventDefault(); acao(`corrigir-${celulaEscolhida.id}`, () => post(`celulas/${celulaEscolhida.id}`, { valor })); }}
        >
          <div className="text-xs text-slate-600">
            <p className="font-medium text-slate-800">Faixa {celulaEscolhida.faixa}</p>
            <p>geométrica/OCR: <span className="num">{brl(celulaEscolhida.geometrico)}</span></p>
            <p>LLM: <span className="num">{brl(celulaEscolhida.llm)}</span></p>
            {celulaEscolhida.calculado && (
              <p>calculado pelo padrão de faixas: <span className="num">{brl(celulaEscolhida.calculado)}</span></p>
            )}
          </div>
          <label className="ml-auto text-xs text-slate-600">
            Valor correto (R$)
            <input value={valor} onChange={(e) => setValor(e.target.value)} inputMode="decimal"
              className="num mt-1 block w-32 rounded-md border border-borda bg-white px-2 py-1.5 text-sm text-slate-900" />
          </label>
          <Botao tipo="primario" carregando={ocupado === `corrigir-${celulaEscolhida.id}`} onClick={() => acao(`corrigir-${celulaEscolhida.id}`, () => post(`celulas/${celulaEscolhida.id}`, { valor }))}>
            Corrigir
          </Botao>
        </form>
      )}

      {(graves.length > 0 || infos.length > 0) && (
        <ul className="space-y-1.5 border-t border-borda px-4 py-3">
          {[...graves, ...infos].map((a, i) => (
            <li key={i} className="flex items-start gap-2 text-xs">
              <IconeSeveridade severidade={a.severidade} tamanho={14} />
              <span className={a.severidade === "info" ? "text-slate-500" : "text-slate-800"}>
                <span className="font-medium">{a.regra}:</span> {a.mensagem}
              </span>
            </li>
          ))}
        </ul>
      )}
    </article>
  );
}

function Legenda() {
  const itens = [
    ["ok", "Confirmado (duas leituras, ou uma leitura e o cálculo) ou corrigido"],
    ["leitura", "Leitura única, sem alerta"],
    ["revisar", "Revisar: regra da ANS ou leitura apontou"],
    ["erro", "Leituras divergem"],
  ] as const;
  const cor: Record<string, string> = { ok: "bg-green-500/40", leitura: "bg-blue-400/30", revisar: "bg-amber-400/60", erro: "bg-red-500/50" };
  return (
    <ul className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-xs text-slate-600">
      {itens.map(([k, t]) => (
        <li key={k} className="flex items-center gap-1.5"><span className={`size-3 rounded-sm ${cor[k]}`} aria-hidden /> {t}</li>
      ))}
    </ul>
  );
}

function InformacoesLLM({ doc }: { doc: DocumentoDetalhe }) {
  const extra = doc.extra_llm;
  if (!extra || (!extra.carencias?.length && !extra.coparticipacao?.length && !extra.avisos?.length)) return null;
  return (
    <Cartao titulo="Lido pelo LLM além dos preços">
      <div className="grid gap-4 p-4 text-sm md:grid-cols-2">
        {extra.carencias?.length ? (
          <div>
            <h3 className="mb-1 text-xs font-semibold uppercase tracking-wide text-slate-500">Carências</h3>
            <ul className="space-y-0.5">{extra.carencias.map((c, i) => <li key={i}>{c.cobertura}: <span className="num">{c.prazo_dias ?? "—"}</span> dias</li>)}</ul>
          </div>
        ) : null}
        {extra.coparticipacao?.length ? (
          <div>
            <h3 className="mb-1 text-xs font-semibold uppercase tracking-wide text-slate-500">Coparticipação</h3>
            <ul className="space-y-0.5">{extra.coparticipacao.slice(0, 10).map((c, i) => <li key={i}>{c.procedimento}: {c.regra}</li>)}</ul>
          </div>
        ) : null}
        {extra.avisos?.length ? (
          <div className="md:col-span-2">
            <h3 className="mb-1 text-xs font-semibold uppercase tracking-wide text-slate-500">Dúvidas de leitura registradas pelo modelo</h3>
            <ul className="list-disc space-y-0.5 pl-5 text-slate-700">{extra.avisos.map((a, i) => <li key={i}>{a}</li>)}</ul>
          </div>
        ) : null}
      </div>
    </Cartao>
  );
}
