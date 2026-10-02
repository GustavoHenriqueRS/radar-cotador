import { Link } from "react-router-dom";
import { Ban, CheckCircle2 } from "lucide-react";
import type { DocumentoResumo, OperadoraSaude, Painel as TPainel } from "../api";
import { Cabecalho } from "../components/Layout";
import { ItemEvento } from "../components/Eventos";
import { Cartao, Carregando, ContaAte, Erro, Kpi, Selo, SeloLeitura, Vazio } from "../components/ui";
import { data, num } from "../formato";
import { useApi } from "../usarApi";

export function Painel() {
  const { dados, erro } = useApi<TPainel>("painel");
  const operadoras = useApi<OperadoraSaude[]>("operadoras");
  const fila = useApi<DocumentoResumo[]>("documentos?status=em_revisao");

  if (erro) return <Erro mensagem={erro} />;
  if (!dados) return <Carregando />;

  const semRevisao = dados.precos_com_produto ? dados.precos_com_produto_sem_revisao / dados.precos_com_produto : 0;
  const custo = Number(dados.custo_llm_usd || 0);
  const inteiro = (v: number) => num(Math.round(v));
  const conta = (v: number) => <ContaAte valor={v} formato={inteiro} />;
  return (
    <>
      <Cabecalho
        titulo="Painel"
        descricao="Cada preço vem de um documento e de uma posição na página, é conferido contra a ANS e só chega a uma pessoa quando algo não fecha."
      />
      <div className="grid grid-cols-2 gap-3 md:grid-cols-3 xl:grid-cols-6">
        <Kpi rotulo="Preços lidos" valor={conta(dados.precos_lidos)} detalhe={`${num(dados.documentos)} documentos · LLM ${custo ? `US$ ${custo.toFixed(2)}` : "desligado"}`} />
        <Kpi rotulo="Sem revisão humana" valor={<ContaAte valor={semRevisao * 100} formato={(v) => `${Math.round(v)}%`} />} proporcao={semRevisao} detalhe={`${num(dados.precos_com_produto_sem_revisao)} de ${num(dados.precos_com_produto)} preços`} tom="ok" />
        <Kpi rotulo="Para revisar" valor={conta(dados.precos_revisar)} detalhe="apontados por regra ou leitura" tom={dados.precos_revisar ? "revisar" : "ok"} />
        <Kpi rotulo="Sem produto identificado" valor={conta(dados.precos_sem_produto)} proporcao={dados.precos_lidos ? dados.precos_sem_produto / dados.precos_lidos : 0} detalhe="PDF sem registro ANS: mapear coluna" tom={dados.precos_sem_produto ? "revisar" : "ok"} />
        <Kpi rotulo="Tabelas publicadas" valor={conta(dados.tabelas_ativas)} detalhe={`${num(dados.operadoras_com_tabela)} operadoras`} />
        <Kpi rotulo="Alertas abertos" valor={conta(dados.eventos_abertos)} detalhe={`${num(dados.tabelas_vencidas)} tabelas vencidas`} tom={dados.eventos_abertos ? "erro" : "ok"} />
      </div>

      <div className="mt-5 grid grid-cols-1 gap-5 xl:grid-cols-[minmax(0,1fr)_380px]">
        <Cartao titulo="Radar: o que mudou" acao={<Link to="/radar" className="text-sm text-acao hover:underline">ver tudo</Link>}>
          {dados.eventos.length ? (
            <ul className="divide-y divide-borda">{dados.eventos.map((e) => <ItemEvento key={e.id} e={e} />)}</ul>
          ) : (
            <Vazio>Nenhum evento ainda.</Vazio>
          )}
        </Cartao>

        <div className="space-y-5">
          <Cartao titulo="Operadoras do Cotador: ANS e canal do preço">
            {operadoras.dados ? (
              <ul className="divide-y divide-borda">
                {operadoras.dados.map((o) => (
                  <li key={o.registro_ans} className="flex items-center justify-between gap-3 px-4 py-2.5">
                    <div className="min-w-0">
                      <p className="truncate text-sm text-slate-900">{o.nome} <span className="font-mono text-xs text-slate-500">ANS {o.registro_ans}</span></p>
                      {o.canal && <p className="text-xs text-slate-500">{o.canal}</p>}
                    </div>
                    {o.ativa ? (
                      <Selo tom="ok" icone={<CheckCircle2 size={12} aria-hidden />}>Ativa</Selo>
                    ) : (
                      <Selo tom="erro" icone={<Ban size={12} aria-hidden />}>Cancelada em {data(o.cancelada_em)}</Selo>
                    )}
                  </li>
                ))}
              </ul>
            ) : (
              <Carregando />
            )}
          </Cartao>

          <Cartao titulo="Fila de revisão">
            {fila.dados?.length ? (
              <ul className="divide-y divide-borda">
                {fila.dados
                  .slice()
                  .sort((a, b) => (a.resumo.revisar ?? 0) - (b.resumo.revisar ?? 0))
                  .map((d) => (
                    <li key={d.id}>
                      <Link to={`/documentos/${d.id}`} className="flex items-center justify-between gap-3 px-4 py-2.5 hover:bg-slate-50">
                        <div className="min-w-0">
                          <p className="truncate text-sm text-slate-900">{d.nome}</p>
                          <p className="text-xs text-slate-500">{d.fonte ?? "sem fonte"}</p>
                        </div>
                        <div className="flex shrink-0 items-center gap-2">
                          <SeloLeitura leitura={d.leitura_llm} ocr={d.ocr} />
                          <span className="num text-sm font-semibold text-revisar">{num(d.resumo.revisar ?? 0)}</span>
                        </div>
                      </Link>
                    </li>
                  ))}
              </ul>
            ) : (
              <Vazio>Nada esperando revisão.</Vazio>
            )}
          </Cartao>
        </div>
      </div>
    </>
  );
}
