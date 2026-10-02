import { useEffect, useLayoutEffect, useRef, useState } from "react";
import type { CSSProperties, ReactNode } from "react";
import { AlertTriangle, CheckCircle2, Info, Loader2, PencilLine, ScanLine, XCircle } from "lucide-react";
import type { Celula, Severidade } from "../api";

export function Cartao({ titulo, acao, children, className = "" }: { titulo?: ReactNode; acao?: ReactNode; children: ReactNode; className?: string }) {
  return (
    <section className={`rounded-lg border border-borda bg-white ${className}`}>
      {titulo && (
        <header className="flex items-center justify-between gap-3 border-b border-borda px-4 py-3">
          <h2 className="text-sm font-semibold text-slate-800">{titulo}</h2>
          {acao}
        </header>
      )}
      {children}
    </section>
  );
}

const semMovimento = () => typeof window !== "undefined" && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

/** Conta de zero até o valor quando a tela abre; com movimento reduzido, mostra o valor direto. */
export function ContaAte({ valor, formato, duracao = 800 }: { valor: number; formato: (v: number) => string; duracao?: number }) {
  const [atual, setAtual] = useState(() => (semMovimento() ? valor : 0));
  useEffect(() => {
    if (semMovimento()) { setAtual(valor); return; }
    const inicio = performance.now();
    let quadro = 0;
    const passo = (agora: number) => {
      const p = Math.min(1, (agora - inicio) / duracao);
      setAtual(valor * (1 - Math.pow(1 - p, 3)));
      if (p < 1) quadro = requestAnimationFrame(passo);
    };
    quadro = requestAnimationFrame(passo);
    return () => cancelAnimationFrame(quadro);
  }, [valor, duracao]);
  return <>{formato(atual)}</>;
}

const COR_TOM = { neutro: "text-slate-900", ok: "text-ok", revisar: "text-revisar", erro: "text-erro" };
const BARRA_TOM = { neutro: "bg-slate-400", ok: "bg-green-600", revisar: "bg-amber-500", erro: "bg-red-600" };

export function Kpi({ rotulo, valor, detalhe, tom = "neutro", proporcao }: {
  rotulo: string; valor: ReactNode; detalhe?: ReactNode; tom?: "neutro" | "ok" | "revisar" | "erro"; proporcao?: number;
}) {
  const [cheia, setCheia] = useState(semMovimento());
  useEffect(() => {
    const q = requestAnimationFrame(() => setCheia(true));
    return () => cancelAnimationFrame(q);
  }, []);
  return (
    <div className="flex flex-col rounded-lg border border-borda bg-white px-4 py-3">
      <p className="text-xs font-medium uppercase tracking-wide text-slate-500">{rotulo}</p>
      <p className={`num mt-1 text-2xl font-semibold ${COR_TOM[tom]}`}>{valor}</p>
      {detalhe && <p className="mt-0.5 text-xs text-slate-500">{detalhe}</p>}
      {proporcao !== undefined && (
        <div className="mt-auto pt-2.5" aria-hidden>
          <div className="h-1.5 overflow-hidden rounded-full bg-slate-100">
            <div className={`h-full rounded-full ${BARRA_TOM[tom]} transition-[width] duration-700 ease-out motion-reduce:transition-none`}
              style={{ width: `${(cheia ? proporcao : 0) * 100}%` }} />
          </div>
        </div>
      )}
    </div>
  );
}

/**
 * Posição do item ativo dentro de um grupo de botões, para um fundo que desliza até ele.
 * O grupo precisa ser `relative` e o botão ativo, marcado com `data-ativo="true"`.
 */
export function useDeslizante<T extends HTMLElement>(ativo: string | null, ...extras: unknown[]) {
  const grupo = useRef<T>(null);
  const [caixa, setCaixa] = useState<{ x: number; y: number; w: number; h: number } | null>(null);
  const [animar, setAnimar] = useState(false);
  useLayoutEffect(() => {
    const medir = () => {
      const el = grupo.current?.querySelector<HTMLElement>('[data-ativo="true"]');
      if (el) setCaixa({ x: el.offsetLeft, y: el.offsetTop, w: el.offsetWidth, h: el.offsetHeight });
    };
    medir();
    const observador = new ResizeObserver(medir);
    if (grupo.current) observador.observe(grupo.current);
    return () => observador.disconnect();
  }, [ativo, ...extras]);
  useEffect(() => {
    if (!caixa || animar) return;
    const q = requestAnimationFrame(() => setAnimar(true));
    return () => cancelAnimationFrame(q);
  }, [caixa, animar]);
  const estilo: CSSProperties = caixa
    ? { transform: `translate(${caixa.x}px, ${caixa.y}px)`, width: caixa.w, height: caixa.h }
    : { opacity: 0 };
  const classe = `pointer-events-none absolute left-0 top-0 ${animar ? "transition-[transform,width,height] duration-300 ease-out motion-reduce:transition-none" : ""}`;
  return { grupo, estilo, classe };
}

const ESTILO_SEVERIDADE: Record<Severidade, { classe: string; Icone: typeof Info; rotulo: string }> = {
  erro: { classe: "bg-erro-fundo text-erro border-red-200", Icone: XCircle, rotulo: "Erro" },
  alerta: { classe: "bg-revisar-fundo text-revisar border-amber-200", Icone: AlertTriangle, rotulo: "Alerta" },
  info: { classe: "bg-info-fundo text-info border-slate-200", Icone: Info, rotulo: "Info" },
};

export function IconeSeveridade({ severidade, tamanho = 16 }: { severidade: Severidade; tamanho?: number }) {
  const { Icone, classe } = ESTILO_SEVERIDADE[severidade] ?? ESTILO_SEVERIDADE.info;
  return <Icone aria-hidden size={tamanho} className={`shrink-0 ${classe.split(" ")[1]}`} />;
}

