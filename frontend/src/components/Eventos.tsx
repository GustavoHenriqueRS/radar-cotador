import { Link } from "react-router-dom";
import {
  ArrowDownUp, Ban, Building2, CalendarX, CloudDownload, FileClock, FilePlus2, GitCompareArrows, History, PackageMinus, PackagePlus, SearchX,
  ServerCrash, ShieldAlert, Shuffle, TrendingUp,
} from "lucide-react";
import type { Evento } from "../api";
import { data, dataHora, pct } from "../formato";

const ICONES: Record<string, typeof Ban> = {
  tabela_nova: FilePlus2,
  reajuste: TrendingUp,
  produto_novo: PackagePlus,
  produto_removido: PackageMinus,
  condicao_alterada: Shuffle,
  versao_coletada: CloudDownload,
  versao_historica: History,
  coleta_falhou: ServerCrash,
  fonte_divergente: GitCompareArrows,
  registro_invalido: SearchX,
  plano_suspenso: ShieldAlert,
  operadora_cancelada: Ban,
  rede_alterada: Building2,
  preco_fora_da_banda: ArrowDownUp,
  vigencia_vencida: CalendarX,
  nota_tecnica_nova: FileClock,
};

const TOM: Record<string, string> = {
  erro: "text-erro bg-erro-fundo",
  alerta: "text-revisar bg-revisar-fundo",
  info: "text-acao bg-sky-50",
};

interface ItemDetalhe {
  registro?: string;
  plano?: string;
  mensagem?: string;
  variacao_mediana?: number;
  outra_fonte?: string;
}

const registroFormatado = (r?: string) =>
  r && r.length === 9 ? `${r.slice(0, 3)}.${r.slice(3, 6)}/${r.slice(6, 8)}-${r[8]}` : r ?? "";

function ConteudoEvento({ e }: { e: Evento }) {
  const variacao = typeof e.detalhe?.variacao_mediana === "number" ? (e.detalhe.variacao_mediana as number) : null;
  const itens = Array.isArray(e.detalhe?.itens) ? (e.detalhe.itens as ItemDetalhe[]) : [];
  return (
    <div className="min-w-0 flex-1">
      <p className="break-words text-sm text-slate-900">{e.titulo}</p>
      {itens.length > 1 && (
        <details className="mt-1 text-xs text-slate-600">
          <summary className="cursor-pointer text-acao">ver os {itens.length} itens</summary>
          <ul className="mt-1 space-y-0.5 border-l-2 border-borda pl-3">
            {itens.slice(0, 25).map((i, k) => (
              <li key={k}>
                <span className="font-mono">{registroFormatado(i.registro)}</span>{" "}
                {i.mensagem?.replace(/^Plano [\d./-]+: /, "") ?? i.plano}
                {typeof i.variacao_mediana === "number" && <span className="num"> · {pct(i.variacao_mediana)}</span>}
              </li>
            ))}
            {itens.length > 25 && <li>… e mais {itens.length - 25}</li>}
          </ul>
        </details>
      )}
      <p className="mt-0.5 flex flex-wrap gap-x-3 gap-y-0.5 text-xs text-slate-500">
        <span className="font-medium text-slate-600">{e.tipo_nome}</span>
        {e.registro_ans && <span className="font-mono">{e.registro_ans}</span>}
        {variacao !== null && <span className="num">{pct(variacao)}</span>}
        {e.data_efeito && <span>efeito em {data(e.data_efeito)}</span>}
        {e.documento_id && (
          <Link className="break-all text-acao underline-offset-2 hover:underline" to={`/documentos/${e.documento_id}`}>
            {e.documento}
          </Link>
        )}
        <span>{dataHora(e.criado_em)}</span>
      </p>
    </div>
  );
}

export function ItemEvento({ e }: { e: Evento }) {
  const Icone = ICONES[e.tipo] ?? FilePlus2;
  return (
    <li className="flex gap-3 px-4 py-3">
      <span className={`mt-0.5 grid size-8 shrink-0 place-items-center rounded-md ${TOM[e.severidade] ?? TOM.info}`}>
        <Icone size={16} aria-hidden />
      </span>
      <ConteudoEvento e={e} />
    </li>
  );
}

const diaDoEvento = (e: Evento) => (e.data_efeito ?? e.criado_em).slice(0, 10);
const COLUNAS = "grid grid-cols-[4.5rem_minmax(0,1fr)] gap-x-6 sm:grid-cols-[5.5rem_minmax(0,1fr)]";

/** Os eventos na data em que valem, do mais novo para o mais antigo, com o dia de hoje marcado: o que está acima ainda vai acontecer. */
export function LinhaDoTempo({ eventos }: { eventos: Evento[] }) {
  const hoje = new Date().toLocaleDateString("sv-SE");
  const ordenados = eventos
    .map((e) => ({ e, dia: diaDoEvento(e) }))
    .sort((a, b) => b.dia.localeCompare(a.dia) || b.e.id - a.e.id);
  const linhas: React.ReactNode[] = [];
  let marcouHoje = false;
  let diaAnterior = "";
  for (const { e, dia } of ordenados) {
    if (!marcouHoje && dia <= hoje) {
      marcouHoje = true;
      linhas.push(
        <li key="hoje" className={COLUNAS}>
          <p className="py-2 text-right text-xs font-semibold uppercase tracking-wide text-acao">Hoje</p>
          <div className="relative flex items-center border-l-2 border-sky-200 py-2 pl-6">
            <span className="absolute -left-[7px] size-3 rounded-full bg-acao ring-4 ring-white" aria-hidden />
            <span className="num text-xs font-medium text-acao">{data(hoje)}</span>
            <span className="ml-3 h-px flex-1 bg-sky-200" aria-hidden />
          </div>
        </li>,
      );
    }
    const Icone = ICONES[e.tipo] ?? FilePlus2;
    const futuro = dia > hoje;
    linhas.push(
      <li key={e.id} className={COLUNAS}>
        <div className="pt-3 text-right">
          {dia !== diaAnterior && dia !== hoje && <time dateTime={dia} className="num text-xs font-medium text-slate-500">{data(dia)}</time>}
          {dia !== diaAnterior && futuro && <p className="mt-0.5 text-[11px] font-medium text-acao">a caminho</p>}
        </div>
        <div className={`relative border-l-2 pb-2 pl-6 ${futuro ? "border-dashed border-sky-200" : "border-borda"}`}>
          <span className={`absolute -left-[17px] top-2 grid size-8 place-items-center rounded-full ring-4 ring-white ${TOM[e.severidade] ?? TOM.info}`}>
            <Icone size={15} aria-hidden />
          </span>
          <div className="rounded-lg px-3 py-2.5 transition-colors duration-150 hover:bg-slate-50">
            <ConteudoEvento e={e} />
          </div>
        </div>
      </li>,
    );
    diaAnterior = dia;
  }
  return <ol className="px-2 py-3 sm:px-4">{linhas}</ol>;
}
