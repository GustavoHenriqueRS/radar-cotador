import { useState } from "react";
import { Link } from "react-router-dom";
import { AlertTriangle, BadgeCheck, CalendarDays, FileText, ScanLine } from "lucide-react";
import { post, type ResultadoCotacao } from "../api";
import { Cabecalho } from "../components/Layout";
import { AtributosDoRegistro, AvisosDeRede, RedeDoPlano, SeloRede } from "../components/Rede";
import { Botao, Cartao, Erro, Selo, Vazio } from "../components/ui";
import { brl, data, pct } from "../formato";

const UFS = ["AC", "AL", "AM", "AP", "BA", "CE", "DF", "ES", "GO", "MA", "MG", "MS", "MT", "PA", "PB", "PE", "PI", "PR", "RJ", "RN", "RO", "RR", "RS", "SC", "SE", "SP", "TO"];
const mesAno = (iso: string | null) => (iso ? `${iso.slice(5, 7)}/${iso.slice(0, 4)}` : "sem data");
const mesesAtras = (iso: string | null) => (iso ? (Date.now() - new Date(iso).getTime()) / (30.4 * 86400000) : Infinity);

export function Cotacao() {
  const [idades, setIdades] = useState("38, 36, 9");
  const [tipo, setTipo] = useState("");
  const [uf, setUf] = useState("");
  const [ufCotada, setUfCotada] = useState("");
  const [resultado, setResultado] = useState<ResultadoCotacao[] | null>(null);
  const [erro, setErro] = useState<string | null>(null);
  const [carregando, setCarregando] = useState(false);

  async function cotar() {
    setCarregando(true);
    setErro(null);
    try {
      const lista = idades.split(/[,;\s]+/).filter(Boolean).map(Number);
      setResultado(await post<ResultadoCotacao[]>("cotacao", { idades: lista, tipo, uf }));
      setUfCotada(uf);
    } catch (e) {
      setErro((e as Error).message);
    } finally {
      setCarregando(false);
    }
  }

  return (
    <>
      <Cabecalho
        titulo="Cotação"
        descricao="A visão do corretor: preço por beneficiário a partir das tabelas publicadas, sempre com a origem do dado à vista (fonte, versão, quando foi confirmado e como foi lido), e o que o registro do produto na ANS diz sobre reembolso, coparticipação e rede hospitalar."
      />
      <Cartao className="mb-5">
        <form className="flex flex-wrap items-end gap-3 p-4" onSubmit={(e) => { e.preventDefault(); cotar(); }}>
          <label className="text-sm text-slate-700">
            Idades dos beneficiários
            <input value={idades} onChange={(e) => setIdades(e.target.value)} inputMode="numeric"
              className="num mt-1 block min-h-10 w-56 rounded-md border border-borda px-3 text-sm" aria-describedby="ajuda-idades" />
            <span id="ajuda-idades" className="mt-1 block text-xs text-slate-500">Separe por vírgula. Ex.: 38, 36, 9</span>
          </label>
          <label className="text-sm text-slate-700">
            Contratação
            <select value={tipo} onChange={(e) => setTipo(e.target.value)} className="mt-1 block min-h-10 rounded-md border border-borda bg-white px-3 text-sm">
              <option value="">Todas</option>
              <option value="adesão">Coletivo por adesão</option>
              <option value="empresarial">Coletivo empresarial</option>
            </select>
            <span className="mt-1 block text-xs text-transparent">.</span>
          </label>
          <label className="text-sm text-slate-700">
            UF do cliente
            <select value={uf} onChange={(e) => setUf(e.target.value)} className="mt-1 block min-h-10 rounded-md border border-borda bg-white px-3 text-sm"
              aria-describedby="ajuda-uf">
              <option value="">Todas</option>
              {UFS.map((u) => <option key={u} value={u}>{u}</option>)}
            </select>
            <span id="ajuda-uf" className="mt-1 block text-xs text-slate-500">Rede e mudanças de rede desse estado</span>
          </label>
          <div className="pb-6"><Botao tipo="primario" carregando={carregando} onClick={cotar}>Cotar</Botao></div>
        </form>
      </Cartao>
      {erro && <Erro mensagem={erro} />}
      {resultado && (resultado.length === 0 ? <Cartao><Vazio>Nenhuma tabela publicada cobre essas idades.</Vazio></Cartao> : (
        <ol className="space-y-3">
          {resultado.slice(0, 40).map((r) => (
            <li key={r.tabela_id} className="rounded-lg border border-borda bg-white p-4">
              <div className="flex items-start justify-between gap-4">
                <div className="min-w-0 flex-1">
                  <p className="font-medium text-slate-900">{r.plano}</p>
                  <p className="text-sm text-slate-600">{r.operadora} · {r.tipo_contratacao}</p>
                  <p className="mt-0.5 truncate text-xs text-slate-500" title={r.condicao}>
                    <span className="font-mono">{r.registro_ans}</span> · {r.condicao}
                  </p>
                </div>
                <div className="shrink-0 text-right">
                  <p className="num text-xl font-semibold text-slate-900">{brl(r.total)}</p>
                  <p className="text-xs text-slate-500">por mês, {r.por_pessoa.length} pessoa(s)</p>
                </div>
              </div>
              <p className="num mt-2 flex flex-wrap gap-x-4 text-xs text-slate-600">
                {r.por_pessoa.map((p, i) => <span key={i}>{p.idade} anos ({p.faixa}): {brl(p.valor)}</span>)}
              </p>
              <AtributosDoRegistro ans={r.ans} />
              <AvisosDeRede mudancas={r.mudancas_de_rede} />
              {r.divergencias.map((d, i) => (
                <p key={i} role="note" className={`mt-2 flex items-start gap-1.5 rounded-md px-2.5 py-1.5 text-xs ${d.outra_mais_recente ? "bg-revisar-fundo text-revisar" : "bg-info-fundo text-info"}`}>
                  <AlertTriangle size={14} className="mt-px shrink-0" aria-hidden />
                  <span>
                    {d.fonte} tem este produto por <span className="num font-semibold">{brl(d.total)}</span> ({pct(d.diferenca)}), material de {mesAno(d.data_material)}.{" "}
                    {d.outra_mais_recente ? "Esta tabela é mais antiga: confirme antes de enviar a proposta." : "O material desta fonte é mais recente."}
                  </span>
                </p>
              ))}
              <div className="mt-3 flex flex-wrap items-center gap-2 border-t border-borda pt-3">
                <Selo tom="info" icone={<FileText size={12} aria-hidden />}>Fonte: {r.fonte}</Selo>
                <Selo tom="info">versão {r.versao}</Selo>
                <Selo tom={mesesAtras(r.data_material) > 6 ? "revisar" : "ok"} icone={<CalendarDays size={12} aria-hidden />}>
                  material de {mesAno(r.data_material)}
                </Selo>
                {r.divergencias.length === 0 && <Selo tom="ok" icone={<BadgeCheck size={12} aria-hidden />}>sem divergência entre fontes</Selo>}
                <Selo tom="leitura" icone={<ScanLine size={12} aria-hidden />}>{r.dupla_leitura ? "dupla leitura" : "leitura geométrica + ANS"}</Selo>
                {r.vigencia_fim && <Selo tom="info">vigente até {data(r.vigencia_fim)}</Selo>}
                <SeloRede rede={r.rede} uf={ufCotada} naUf={r.rede_na_uf} />
                <Link to={`/documentos/${r.documento_id}`} className="ml-auto text-xs font-medium text-acao hover:underline">ver no documento de origem</Link>
              </div>
              {r.rede && <RedeDoPlano key={`${r.tabela_id}-${ufCotada}`} tabelaId={r.tabela_id} ufInicial={ufCotada} />}
            </li>
          ))}
        </ol>
      ))}
    </>
  );
}