export function Selo({ children, tom = "info", icone }: { children: ReactNode; tom?: "ok" | "revisar" | "erro" | "info" | "leitura" | "marinho"; icone?: ReactNode }) {
  const classe = {
    ok: "bg-ok-fundo text-ok border-green-200",
    revisar: "bg-revisar-fundo text-revisar border-amber-200",
    erro: "bg-erro-fundo text-erro border-red-200",
    info: "bg-info-fundo text-info border-slate-200",
    leitura: "bg-leitura-fundo text-leitura border-blue-200",
    marinho: "bg-marinho text-white border-marinho",
  }[tom];
  return (
    <span className={`inline-flex items-center gap-1 whitespace-nowrap rounded-md border px-1.5 py-0.5 text-xs font-medium ${classe}`}>
      {icone}
      {children}
    </span>
  );
}

const STATUS_DOCUMENTO: Record<string, { rotulo: string; tom: "ok" | "revisar" | "erro" | "info" | "leitura" }> = {
  processando: { rotulo: "Processando", tom: "leitura" },
  em_revisao: { rotulo: "Em revisão", tom: "revisar" },
  publicado: { rotulo: "Publicado", tom: "ok" },
  historico: { rotulo: "No histórico", tom: "info" },
  descartado: { rotulo: "Descartado", tom: "info" },
  erro: { rotulo: "Erro", tom: "erro" },
};

export function SeloStatusDocumento({ status }: { status: string }) {
  const s = STATUS_DOCUMENTO[status] ?? { rotulo: status, tom: "info" as const };
  return (
    <Selo tom={s.tom} icone={status === "processando" ? <Loader2 size={12} className="animate-spin" aria-hidden /> : undefined}>
      {s.rotulo}
    </Selo>
  );
}

export function SeloLeitura({ leitura, ocr }: { leitura: string; ocr: boolean }) {
  const base = ocr ? "OCR" : "Geométrica";
  if (leitura === "nenhuma") return <Selo tom="info" icone={<ScanLine size={12} aria-hidden />}>{base}</Selo>;
  if (leitura === "falhou") return <Selo tom="revisar" icone={<ScanLine size={12} aria-hidden />}>{base} · LLM falhou</Selo>;
  return (
    <Selo tom="leitura" icone={<ScanLine size={12} aria-hidden />}>
      {base} + LLM{leitura === "gravada" ? " (gravada)" : ""}
    </Selo>
  );
}

/** Estado visual de uma célula: o que a pessoa precisa fazer com ela. */
export function estadoCelula(c: Celula): { tom: "ok" | "revisar" | "erro" | "leitura"; rotulo: string; Icone: typeof Info } {
  if (c.corrigida) return { tom: "ok", rotulo: "Corrigido por pessoa", Icone: PencilLine };
  if (c.status === "divergente") return { tom: "erro", rotulo: "Leituras divergem", Icone: XCircle };
  if (c.revisar) return { tom: "revisar", rotulo: "Revisar", Icone: AlertTriangle };
  if (c.status === "confirmado") return { tom: "ok", rotulo: "Confirmado pelas duas leituras", Icone: CheckCircle2 };
  if (c.status === "confirmado_calculo") return { tom: "ok", rotulo: "Confirmado por uma leitura e pelo cálculo do padrão de faixas", Icone: CheckCircle2 };
  return { tom: "leitura", rotulo: c.status === "so_llm" ? "Lido só pelo LLM" : "Lido (leitura única)", Icone: ScanLine };
}

export const COR_CAIXA: Record<string, string> = {
  ok: "border-green-600 bg-green-500/15",
  revisar: "border-amber-500 bg-amber-400/30",
  erro: "border-red-600 bg-red-500/25",
  leitura: "border-blue-500/70 bg-blue-400/10",
};

export function Botao({ children, onClick, tipo = "secundario", disabled, carregando, title }: {
  children: ReactNode; onClick?: () => void; tipo?: "primario" | "secundario" | "fantasma"; disabled?: boolean; carregando?: boolean; title?: string;
}) {
  const classe = {
    primario: "bg-acao text-white hover:bg-acao-escura border-acao",
    secundario: "bg-white text-slate-800 hover:bg-slate-50 border-borda",
    fantasma: "bg-transparent text-slate-700 hover:bg-slate-100 border-transparent",
  }[tipo];
  return (
    <button
      type="button"
      title={title}
      onClick={onClick}
      disabled={disabled || carregando}
      className={`inline-flex min-h-9 cursor-pointer items-center gap-1.5 rounded-md border px-3 py-1.5 text-sm font-medium transition-colors duration-150 disabled:cursor-not-allowed disabled:opacity-50 ${classe}`}
    >
      {carregando && <Loader2 size={14} className="animate-spin" aria-hidden />}
      {children}
    </button>
  );
}

export function Carregando({ texto = "Carregando…" }: { texto?: string }) {
  return (
    <div className="flex items-center gap-2 p-6 text-sm text-slate-500" role="status">
      <Loader2 size={16} className="animate-spin" aria-hidden /> {texto}
    </div>
  );
}

export function Vazio({ children }: { children: ReactNode }) {
  return <div className="p-6 text-center text-sm text-slate-500">{children}</div>;
}

export function Erro({ mensagem }: { mensagem: string }) {
  return (
    <div role="alert" className="m-4 flex items-start gap-2 rounded-md border border-red-200 bg-erro-fundo p-3 text-sm text-erro">
      <XCircle size={16} aria-hidden className="mt-0.5" /> {mensagem}
    </div>
  );
}
