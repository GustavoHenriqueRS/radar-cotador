import { useState } from "react";
import { Building2, ChevronDown, ChevronUp, Hospital as IconeHospital, Siren } from "lucide-react";
import { get, type AtributosAns, type MudancaRede, type RedeDaTabela, type ResumoRede } from "../api";
import { Carregando, Erro, Selo } from "./ui";
import { data, num } from "../formato";

/** Reembolso, coparticipação e acomodação como estão no registro do produto na ANS, não como o folheto diz. */
export function AtributosDoRegistro({ ans }: { ans: AtributosAns | null }) {
  if (!ans) return null;
  const itens = [
    ["Reembolso", ans.reembolso || "não informado"],
    ["Coparticipação ou franquia", ans.coparticipacao || "não informado"],
    ["Acomodação", ans.acomodacao || "não informado"],
    ["Abrangência", ans.abrangencia || "não informado"],
  ];
  return (
    <p className="mt-1.5 flex flex-wrap gap-x-3 gap-y-0.5 text-xs text-slate-600" aria-label="Registro do produto na ANS">
      <span className="font-medium text-slate-700">Registro na ANS:</span>
      {itens.map(([rotulo, valor]) => <span key={rotulo}>{rotulo}: <span className="text-slate-800">{valor}</span></span>)}
    </p>
  );
}

export function SeloRede({ rede, uf, naUf }: { rede: ResumoRede | null; uf?: string; naUf?: { hospitais: number; urgencia: number } | null }) {
  if (!rede) return null;
  if (uf) {
    return (
      <Selo tom={naUf?.hospitais ? "info" : "revisar"} icone={<IconeHospital size={12} aria-hidden />}>
        {naUf?.hospitais ? `rede ANS em ${uf}: ${num(naUf.hospitais)} hospitais, ${num(naUf.urgencia)} com pronto-socorro` : `nenhum hospital da rede em ${uf} na ANS`}
      </Selo>
    );
  }
  const ufs = Object.keys(rede.por_uf).length;
  const urgencia = Object.values(rede.por_uf).reduce((t, u) => t + u.urgencia, 0);
  return (
    <Selo tom={rede.hospitais ? "info" : "revisar"} icone={<IconeHospital size={12} aria-hidden />}>
      {rede.hospitais ? `rede ANS: ${num(rede.hospitais)} hospitais em ${ufs} UF(s), ${num(urgencia)} com pronto-socorro` : "rede hospitalar não informada à ANS"}
    </Selo>
  );
}

export function AvisosDeRede({ mudancas }: { mudancas: MudancaRede[] }) {
  if (!mudancas.length) return null;
  const hoje = new Date().toISOString().slice(0, 10);
  return (
    <>
      {mudancas.map((m) => (
        <p key={m.protocolo} role="note" className={`mt-2 flex items-start gap-1.5 rounded-md px-2.5 py-1.5 text-xs ${m.incluidos.length ? "bg-info-fundo text-info" : "bg-revisar-fundo text-revisar"}`}>
          <Building2 size={14} className="mt-px shrink-0" aria-hidden />
          <span>
            Rede: {m.excluidos.join(", ")} {m.vale_em >= hoje ? `sai em ${data(m.vale_em)}` : `saiu em ${data(m.vale_em)}`}
            {m.incluidos.length ? `, no lugar entra ${m.incluidos.join(", ")}` : ", sem substituto"} ({m.tipo.toLowerCase()} deferida pela ANS, protocolo {m.protocolo}).
          </span>
        </p>
      ))}
    </>
  );
}

/** Lista da rede hospitalar, buscada só quando o corretor abre. */
export function RedeDoPlano({ tabelaId, ufInicial = "" }: { tabelaId: number; ufInicial?: string }) {
  const [aberta, setAberta] = useState(false);
  const [rede, setRede] = useState<RedeDaTabela | null>(null);
  const [erro, setErro] = useState<string | null>(null);
  const [uf, setUf] = useState(ufInicial);

  async function alternar() {
    setAberta(!aberta);
    if (!rede && !aberta) {
      try {
        setRede(await get<RedeDaTabela>(`tabelas/${tabelaId}/rede`));
      } catch (e) {
        setErro((e as Error).message);
      }
    }
  }

  const hospitais = (rede?.hospitais ?? []).filter((h) => !uf || h.uf === uf);
  return (
    <div className="mt-2">
      <button type="button" onClick={alternar} aria-expanded={aberta}
        className="inline-flex min-h-8 cursor-pointer items-center gap-1 rounded-md px-2 text-xs font-medium text-acao hover:bg-sky-50">
        {aberta ? <ChevronUp size={14} aria-hidden /> : <ChevronDown size={14} aria-hidden />} Rede hospitalar (ANS)
      </button>
      {aberta && (
        <div className="mt-2 rounded-md border border-borda bg-slate-50/60 p-3">
          {erro && <Erro mensagem={erro} />}
          {!rede && !erro && <Carregando texto="Consultando a rede registrada na ANS…" />}
          {rede && (
            <>
              <div className="mb-2 flex flex-wrap items-center gap-2 text-xs text-slate-600">
                <label>
                  UF{" "}
                  <select value={uf} onChange={(e) => setUf(e.target.value)} className="min-h-8 rounded-md border border-borda bg-white px-2">
                    <option value="">todas</option>
                    {Object.entries(rede.resumo.por_uf).map(([sigla, r]) => <option key={sigla} value={sigla}>{sigla} ({r.hospitais})</option>)}
                  </select>
                </label>
                <span>{rede.fonte}; atualizado em {data(rede.atualizado_em.slice(0, 10))}.</span>
              </div>
              {hospitais.length === 0 ? <p className="text-xs text-slate-500">Nenhum hospital ativo registrado na ANS para este plano.</p> : (
                <ul className="max-h-72 divide-y divide-borda overflow-y-auto rounded-md border border-borda bg-white text-xs">
                  {hospitais.map((h) => (
                    <li key={h.cnes} className="flex items-center gap-2 px-2.5 py-1.5">
                      {h.urgencia ? <Siren size={13} className="shrink-0 text-erro" aria-label="com pronto-socorro" /> : <span className="w-[13px] shrink-0" />}
                      <span className="min-w-0 flex-1 truncate text-slate-800" title={h.estabelecimento}>{h.estabelecimento}</span>
                      <span className="shrink-0 text-slate-500">{h.municipio}/{h.uf}</span>
                    </li>
                  ))}
                </ul>
              )}
            </>
          )}
        </div>
      )}
    </div>
  );
}
