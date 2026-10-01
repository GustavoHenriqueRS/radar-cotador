const moeda = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" });
const inteiro = new Intl.NumberFormat("pt-BR");

export const brl = (v: number | string | null | undefined) =>
  v === null || v === undefined || v === "" ? "—" : moeda.format(Number(v));

export const num = (v: number | null | undefined) => (v === null || v === undefined ? "—" : inteiro.format(v));

export const pct = (v: number, casas = 1) =>
  `${v > 0 ? "+" : ""}${(v * 100).toLocaleString("pt-BR", { minimumFractionDigits: casas, maximumFractionDigits: casas })}%`;

export const data = (iso: string | null | undefined) => {
  if (!iso) return "—";
  const [a, m, d] = iso.slice(0, 10).split("-");
  return `${d}/${m}/${a}`;
};

export const dataHora = (iso: string) =>
  new Date(iso).toLocaleString("pt-BR", { day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit" });

export const haQuantoTempo = (dias: number) =>
  dias <= 0 ? "hoje" : dias === 1 ? "ontem" : dias < 30 ? `há ${dias} dias` : `há ${Math.round(dias / 30)} meses`;

export const FAIXAS = ["00-18", "19-23", "24-28", "29-33", "34-38", "39-43", "44-48", "49-53", "54-58", "59+"];
