import { ESTATICO, pedirEstatico } from "./estatico";

export type Severidade = "erro" | "alerta" | "info";

export interface Achado {
  regra: string;
  severidade: Severidade;
  mensagem: string;
  faixas: string[];
}

export interface Evento {
  id: number;
  tipo: string;
  tipo_nome: string;
  severidade: Severidade;
  titulo: string;
  registro_ans: string;
  operadora: string;
  documento_id: number | null;
  documento: string | null;
  criado_em: string;
  data_efeito: string | null;
  detalhe: Record<string, unknown>;
}

export interface ResumoLeitura {
  celulas: number;
  confirmado: number;
  confirmado_calculo: number;
  divergente: number;
  so_geometrico: number;
  so_llm: number;
  revisar: number;
  erros: number;
  alertas: number;
  colunas: number;
  colunas_com_registro_ans: number;
}

export interface DocumentoResumo {
  id: number;
  nome: string;
  serie: string;
  fonte: string | null;
  status: "processando" | "em_revisao" | "publicado" | "historico" | "descartado" | "erro";
  recebido_em: string;
  paginas: number;
  ocr: boolean;
  leitura_llm: "nenhuma" | "ao_vivo" | "gravada" | "falhou";
  custo_llm_usd: string | null;
  operadora: string;
  administradora: string;
  tipo_contratacao: string;
  vigencia_inicio: string | null;
  vigencia_fim: string | null;
  resumo: Partial<ResumoLeitura>;
  erro: string;
}

export interface Celula {
  id: number;
  faixa: string;
  geometrico: string | null;
  llm: string | null;
  calculado: string | null;
  valor: string | null;
  status: "confirmado" | "confirmado_calculo" | "divergente" | "so_geometrico" | "so_llm";
  caixa: [number, number, number, number] | null;
  revisar: boolean;
  corrigida: boolean;
}

export interface Coluna {
  id: number;
  ordem: number;
  pagina: number;
  tabela: string;
  coluna: string;
  ocorrencia: number;
  registro_ans: string;
  plano_ans: {
    nome: string;
    operadora: string;
    situacao: string;
    contratacao: string;
    acomodacao: string;
    fator_moderador: string;
    abrangencia: string;
  } | null;
  achados: Achado[];
  status: "pendente" | "aprovada" | "ignorada";
  publicavel: boolean;
  celulas: Celula[];
}

export interface DocumentoDetalhe extends DocumentoResumo {
  tamanhos_paginas: [number, number][];
  colunas: Coluna[];
  url_origem: string;
  achados_documento: Achado[];
  extra_llm: {
    avisos?: string[];
    carencias?: { cobertura: string; prazo_dias: number | null; observacao: string | null }[];
    coparticipacao?: { procedimento: string; regra: string }[];
    elegibilidade?: string[];
    falha?: string;
  };
  eventos: Evento[];
}

export interface Painel {
  documentos: number;
  documentos_por_status: Record<string, number>;
  precos_lidos: number;
  precos_confirmados_dupla_leitura: number;
  precos_sem_revisao: number;
  precos_revisar: number;
  precos_sem_produto: number;
  precos_com_produto: number;
  precos_com_produto_sem_revisao: number;
  tabelas_ativas: number;
  operadoras_com_tabela: number;
  tabelas_vencidas: number;
  custo_llm_usd: number;
  eventos_abertos: number;
  eventos: Evento[];
}

export interface Tabela {
  id: number;
  registro_ans: string;
  ocorrencia: number;
  condicao: string;
  marcas_condicao: string[];
  cadeia?: number;
  plano: string;
  operadora: string;
  administradora: string;
  tipo_contratacao: string;
  fonte: string | null;
  documento_id: number;
  documento: string;
  precos: Record<string, number>;
  vigencia_inicio: string | null;
  vigencia_fim: string | null;
  versao: number;
  publicada_em: string;
  confirmada_em: string | null;
  ativa: boolean;
  dias_desde_confirmacao: number;
  data_material: string | null;
  ans: AtributosAns | null;
  rede: ResumoRede | null;
}

