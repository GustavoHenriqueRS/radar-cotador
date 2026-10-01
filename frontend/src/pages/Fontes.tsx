import { useState } from "react";
import { Globe, History, Link2, Mail } from "lucide-react";
import { post, type Captura, type ColetaResumo, type Fonte } from "../api";
import { Cabecalho } from "../components/Layout";
import { Botao, Cartao, Carregando, Erro, Selo } from "../components/ui";
import { dataHora, num } from "../formato";
import { useApi } from "../usarApi";

const TOM_COLETA = { rodando: "leitura", ok: "ok", bloqueada: "revisar", erro: "erro" } as const;
const ICONE_CAPTURA = { pagina_publica: Globe, url_direta: Link2, wayback: History, caixa_email: Mail } as const;

export function Fontes() {
  const { dados, erro, recarregar } = useApi<Fonte[]>("fontes", 2500, (fs) =>
    fs.some((f) => f.capturas.some((c) => c.ultima_coleta?.situacao === "rodando")));
  const [falha, setFalha] = useState<string | null>(null);
  const [disparando, setDisparando] = useState<number | null>(null);

  async function coletar(c: Captura) {
    setDisparando(c.id);
    setFalha(null);
    try {
      await post(`capturas/${c.id}/coletar`);
      await recarregar();
    } catch (e) {
      setFalha((e as Error).message);
    } finally {
      setDisparando(null);
    }
  }

  return (
    <>
      <Cabecalho
        titulo="Fontes"
        descricao="De onde vem cada dado, com o nível de confiança, as regras de coleta (robots.txt, termos de uso, necessidade de parceria) e os fluxos de captura de cada fonte: página pública, endereço fixo, histórico no arquivo da web, caixa de e-mail. Os dados abertos da ANS entram como referência de todas."
      />
      {falha && <Erro mensagem={falha} />}
      <Cartao>
        {erro && <Erro mensagem={erro} />}
        {!dados ? <Carregando /> : (
          <ul className="divide-y divide-borda">
            {dados.map((f) => (
              <li key={f.id} className="grid gap-2 px-4 py-3 md:grid-cols-[220px_140px_1fr]">
                <div>
                  <p className="font-medium text-slate-900">{f.nome}</p>
                  <p className="text-xs text-slate-500">{f.tipo_nome} · {f.documentos} documento(s)</p>
                </div>
                <div className="flex items-center gap-1" aria-label={`Confiabilidade ${f.confiabilidade} de 5`}>
                  {[1, 2, 3, 4, 5].map((n) => (
                    <span key={n} className={`h-2 w-5 rounded-sm ${n <= f.confiabilidade ? "bg-acao" : "bg-slate-200"}`} />
                  ))}
                </div>
                <div className="min-w-0 space-y-2">
                  <p className="text-sm text-slate-600">
                    {f.observacoes}
                    {f.url && <> <a href={f.url} target="_blank" rel="noreferrer" className="text-acao hover:underline">origem</a></>}
                  </p>
                  {f.capturas.length > 0 && (
                    <ul className="space-y-2" aria-label={`Capturas de ${f.nome}`}>
                      {f.capturas.map((c) => (
                        <LinhaCaptura key={c.id} c={c} disparando={disparando === c.id} onColetar={() => coletar(c)} />
                      ))}
                    </ul>
                  )}
                </div>
              </li>
            ))}
          </ul>
        )}
      </Cartao>
    </>
  );
}

function LinhaCaptura({ c, disparando, onColetar }: { c: Captura; disparando: boolean; onColetar: () => void }) {
  const Icone = ICONE_CAPTURA[c.tipo] ?? Globe;
  return (
    <li className="rounded-md border border-borda bg-slate-50/60 px-3 py-2">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 space-y-1">
          <p className="flex items-start gap-1.5 text-sm font-medium text-slate-800">
            <Icone size={14} className="mt-0.5 shrink-0 text-slate-500" aria-hidden />
            <span>{c.nome}</span>
          </p>
          <div className="flex flex-wrap items-center gap-2 text-xs text-slate-600">
            <Selo tom={c.ativa ? "leitura" : "info"}>{c.ativa ? "coleta agendada" : "sob demanda"}</Selo>
            {c.ultima_coleta && <UltimaColeta c={c.ultima_coleta} />}
          </div>
        </div>
        <Botao onClick={onColetar} carregando={disparando} disabled={c.ultima_coleta?.situacao === "rodando"}>
          Coletar agora
        </Botao>
      </div>
      {c.onde && <p className="mt-1 truncate font-mono text-[11px] text-slate-500" title={c.onde}>{c.onde}</p>}
    </li>
  );
}

function UltimaColeta({ c }: { c: ColetaResumo }) {
  return (
    <>
      <Selo tom={TOM_COLETA[c.situacao]}>{c.situacao_nome}</Selo>
      <span>
        {dataHora(c.iniciada_em)}
        {c.situacao !== "rodando" && (
          <> · {num(c.encontrados)} encontrados, {num(c.novos)} novos, {num(c.conhecidos)} já no acervo, {num(c.sem_mudanca)} sem mudança
            {c.bloqueados > 0 && <>, {num(c.bloqueados)} bloqueados</>}{c.erros > 0 && <>, {num(c.erros)} com erro</>}</>
        )}
      </span>
      {c.mensagem && <span className="basis-full text-slate-500">{c.mensagem}</span>}
    </>
  );
}
