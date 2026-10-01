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

export function ItemEvento({ e }: { e: Evento }) {
  const Icone = ICONES[e.tipo] ?? FilePlus2;
  const variacao = typeof e.detalhe?.variacao_mediana === "number" ? (e.detalhe.variacao_mediana as number) : null;
  const itens = Array.isArray(e.detalhe?.itens) ? (e.detalhe.itens as ItemDetalhe[]) : [];
  return (
    <li className="flex gap-3 px-4 py-3">
      <span className={`mt-0.5 grid size-8 shrink-0 place-items-center rounded-md ${TOM[e.severidade] ?? TOM.info}`}>
        <Icone size={16} aria-hidden />
      </span>
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
            <Link className="text-acao underline-offset-2 hover:underline" to={`/documentos/${e.documento_id}`}>
              {e.documento}
            </Link>
          )}
          <span>{dataHora(e.criado_em)}</span>
        </p>
      </div>
    </li>
  );
}
