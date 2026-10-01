import { useState } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";
import type { Celula, Coluna } from "../api";
import { urlPagina } from "../estatico";
import { brl } from "../formato";
import { COR_CAIXA, estadoCelula } from "./ui";

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

/** A página do PDF com cada preço lido destacado no lugar exato de onde saiu. */
export function VisorPagina({ documentoId, pagina, totalPaginas, tamanho, colunas, selecionada, aoSelecionar, aoMudarPagina }: Props) {
  const [carregou, setCarregou] = useState(false);
  const [largura, altura] = tamanho ?? [595, 842];
  const naPagina = colunas.filter((c) => c.pagina === pagina);

  return (
    <div className="rounded-lg border border-borda bg-white">
      <div className="flex items-center justify-between border-b border-borda px-3 py-2">
        <p className="text-sm font-medium text-slate-700">
          Página <span className="num">{pagina}</span> de <span className="num">{totalPaginas}</span>
        </p>
        <div className="flex gap-1">
          <button type="button" aria-label="Página anterior" disabled={pagina <= 1} onClick={() => aoMudarPagina(pagina - 1)}
            className="grid size-9 cursor-pointer place-items-center rounded-md hover:bg-slate-100 disabled:cursor-not-allowed disabled:opacity-40">
            <ChevronLeft size={18} aria-hidden />
          </button>
          <button type="button" aria-label="Próxima página" disabled={pagina >= totalPaginas} onClick={() => aoMudarPagina(pagina + 1)}
            className="grid size-9 cursor-pointer place-items-center rounded-md hover:bg-slate-100 disabled:cursor-not-allowed disabled:opacity-40">
            <ChevronRight size={18} aria-hidden />
          </button>
        </div>
      </div>
      <div className="relative bg-slate-100" style={{ aspectRatio: `${largura} / ${altura}` }}>
        {!carregou && <div className="absolute inset-0 animate-pulse bg-slate-200" aria-hidden />}
        <img
          key={`${documentoId}-${pagina}`}
          src={urlPagina(documentoId, pagina)}
          alt={`Página ${pagina} do documento, com os preços lidos destacados`}
          className="absolute inset-0 h-full w-full"
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
  );
}
