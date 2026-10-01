import type { ReactNode } from "react";
import { Link } from "react-router-dom";
import {
  Activity, ArrowRight, BookOpen, Calculator, CircleAlert, CirclePlay, FileText, FolderGit2, Hospital, Layers, Radar, Scale, ScanLine, ShieldCheck,
} from "lucide-react";
import arquitetura from "../../../docs/img/arquitetura.svg?url";
import { GradeAnimada } from "../components/GradeAnimada";
import { ESTATICO } from "../estatico";
import { CAPA_VIDEO, REPOSITORIO, VIDEO, pdf } from "../links";

const NUMEROS = [
  { valor: "81,1%", texto: "dos preços passam sem revisão humana, nos produtos que o PDF identifica pelo registro ANS" },
  { valor: "137", texto: "tabelas que o leitor nunca tinha visto, em dois testes às cegas, sem nenhuma divergência entre as leituras" },
  { valor: "9 de 9", texto: "operadoras da página do Cotador mapeadas uma a uma, com o canal por onde o preço chega" },
  { valor: "US$ 0,001", texto: "por página, o custo da segunda leitura; o acervo inteiro custou US$ 0,35" },
];

const RECURSOS = [
  { Icone: ScanLine, titulo: "Duas leituras independentes", para: "/documentos/19", texto: "Uma geométrica (ou OCR) e outra por modelo de linguagem. Quando discordam, a célula vai para uma pessoa, com o PDF ao lado." },
  { Icone: Calculator, titulo: "Conferência por cálculo", para: "/documentos/23", texto: "O percentual entre as faixas etárias refaz cada preço. Em 1.434 erros de digitação plantados de propósito, apontou todos os acima de 0,1%." },
  { Icone: Scale, titulo: "Regras com base legal", para: "/documentos/19", texto: "RN 563 para as faixas, RN 564 para o preço de referência da nota técnica e RN 543 para a situação do plano na ANS." },
  { Icone: Layers, titulo: "Origem e histórico", para: "/tabelas", texto: "Todo preço publicado sabe de onde veio. Nada é sobrescrito, e material antigo nunca volta a ser o preço vigente." },
  { Icone: Radar, titulo: "Radar de mudanças", para: "/radar", texto: "Nota técnica nova, plano suspenso, hospital saindo da rede: o aviso chega antes de o corretor errar." },
  { Icone: Hospital, titulo: "Cotação com contexto", para: "/cotacao", texto: "Rede hospitalar no estado do cliente, reembolso do registro ANS e alerta quando outra fonte tem material mais novo." },
];

const ACHADOS = [
  { titulo: "Operadora extinta na lista", para: "/", texto: "A Saúde Sim teve o registro cancelado em 2022 e ainda aparecia na página do Cotador." },
  { titulo: "Plano suspenso à venda", para: "/radar", texto: "Planos com venda suspensa na ANS desde 11/2024 ainda estavam numa tabela de venda de 2026." },
  { titulo: "Preço velho mais barato", para: "/cotacao", texto: "A mesma tabela Hapvida DF estava 9,7% mais barata numa das fontes, porque era a versão de 2025." },
  { titulo: "Hospital fora da rede", para: "/radar", texto: "A ANS deferiu a saída do Hospital Mogiano da rede de 9 planos publicados. Nenhum PDF de venda conta isso." },
];

const DOCUMENTOS = [
  { nome: "proposta", titulo: "Proposta", texto: "Os cinco pontos do desafio e os problemas resolvidos no caminho." },
  { nome: "slides", titulo: "Slides", texto: "A proposta em 12 slides, para apresentar em poucos minutos." },
  { nome: "detalhes-tecnicos", titulo: "Detalhes técnicos", texto: "As medições, as regras e as tabelas por trás de cada número." },
  { nome: "como-evoluir", titulo: "Como evoluir", texto: "Princípios, receitas de extensão, escala e próximos passos." },
  { nome: "operadoras", titulo: "As 9 operadoras", texto: "Canais, robots.txt, termos de uso e amostras lidas, uma a uma." },
  { nome: "pesquisa", titulo: "Pesquisa", texto: "Fontes de dados, achados e embasamento regulatório." },
  { nome: "roteiro-demo", titulo: "Roteiro da demonstração", texto: "O protótipo em cinco minutos, tela a tela." },
];

