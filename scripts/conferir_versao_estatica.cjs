// Confere que a versão estática cota igual ao protótipo: para cada combinação de idade, contratação e UF,
// o texto de cada cartão do resultado tem de sair idêntico nas duas versões.
// Precisa das duas no ar e do playwright-core (npm).
// Uso: ESTATICO=http://localhost:8765/radar-cotador/ REAL=http://localhost:8000/ node scripts/conferir_versao_estatica.cjs
const { chromium } = require(process.env.PLAYWRIGHT_CORE || "playwright-core");

const ESTATICO = (process.env.ESTATICO || "http://localhost:8765/radar-cotador/") + "#/cotacao";
const REAL = (process.env.REAL || "http://localhost:8000/") + "cotacao";
const CHROME = process.env.CHROME || "/usr/bin/google-chrome";

const CASOS = [
  ["38, 36, 9", "", ""],
  ["38, 36, 9", "", "RN"],
  ["25", "adesão", "SP"],
  ["0, 18, 59, 70", "empresarial", "DF"],
  ["44", "", "MG"],
  ["30, 30", "", "BA"],
  ["19, 24, 29, 34, 39, 49, 54", "", "CE"],
  ["120", "", ""],
];

async function cotar(page, url, [idades, tipo, uf]) {
  await page.goto(url, { waitUntil: "networkidle" });
  await page.locator('input[inputmode="numeric"]').fill(idades);
  await page.locator("select").nth(0).selectOption(tipo);
  await page.locator("select").nth(1).selectOption(uf);
  await page.getByRole("button", { name: "Cotar" }).click();
  await page.waitForFunction(() => document.querySelector("main ol > li") || /Nenhuma tabela/.test(document.querySelector("main").innerText), null, { timeout: 15000 });
  await page.waitForTimeout(400);
  return page.locator("main ol > li").allInnerTexts();
}

(async () => {
  const browser = await chromium.launch({ executablePath: CHROME, headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  let divergentes = 0;
  for (const caso of CASOS) {
    const a = await cotar(page, ESTATICO, caso);
    const b = await cotar(page, REAL, caso);
    const iguais = a.length === b.length && a.every((t, i) => t === b[i]);
    console.log(`${JSON.stringify(caso)}: ${a.length} x ${b.length} cartões -> ${iguais ? "iguais" : "DIFERENTES"}`);
    if (!iguais) {
      divergentes++;
      const i = a.findIndex((t, j) => t !== b[j]);
      console.log("  primeiro cartão diferente:", i, "\n  estático:", JSON.stringify(a[i]).slice(0, 400), "\n  real:    ", JSON.stringify(b[i]).slice(0, 400));
    }
  }
  console.log(divergentes ? `${divergentes} caso(s) com diferença` : "todas as cotações iguais nas duas versões");
  await browser.close();
  process.exitCode = divergentes ? 1 : 0;
})();
