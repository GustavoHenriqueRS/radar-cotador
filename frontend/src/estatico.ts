import type { AtributosAns, MudancaRede, ResultadoCotacao, ResumoRede, Tabela } from "./api";

/**
 * Versão estática do protótipo, publicada no GitHub Pages: as telas leem o acervo de demonstração exportado por
 * `manage.py exportar_demo`, e a cotação roda no navegador com a mesma conta de `servicos.cotar`.
 */
export const ESTATICO = import.meta.env.VITE_DEMO_ESTATICA === "1";

const BASE = `${import.meta.env.BASE_URL}demo/`;

export const AVISO_ACAO =
  "Nesta versão estática, revisar, publicar, coletar e enviar PDF ficam desligados. Para usar, rode o protótipo com docker compose up.";

export const urlPagina = (documentoId: number, pagina: number) =>
  ESTATICO ? `${BASE}paginas/${documentoId}/${pagina}.webp` : `/api/documentos/${documentoId}/pagina/${pagina}.png`;

export const urlPdf = (documentoId: number) =>
  ESTATICO ? `${BASE}pdfs/${documentoId}.pdf` : `/api/documentos/${documentoId}/pdf?baixar=1`;

async function lerJson<T>(arquivo: string): Promise<T> {
  const r = await fetch(BASE + arquivo);
  if (!r.ok) throw new Error(`Esta tela não faz parte da versão estática (${arquivo}).`);
  return r.json();
}

export async function pedirEstatico<T>(caminho: string, init?: RequestInit): Promise<T> {
  if ((init?.method ?? "GET") !== "GET") {
    if (caminho !== "cotacao") throw new Error(AVISO_ACAO);
    const corpo = JSON.parse(String(init?.body ?? "{}"));
    return (await cotarNoNavegador(corpo.idades ?? [], corpo.tipo ?? "", String(corpo.uf ?? "").toUpperCase())) as T;
  }
  const [rota, consulta = ""] = caminho.split("?");
  const params = new URLSearchParams(consulta);
  if (rota === "documentos" && params.get("status") === "em_revisao") return lerJson<T>("api/documentos_em_revisao.json");
  const q = params.get("q");
  if (rota === "tabelas" && q) return filtrarTabelas(await lerJson<Tabela[]>("api/tabelas.json"), q) as T;
  return lerJson<T>(`api/${rota}.json`);
}

/** A busca de `api.tabelas`: nome do plano, operadora ou dígitos do registro ANS. */
function filtrarTabelas(tabelas: Tabela[], q: string): Tabela[] {
  const termo = q.toLowerCase();
  const digitos = q.replace(/\D/g, "");
  return tabelas
    .filter((t) => t.plano.toLowerCase().includes(termo) || t.operadora.toLowerCase().includes(termo)
      || (digitos !== "" && t.registro_ans.replace(/\D/g, "").includes(digitos)))
    .slice(0, 500);
}

interface TabelaCotacao {
  tabela_id: number;
  registro: string;
  registro_ans: string;
  plano: string;
  operadora: string;
  fonte: string;
  condicao: string;
  tipo_contratacao: string;
  precos: Record<string, number>;
  vigencia_inicio: string | null;
  vigencia_fim: string | null;
  versao: number;
  documento: string;
  documento_id: number;
  referencia: string;
  dupla_leitura: boolean;
  data_material: string | null;
  mesmas: number[];
}

interface BaseCotacao {
  faixas: string[];
  tabelas: TabelaCotacao[];
  registros: Record<string, { ans: AtributosAns | null; rede: ResumoRede | null; mudancas: Record<string, MudancaRede[]> }>;
}

let base: Promise<BaseCotacao> | null = null;
const LIMITES = [18, 23, 28, 33, 38, 43, 48, 53, 58];
const centavos = (v: number) => Math.round(v * 100) / 100;

async function cotarNoNavegador(idadesInformadas: unknown[], tipo: string, uf: string): Promise<ResultadoCotacao[]> {
  const idades = idadesInformadas.map(Number);
  if (idades.some((i) => !Number.isInteger(i))) throw new Error("idades inválidas");
  if (!idades.length || idades.some((i) => i < 0 || i > 120)) throw new Error("informe as idades dos beneficiários");
  if (uf && !/^[A-Z]{2}$/.test(uf)) throw new Error("UF inválida");

  base ??= lerJson<BaseCotacao>("cotacao.json");
  const { faixas: FAIXAS, tabelas, registros } = await base;
  const faixaDa = (idade: number) => {
    const i = LIMITES.findIndex((limite) => idade <= limite);
    return FAIXAS[i === -1 ? FAIXAS.length - 1 : i];
  };
  const faixas = idades.map(faixaDa);
  const porId = new Map(tabelas.map((t) => [t.tabela_id, t]));
  const cobre = (t: TabelaCotacao) => faixas.every((f) => f in t.precos);
  const soma = (t: TabelaCotacao) => faixas.reduce((total, f) => total + t.precos[f], 0);
  const agora = Date.now();

  return tabelas
    .filter((t) => (!tipo || (t.tipo_contratacao || "").toLowerCase().includes(tipo.toLowerCase())) && cobre(t))
    .map((t): ResultadoCotacao => {
      const total = soma(t);
      const registro = registros[t.registro];
      return {
        tabela_id: t.tabela_id, registro_ans: t.registro_ans, plano: t.plano, operadora: t.operadora, fonte: t.fonte,
        condicao: t.condicao, tipo_contratacao: t.tipo_contratacao, total: centavos(total),
        por_pessoa: idades.map((idade, i) => ({ idade, faixa: faixas[i], valor: t.precos[faixas[i]] })),
        vigencia_inicio: t.vigencia_inicio, vigencia_fim: t.vigencia_fim, versao: t.versao,
        documento: t.documento, documento_id: t.documento_id,
        dias_desde_confirmacao: Math.floor((agora - Date.parse(t.referencia.replace(" ", "T"))) / 86_400_000),
        dupla_leitura: t.dupla_leitura, data_material: t.data_material,
        divergencias: t.mesmas
          .map((id) => porId.get(id))
          .filter((outra): outra is TabelaCotacao => !!outra && cobre(outra) && Math.abs(soma(outra) - total) >= 0.01)
          .map((outra) => ({
            fonte: outra.fonte, total: centavos(soma(outra)), diferenca: soma(outra) / total - 1, data_material: outra.data_material,
            outra_mais_recente: (outra.data_material ?? "") > (t.data_material ?? ""),
          })),
        ans: registro?.ans ?? null,
        rede: registro?.rede ?? null,
        rede_na_uf: uf && registro?.rede ? registro.rede.por_uf[uf] ?? null : null,
        mudancas_de_rede: registro?.mudancas[uf] ?? [],
      };
    })
    .sort((a, b) => a.total - b.total);
}
