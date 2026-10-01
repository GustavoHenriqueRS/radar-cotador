import { useCallback, useEffect, useLayoutEffect, useRef, useState } from "react";
import type { MouseEvent as EventoMouse, PointerEvent as EventoPonteiro } from "react";
import { ChevronLeft, ChevronRight, ZoomIn, ZoomOut } from "lucide-react";
import type { Celula, Coluna } from "../api";
import { urlPagina } from "../estatico";
import { brl } from "../formato";
import { COR_CAIXA, estadoCelula } from "./ui";

// A página é renderizada com o dobro da resolução do PDF: acima de 3x a imagem já perde nitidez.
const NIVEIS = [1, 1.5, 2, 3];
const ZOOM_MAXIMO = NIVEIS[NIVEIS.length - 1];
const limitar = (z: number) => (z < 1.03 ? 1 : Math.min(ZOOM_MAXIMO, z));

interface Props {
  documentoId: number;
  pagina: number;
  totalPaginas: number;
  tamanho: [number, number] | undefined;
  colunas: Coluna[];
  selecionada: { coluna: number; celula?: number } | null;
  aoSelecionar: (coluna: number, celula: number) => void;
  aoMudarPagina: (p: number) => void;
}

const BOTAO = "grid size-9 cursor-pointer place-items-center rounded-md hover:bg-slate-100 disabled:cursor-not-allowed disabled:opacity-40";

