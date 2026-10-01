import { useMemo, useState } from "react";
import type { Evento } from "../api";
import { Cabecalho } from "../components/Layout";
import { ItemEvento } from "../components/Eventos";
import { Cartao, Carregando, Erro, Vazio } from "../components/ui";
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

  return (
    <>
      <Cabecalho
        titulo="Radar"
        descricao="Tudo o que mudou ou precisa de atenção: reajustes entre versões, produtos que saíram da tabela, fontes que discordam, planos suspensos e operadoras canceladas na ANS, vigências vencidas."
      />
      <div className="mb-4 flex flex-wrap gap-2">
        <button type="button" onClick={() => setTipo(null)}
          className={`min-h-8 cursor-pointer rounded-full border px-3 text-sm ${!tipo ? "border-marinho bg-marinho text-white" : "border-borda bg-white text-slate-700 hover:bg-slate-50"}`}>
          Todos ({dados?.length ?? 0})
        </button>
        {tipos.map(([t, { nome, n }]) => (
          <button key={t} type="button" onClick={() => setTipo(t)}
            className={`min-h-8 cursor-pointer rounded-full border px-3 text-sm ${tipo === t ? "border-marinho bg-marinho text-white" : "border-borda bg-white text-slate-700 hover:bg-slate-50"}`}>
            {nome} ({n})
          </button>
        ))}
      </div>
      <Cartao>
        {erro && <Erro mensagem={erro} />}
        {!dados ? <Carregando /> : lista.length === 0 ? <Vazio>Nenhum evento.</Vazio> : (
          <ul className="divide-y divide-borda">{lista.map((e) => <ItemEvento key={e.id} e={e} />)}</ul>
        )}
      </Cartao>
    </>
  );
}
