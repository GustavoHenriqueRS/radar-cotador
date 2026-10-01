import { useId, useMemo } from "react";

const LADO = 40;

/** Quadrados em posições pseudoaleatórias, mas fixas: a página sai igual em toda visita e em toda gravação. */
function quadrados(quantidade: number, colunas: number, linhas: number) {
  let semente = 7;
  const proximo = () => {
    semente = (semente * 1103515245 + 12345) % 2147483648;
    return semente / 2147483648;
  };
  return Array.from({ length: quantidade }, (_, i) => ({
    x: Math.floor(proximo() * colunas),
    y: Math.floor(proximo() * linhas),
    atraso: (i * 0.37) % 6,
  }));
}

/** Grade de fundo com quadrados que acendem e apagam devagar, só com CSS. */
export function GradeAnimada({ className = "" }: { className?: string }) {
  const id = useId().replace(/:/g, "");
  const pontos = useMemo(() => quadrados(34, 40, 18), []);
  return (
    <svg aria-hidden className={`pointer-events-none absolute inset-0 h-full w-full ${className}`}>
      <defs>
        <pattern id={id} width={LADO} height={LADO} patternUnits="userSpaceOnUse" x={-1} y={-1}>
          <path d={`M.5 ${LADO}V.5H${LADO}`} fill="none" stroke="currentColor" strokeOpacity={0.14} />
        </pattern>
      </defs>
      <rect width="100%" height="100%" fill={`url(#${id})`} />
      {pontos.map((p, i) => (
        <rect key={i} x={p.x * LADO} y={p.y * LADO} width={LADO - 1} height={LADO - 1} fill="currentColor"
          className="quadrado-grade" style={{ animationDelay: `${p.atraso}s` }} />
      ))}
    </svg>
  );
}