/** A página do PDF com cada preço lido destacado no lugar exato de onde saiu, com zoom para conferir o número. */
export function VisorPagina({ documentoId, pagina, totalPaginas, tamanho, colunas, selecionada, aoSelecionar, aoMudarPagina }: Props) {
  const [carregou, setCarregou] = useState(false);
  const [zoom, setZoom] = useState(1);
  const [arrastando, setArrastando] = useState(false);
  const janela = useRef<HTMLDivElement>(null);
  const zoomAtual = useRef(1);
  // O ponto da página que estava sob o cursor (ou no centro) fica no mesmo lugar da tela depois do zoom.
  const ancora = useRef<{ x: number; y: number; px: number; py: number; antes: number } | null>(null);
  const arraste = useRef<{ x: number; y: number; esquerda: number; topo: number } | null>(null);
  const [largura, altura] = tamanho ?? [595, 842];
  const naPagina = colunas.filter((c) => c.pagina === pagina);

  const aplicarZoom = useCallback((alvo: number, x?: number, y?: number) => {
    const el = janela.current;
    const novo = limitar(alvo);
    if (!el || novo === zoomAtual.current) return;
    const cx = x ?? el.clientWidth / 2;
    const cy = y ?? el.clientHeight / 2;
    ancora.current = { x: cx, y: cy, px: el.scrollLeft + cx, py: el.scrollTop + cy, antes: zoomAtual.current };
    zoomAtual.current = novo;
    setZoom(novo);
  }, []);

  useLayoutEffect(() => {
    const el = janela.current;
    const a = ancora.current;
    if (!el || !a) return;
    const fator = zoom / a.antes;
    el.scrollLeft = a.px * fator - a.x;
    el.scrollTop = a.py * fator - a.y;
    ancora.current = null;
  }, [zoom]);

  // Ctrl + roda do mouse (ou o gesto de pinça no trackpad) dá zoom no ponto do cursor, sem dar zoom na tela inteira.
  useEffect(() => {
    const el = janela.current;
    if (!el) return;
    const aoRolar = (e: WheelEvent) => {
      if (!e.ctrlKey && !e.metaKey) return;
      e.preventDefault();
      const delta = e.deltaMode === 1 ? e.deltaY * 33 : e.deltaY;
      const r = el.getBoundingClientRect();
      aplicarZoom(zoomAtual.current * Math.exp(-delta * 0.0025), e.clientX - r.left, e.clientY - r.top);
    };
    el.addEventListener("wheel", aoRolar, { passive: false });
    return () => el.removeEventListener("wheel", aoRolar);
  }, [aplicarZoom]);

  // Com zoom, a célula escolhida na lista ao lado é trazida para dentro da janela.
  useEffect(() => {
    const el = janela.current;
    if (!el || zoomAtual.current === 1 || selecionada?.celula == null) return;
    const alvo = el.querySelector<HTMLElement>(`[data-celula="${selecionada.celula}"]`);
    if (!alvo) return;
    const j = el.getBoundingClientRect();
    const c = alvo.getBoundingClientRect();
    if (c.left >= j.left && c.right <= j.right && c.top >= j.top && c.bottom <= j.bottom) return;
    const suave = !window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    el.scrollTo({
      left: el.scrollLeft + c.left - j.left - (j.width - c.width) / 2,
      top: el.scrollTop + c.top - j.top - (j.height - c.height) / 2,
      behavior: suave ? "smooth" : "auto",
    });
  }, [selecionada?.celula, pagina]);

  const sobreCelula = (alvo: EventTarget) => (alvo as HTMLElement).closest("button") !== null;

  const aoPressionar = (e: EventoPonteiro<HTMLDivElement>) => {
    const el = janela.current;
    if (!el || zoom === 1 || e.pointerType !== "mouse" || e.button !== 0 || sobreCelula(e.target)) return;
    arraste.current = { x: e.clientX, y: e.clientY, esquerda: el.scrollLeft, topo: el.scrollTop };
    el.setPointerCapture(e.pointerId);
    setArrastando(true);
  };

  const aoMover = (e: EventoPonteiro<HTMLDivElement>) => {
    const el = janela.current;
    const a = arraste.current;
    if (!el || !a) return;
    el.scrollLeft = a.esquerda - (e.clientX - a.x);
    el.scrollTop = a.topo - (e.clientY - a.y);
  };

  const aoSoltar = () => {
    arraste.current = null;
    setArrastando(false);
  };

  const aoClicarDuasVezes = (e: EventoMouse<HTMLDivElement>) => {
    const el = janela.current;
    if (!el || sobreCelula(e.target)) return;
    const r = el.getBoundingClientRect();
    aplicarZoom(zoom === 1 ? 2 : 1, e.clientX - r.left, e.clientY - r.top);
  };

  const proximo = NIVEIS.find((n) => n > zoom + 0.01) ?? ZOOM_MAXIMO;
  const anterior = [...NIVEIS].reverse().find((n) => n < zoom - 0.01) ?? 1;

  return (
    <div className="rounded-lg border border-borda bg-white">
      <div className="flex items-center justify-between gap-2 border-b border-borda px-3 py-2">
        <p className="text-sm font-medium text-slate-700">
          Página <span className="num">{pagina}</span> de <span className="num">{totalPaginas}</span>
        </p>
        <div className="flex items-center gap-1">
          <button type="button" aria-label="Diminuir o zoom" title="Diminuir o zoom (Ctrl + roda do mouse)" disabled={zoom <= 1}
            onClick={() => aplicarZoom(anterior)} className={BOTAO}>
            <ZoomOut size={18} aria-hidden />
          </button>
          <button type="button" aria-label="Voltar ao tamanho da página" title="Voltar ao tamanho da página" disabled={zoom === 1}
            onClick={() => aplicarZoom(1)}
            className="num h-9 w-14 cursor-pointer rounded-md text-sm text-slate-600 hover:bg-slate-100 disabled:cursor-default disabled:hover:bg-transparent">
            {Math.round(zoom * 100)}%
          </button>
          <button type="button" aria-label="Aumentar o zoom" title="Aumentar o zoom (Ctrl + roda do mouse ou duplo clique na página)"
            disabled={zoom >= ZOOM_MAXIMO} onClick={() => aplicarZoom(proximo)} className={BOTAO}>
            <ZoomIn size={18} aria-hidden />
          </button>
          <span className="mx-1 h-5 w-px bg-borda" aria-hidden />
          <button type="button" aria-label="Página anterior" disabled={pagina <= 1} onClick={() => aoMudarPagina(pagina - 1)} className={BOTAO}>
            <ChevronLeft size={18} aria-hidden />
          </button>
          <button type="button" aria-label="Próxima página" disabled={pagina >= totalPaginas} onClick={() => aoMudarPagina(pagina + 1)} className={BOTAO}>
            <ChevronRight size={18} aria-hidden />
          </button>
        </div>
      </div>
      <div
        ref={janela}
        className={`relative select-none overflow-auto bg-slate-100 ${zoom > 1 ? `overscroll-contain ${arrastando ? "cursor-grabbing" : "cursor-grab"}` : ""}`}
        style={{ aspectRatio: `${largura} / ${altura}` }}
        onPointerDown={aoPressionar}
        onPointerMove={aoMover}
        onPointerUp={aoSoltar}
        onPointerCancel={aoSoltar}
        onDoubleClick={aoClicarDuasVezes}
      >
        <div className="relative" style={{ width: `${zoom * 100}%`, aspectRatio: `${largura} / ${altura}` }}>
          {!carregou && <div className="absolute inset-0 animate-pulse bg-slate-200" aria-hidden />}
          <img
            key={`${documentoId}-${pagina}`}
            src={urlPagina(documentoId, pagina)}
            alt={`Página ${pagina} do documento, com os preços lidos destacados`}
            className="absolute inset-0 h-full w-full"
            draggable={false}
            onLoad={() => setCarregou(true)}
          />
          {naPagina.flatMap((col) =>
            col.celulas.filter((c) => c.caixa).map((c: Celula) => {
              const [x0, y0, x1, y1] = c.caixa!;
              const estado = estadoCelula(c);
              const ativa = selecionada?.coluna === col.id;
              const escolhida = ativa && selecionada?.celula === c.id;
              return (
                <button
                  type="button"
                  key={c.id}
                  data-celula={c.id}
                  title={`${col.registro_ans || col.coluna} · ${c.faixa}: ${brl(c.valor)} — ${estado.rotulo}`}
                  aria-label={`${c.faixa}: ${brl(c.valor)}, ${estado.rotulo}`}
                  onClick={() => aoSelecionar(col.id, c.id)}
                  className={`absolute cursor-pointer rounded-[2px] border transition-shadow duration-150 ${COR_CAIXA[estado.tom]} ${
                    escolhida ? "z-10 ring-2 ring-acao ring-offset-1" : ativa ? "ring-1 ring-acao/70" : ""
                  }`}
                  style={{
                    left: `${((x0 - 1.5) / largura) * 100}%`,
                    top: `${((y0 - 1.5) / altura) * 100}%`,
                    width: `${((x1 - x0 + 3) / largura) * 100}%`,
                    height: `${((y1 - y0 + 3) / altura) * 100}%`,
                  }}
                />
              );
            }),
          )}
        </div>
      </div>
    </div>
  );
}
