import { useMemo, useState } from "react";
import type { Evento } from "../api";
import { Cabecalho } from "../components/Layout";
import { LinhaDoTempo } from "../components/Eventos";
import { Cartao, Carregando, Erro, Vazio, useDeslizante } from "../components/ui";
import { useApi } from "../usarApi";

export function Radar() {
  const { dados, erro } = useApi<Evento[]>("eventos?limite=500");
  const [tipo, setTipo] = useState<string | null>(null);
  const tipos = useMemo(() => {
    const contagem = new Map<string, { nome: string; n: number }>();
    for (const e of dados ?? []) contagem.set(e.tipo, { nome: e.tipo_nome, n: (contagem.get(e.tipo)?.n ?? 0) + 1 });
    return [...contagem.entries()].sort((a, b) => b[1].n - a[1].n);
  }, [dados]);
  const lista = (dados ?? []).filter((e) => !tipo || e.tipo === tipo);
  const filtros = useDeslizante<HTMLDivElement>(tipo ?? "todos", tipos.length);
  const chip = (ativo: boolean) =>
    `relative min-h-8 cursor-pointer rounded-full border px-3 text-sm transition-colors duration-200 ${ativo ? "border-transparent text-white" : "border-borda bg-white text-slate-700 hover:bg-slate-50"}`;

  return (
    <>
      <Cabecalho
        titulo="Radar"
        descricao="Tudo o que mudou ou precisa de atenção: reajustes entre versões, produtos que saíram da tabela, fontes que discordam, planos suspensos e operadoras canceladas na ANS, vigências vencidas."
      />
      <div ref={filtros.grupo} className="relative mb-4 flex flex-wrap gap-2">
        <span aria-hidden className={`${filtros.classe} rounded-full bg-marinho`} style={filtros.estilo} />
        <button type="button" onClick={() => setTipo(null)} data-ativo={!tipo} aria-pressed={!tipo} className={chip(!tipo)}>
          Todos ({dados?.length ?? 0})
        </button>
        {tipos.map(([t, { nome, n }]) => (
          <button key={t} type="button" onClick={() => setTipo(t)} data-ativo={tipo === t} aria-pressed={tipo === t} className={chip(tipo === t)}>
            {nome} ({n})
          </button>
        ))}
      </div>
      <Cartao>
        {erro && <Erro mensagem={erro} />}
        {!dados ? <Carregando /> : lista.length === 0 ? <Vazio>Nenhum evento.</Vazio> : (
          <LinhaDoTempo eventos={lista} />
        )}
      </Cartao>
    </>
  );
}