/** O que o registro do produto na ANS diz (pda-008): o material de venda é conferido contra isso. */
export interface AtributosAns {
  reembolso: string;
  coparticipacao: string;
  acomodacao: string;
  abrangencia: string;
  segmentacao: string;
  situacao: string;
}

export interface ResumoRede {
  hospitais: number;
  por_uf: Record<string, { hospitais: number; urgencia: number }>;
}

export interface MudancaRede {
  protocolo: string;
  tipo: string;
  motivo: string;
  plano: string;
  solicitada_em: string;
  vale_em: string;
  excluidos: string[];
  incluidos: string[];
}

export interface Hospital {
  cnes: string;
  estabelecimento: string;
  classe: string;
  urgencia: number;
  municipio: string;
  uf: string;
  contrato: string;
  disponibilidade: string;
}

export interface RedeDaTabela {
  registro_ans: string;
  plano: string;
  atualizado_em: string;
  resumo: ResumoRede;
  hospitais: Hospital[];
  mudancas: MudancaRede[];
  fonte: string;
}

export interface OperadoraSaude {
  registro_ans: string;
  nome: string;
  ativa: boolean;
  cancelada_em: string | null;
  motivo_cancelamento: string;
  tabelas_ativas: number;
  canal: string;
}

export interface ColetaResumo {
  id: number;
  situacao: "rodando" | "ok" | "bloqueada" | "erro";
  situacao_nome: string;
  iniciada_em: string;
  terminada_em: string | null;
  encontrados: number;
  novos: number;
  conhecidos: number;
  sem_mudanca: number;
  bloqueados: number;
  erros: number;
  mensagem: string;
}

export interface Fonte {
  id: number;
  nome: string;
  tipo: string;
  tipo_nome: string;
  url: string;
  confiabilidade: number;
  observacoes: string;
  documentos: number;
  capturas: Captura[];
}

export interface Captura {
  id: number;
  tipo: "pagina_publica" | "url_direta" | "wayback" | "caixa_email";
  tipo_nome: string;
  nome: string;
  onde: string;
  ativa: boolean;
  ultima_coleta: ColetaResumo | null;
}

export interface ResultadoPublicacao {
  publicadas: number;
  sem_mudanca: number;
  bloqueadas: number;
  retiradas: number;
  historico?: boolean;
  adiadas?: number;
  versao_mais_nova?: string;
}

export interface ResultadoCotacao {
  tabela_id: number;
  registro_ans: string;
  plano: string;
  operadora: string;
  fonte: string;
  condicao: string;
  tipo_contratacao: string;
  total: number;
  por_pessoa: { idade: number; faixa: string; valor: number }[];
  vigencia_inicio: string | null;
  vigencia_fim: string | null;
  versao: number;
  documento: string;
  documento_id: number;
  dias_desde_confirmacao: number;
  dupla_leitura: boolean;
  data_material: string | null;
  divergencias: { fonte: string; total: number; diferenca: number; data_material: string | null; outra_mais_recente: boolean }[];
  ans: AtributosAns | null;
  rede: ResumoRede | null;
  rede_na_uf: { hospitais: number; urgencia: number } | null;
  mudancas_de_rede: MudancaRede[];
}

async function pedir<T>(caminho: string, init?: RequestInit): Promise<T> {
  if (ESTATICO) return pedirEstatico<T>(caminho, init);
  const r = await fetch(`/api/${caminho}`, init);
  if (!r.ok) {
    const corpo = await r.json().catch(() => ({}));
    throw new Error(corpo.erro ?? `Erro ${r.status} em /api/${caminho}`);
  }
  return r.json();
}

export const get = <T,>(caminho: string) => pedir<T>(caminho);

export const post = <T,>(caminho: string, corpo: unknown = {}) =>
  pedir<T>(caminho, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(corpo) });

export const enviarArquivo = (arquivo: File) => {
  const dados = new FormData();
  dados.append("arquivo", arquivo);
  return pedir<{ id: number; novo: boolean }>("documentos", { method: "POST", body: dados });
};
