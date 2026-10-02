import { useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { FileUp } from "lucide-react";
import { enviarArquivo, type DocumentoResumo } from "../api";
import { Cabecalho } from "../components/Layout";
import { Cartao, Carregando, Erro, SeloLeitura, SeloStatusDocumento, Vazio } from "../components/ui";
import { data, dataHora, num } from "../formato";
import { useApi } from "../usarApi";

export function Documentos() {
  const { dados, erro, recarregar } = useApi<DocumentoResumo[]>("documentos", 3000, (d) => d.some((x) => x.status === "processando"));
  const [enviando, setEnviando] = useState(false);
  const [erroEnvio, setErroEnvio] = useState<string | null>(null);
  const [arrastando, setArrastando] = useState(false);
  const input = useRef<HTMLInputElement>(null);
  const navegar = useNavigate();

  async function enviar(arquivos: FileList | null) {
    if (!arquivos?.length) return;
    setEnviando(true);
    setErroEnvio(null);
    try {
      let ultimo = 0;
      for (const arquivo of Array.from(arquivos)) ultimo = (await enviarArquivo(arquivo)).id;
      await recarregar();
      if (arquivos.length === 1) navegar(`/documentos/${ultimo}`);
    } catch (e) {
      setErroEnvio((e as Error).message);
    } finally {
      setEnviando(false);
    }
  }

  return (
    <>
      <Cabecalho titulo="Documentos recebidos" descricao="Tabelas de venda de operadoras e administradoras. Cada arquivo é lido duas vezes, conferido contra a ANS e fica guardado com o hash, para rastrear a origem de cada número." />
      <label
        data-ativo={arrastando || enviando}
        onDragOver={(e) => { e.preventDefault(); setArrastando(true); }}
        onDragLeave={(e) => { if (!e.currentTarget.contains(e.relatedTarget as Node)) setArrastando(false); }}
        onDrop={(e) => { e.preventDefault(); setArrastando(false); enviar(e.dataTransfer.files); }}
        className={`halo group mb-5 flex cursor-pointer flex-col items-center justify-center gap-2 rounded-xl border px-4 py-8 text-center transition-[background-color,box-shadow,border-color] duration-200 ${
          arrastando || enviando
            ? "border-transparent bg-sky-50/70 shadow-[0_0_0_4px_rgba(3,105,161,0.08),0_14px_40px_rgba(3,105,161,0.14)]"
            : "border-dashed border-slate-300 bg-white hover:border-acao/60"
        }`}
      >
        <span className={`grid size-12 place-items-center rounded-xl bg-sky-50 text-acao ring-1 ring-sky-100 transition-transform duration-200 motion-reduce:transition-none ${
          arrastando ? "-translate-y-1 scale-110" : "group-hover:-translate-y-0.5"}`}>
          <FileUp size={24} aria-hidden />
        </span>
        <span className="mt-1 text-sm font-medium text-slate-800">
          {enviando ? "Enviando e lendo o PDF…" : arrastando ? "Solte para enviar" : "Arraste PDFs de tabela aqui ou clique para escolher"}
        </span>
        <span className="text-xs text-slate-500">PDF com texto ou escaneado (vai para OCR). O mesmo arquivo não é processado duas vezes.</span>
        <input ref={input} type="file" accept="application/pdf" multiple className="sr-only" onChange={(e) => enviar(e.target.files)} />
      </label>
      {erroEnvio && <Erro mensagem={erroEnvio} />}

      <Cartao>
        {erro && <Erro mensagem={erro} />}
        {!dados ? (
          <Carregando />
        ) : dados.length === 0 ? (
          <Vazio>Nenhum documento ainda. Envie um PDF ou rode <code>manage.py carregar_demo</code>.</Vazio>
        ) : (
          <div className="relative overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="border-b border-borda bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
                <tr>
                  <th className="px-4 py-2.5 font-medium">Documento</th>
                  <th className="px-3 py-2.5 font-medium">Fonte</th>
                  <th className="px-3 py-2.5 font-medium">Situação</th>
                  <th className="px-3 py-2.5 font-medium">Leitura</th>
                  <th className="px-3 py-2.5 text-right font-medium">Preços</th>
                  <th className="px-3 py-2.5 text-right font-medium">Revisar</th>
                  <th className="px-3 py-2.5 font-medium">Vigência</th>
                  <th className="px-4 py-2.5 font-medium">Recebido</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-borda">
                {dados.map((d) => (
                  <tr key={d.id} className="hover:bg-slate-50">
                    <td className="max-w-80 px-4 py-2.5">
                      <Link to={`/documentos/${d.id}`} className="block truncate font-medium text-acao hover:underline">{d.nome}</Link>
                      <span className="block truncate text-xs text-slate-500">{[d.operadora, d.administradora].filter(Boolean).join(" · ")}</span>
                    </td>
                    <td className="px-3 py-2.5 text-slate-700">{d.fonte ?? "—"}</td>
                    <td className="px-3 py-2.5"><SeloStatusDocumento status={d.status} /></td>
                    <td className="px-3 py-2.5"><SeloLeitura leitura={d.leitura_llm} ocr={d.ocr} /></td>
                    <td className="num px-3 py-2.5 text-right">{num(d.resumo.celulas ?? 0)}</td>
                    <td className={`num px-3 py-2.5 text-right font-medium ${d.resumo.revisar ? "text-revisar" : "text-slate-400"}`}>{num(d.resumo.revisar ?? 0)}</td>
                    <td className="num px-3 py-2.5 text-xs text-slate-600">{d.vigencia_fim ? `até ${data(d.vigencia_fim)}` : "—"}</td>
                    <td className="num px-4 py-2.5 text-xs text-slate-500">{dataHora(d.recebido_em)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Cartao>
    </>
  );
}