function VerNoPrototipo({ para }: { para: string }) {
  return (
    <Link to={para} className="mt-auto inline-flex min-h-8 items-center gap-1 self-start pt-2 text-sm font-medium text-acao hover:underline">
      Ver no protótipo <ArrowRight size={14} aria-hidden />
    </Link>
  );
}

function Secao({ id, rotulo, titulo, children }: { id?: string; rotulo: string; titulo: string; children: ReactNode }) {
  return (
    <section id={id} className="mx-auto max-w-6xl px-4 py-16 sm:px-6 sm:py-20">
      <p className="font-mono text-xs uppercase tracking-widest text-acao">{rotulo}</p>
      <h2 className="mt-2 max-w-2xl text-balance text-2xl font-semibold tracking-tight text-slate-900 sm:text-3xl">{titulo}</h2>
      <div className="mt-8">{children}</div>
    </section>
  );
}

export function Apresentacao() {
  return (
    <div className="min-h-dvh bg-fundo">
      <header className="relative overflow-hidden bg-marinho text-slate-300">
        <GradeAnimada className="text-sky-300 [mask-image:radial-gradient(700px_circle_at_50%_40%,white,transparent)]" />
        <div className="relative mx-auto max-w-6xl px-4 pb-20 pt-6 sm:px-6 sm:pb-28">
          <nav aria-label="Apresentação" className="flex items-center justify-between gap-4">
            <span className="flex items-center gap-2 text-sm font-semibold text-white">
              <span className="grid size-8 place-items-center rounded-md bg-acao"><Activity size={18} aria-hidden /></span>
              Radar do Cotador
            </span>
            <a href={REPOSITORIO} className="flex min-h-10 items-center gap-1.5 rounded-md px-3 text-sm text-slate-300 transition-colors duration-150 hover:bg-marinho-2 hover:text-white">
              <FolderGit2 size={16} aria-hidden /> Código no GitHub
            </a>
          </nav>
          <div className="mx-auto mt-16 max-w-3xl text-center sm:mt-24">
            <p className="inline-flex items-center gap-2 rounded-full border border-slate-700 bg-marinho-2/70 px-3 py-1 text-xs font-medium text-sky-200">
              Desafio técnico · Cotador de Planos de Saúde
            </p>
            <h1 className="mt-6 text-balance text-4xl font-semibold tracking-tight text-white sm:text-6xl">
              Tabelas de preço que se conferem sozinhas
            </h1>
            <p className="mx-auto mt-6 max-w-2xl text-pretty text-lg leading-relaxed text-slate-300 sm:text-xl">
              O material é buscado onde é publicado, lido duas vezes, conferido contra os dados abertos da ANS e publicado com a origem de cada número.
              Uma pessoa só olha o que não fecha.
            </p>
            <div className="mt-10 flex flex-wrap items-center justify-center gap-3">
              <Link to="/" className="inline-flex min-h-12 items-center gap-2 rounded-full bg-acao px-6 text-base font-medium text-white transition-colors duration-150 hover:bg-acao-escura">
                Abrir o protótipo <ArrowRight size={18} aria-hidden />
              </Link>
              <a href="#video" onClick={(e) => { e.preventDefault(); document.getElementById("video")?.scrollIntoView({ behavior: "smooth" }); }}
                className="inline-flex min-h-12 items-center gap-2 rounded-full border border-slate-600 px-6 text-base font-medium text-white transition-colors duration-150 hover:bg-marinho-2">
                <CirclePlay size={18} aria-hidden /> Ver o vídeo
              </a>
              <a href={pdf("proposta")} className="inline-flex min-h-12 items-center gap-2 rounded-full border border-slate-600 px-6 text-base font-medium text-white transition-colors duration-150 hover:bg-marinho-2">
                <FileText size={18} aria-hidden /> Ler a proposta
              </a>
            </div>
            {ESTATICO && (
              <p className="mx-auto mt-6 max-w-xl text-sm text-slate-400">
                Esta é a versão estática: o acervo de demonstração como estava em {import.meta.env.VITE_DEMO_DATA ?? "sua exportação"}, com a cotação calculada no próprio navegador.
              </p>
            )}
          </div>
        </div>
      </header>

      <section aria-label="Resultados" className="relative z-10 mx-auto -mt-10 max-w-6xl px-4 sm:px-6">
        <div className="grid overflow-hidden rounded-2xl border border-borda bg-white shadow-sm sm:grid-cols-2 lg:grid-cols-4">
          {NUMEROS.map((n) => (
            <p key={n.valor} className="-m-px border-l border-t border-borda p-6 sm:p-8">
              <span className="num block text-4xl font-semibold tracking-tight text-marinho">{n.valor}</span>
              <span className="mt-3 block text-sm leading-relaxed text-slate-600">{n.texto}</span>
            </p>
          ))}
        </div>
      </section>

      <Secao id="video" rotulo="Demonstração" titulo="O protótipo em um minuto e meio">
        <video controls preload="metadata" poster={CAPA_VIDEO} className="aspect-video w-full rounded-2xl border border-borda bg-marinho shadow-sm">
          <source src={VIDEO} type="video/mp4" />
          <a href={VIDEO}>Baixar o vídeo da demonstração</a>
        </video>
      </Secao>

      <Secao rotulo="Como funciona" titulo="Do PDF da operadora à cotação do corretor, com a ANS por baixo de tudo">
        <figure className="overflow-x-auto rounded-2xl border border-borda bg-white p-4 shadow-sm sm:p-8">
          <img src={arquitetura} width={1000} height={452} alt="Fluxo do Radar do Cotador: fontes, coleta, PDF guardado, duas leituras, conferência, revisão, versão publicada e cotação, com os dados abertos da ANS na base da conferência e dos avisos." className="h-auto w-full min-w-[680px]" />
        </figure>
      </Secao>

      <Secao rotulo="O que já funciona" titulo="Seis peças que tiram a digitação sem perder o controle">
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {RECURSOS.map(({ Icone, titulo, para, texto }) => (
            <div key={titulo} className="flex flex-col gap-4 rounded-2xl border border-borda bg-white p-6 shadow-sm">
              <span className="grid size-10 place-items-center rounded-xl border border-borda bg-sky-50 text-acao"><Icone size={20} strokeWidth={1.75} aria-hidden /></span>
              <div>
                <h3 className="text-base font-semibold text-slate-900">{titulo}</h3>
                <p className="mt-1.5 text-pretty text-sm leading-relaxed text-slate-600">{texto}</p>
              </div>
              <VerNoPrototipo para={para} />
            </div>
          ))}
        </div>
      </Secao>

      <Secao rotulo="Nos dados reais" titulo="Problemas que estavam passando e que o radar encontrou">
        <div className="grid gap-4 sm:grid-cols-2">
          {ACHADOS.map((a) => (
            <div key={a.titulo} className="flex gap-4 rounded-2xl border border-amber-200 bg-amber-50/60 p-6">
              <CircleAlert size={22} className="mt-0.5 shrink-0 text-revisar" aria-hidden />
              <div>
                <h3 className="text-base font-semibold text-slate-900">{a.titulo}</h3>
                <p className="mt-1 text-pretty text-sm leading-relaxed text-slate-700">{a.texto}</p>
                <VerNoPrototipo para={a.para} />
              </div>
            </div>
          ))}
        </div>
      </Secao>

      <Secao rotulo="Para ler" titulo="Os documentos, em PDF">
        <ul className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {DOCUMENTOS.map((d) => (
            <li key={d.nome}>
              <a href={pdf(d.nome)} className="group flex h-full gap-3 rounded-2xl border border-borda bg-white p-5 shadow-sm transition-colors duration-150 hover:border-acao">
                <BookOpen size={20} className="mt-0.5 shrink-0 text-acao" aria-hidden />
                <span>
                  <span className="block text-base font-semibold text-slate-900 group-hover:text-acao">{d.titulo}</span>
                  <span className="mt-1 block text-sm leading-relaxed text-slate-600">{d.texto}</span>
                </span>
              </a>
            </li>
          ))}
        </ul>
        <p className="mt-6 flex items-center gap-2 text-sm text-slate-600">
          <ShieldCheck size={16} className="shrink-0 text-ok" aria-hidden />
          Os números se refazem com os scripts e os testes do repositório, e o mesmo PDF dá sempre o mesmo resultado.
        </p>
      </Secao>

      <footer className="border-t border-borda bg-white">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-4 px-4 py-8 text-sm text-slate-600 sm:px-6">
          <p><span className="font-semibold text-slate-900">Gustavo Henrique</span> · desafio técnico do Cotador de Planos de Saúde · outubro de 2026</p>
          <div className="flex flex-wrap gap-4">
            <Link to="/" className="font-medium text-acao hover:underline">Abrir o protótipo</Link>
            <a href={REPOSITORIO} className="font-medium text-acao hover:underline">Código no GitHub</a>
          </div>
        </div>
      </footer>
    </div>
  );
}
