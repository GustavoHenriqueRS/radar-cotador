// Grava o vídeo da demonstração seguindo docs/roteiro-demo.md, com legendas e um cursor visível.
// Precisa do protótipo no ar com o acervo de demonstração carregado e do playwright-core (npm).
// Uso: URL=http://localhost:8000/ SAIDA=pasta node scripts/gravar_video.cjs
const { chromium } = require(process.env.PLAYWRIGHT_CORE || "playwright-core");

const URL = process.env.URL || "http://localhost:8000/";
const SAIDA = process.env.SAIDA || "video";
const CHROME = process.env.CHROME || "/usr/bin/google-chrome";

const ESTILO = `
#legenda-video { position: fixed; left: 50%; bottom: 28px; transform: translateX(-50%); max-width: 1040px; z-index: 2147483646;
  background: rgba(15, 23, 42, .92); color: #fff; font: 500 21px/1.4 'Fira Sans', sans-serif; padding: 14px 22px; border-radius: 12px;
  box-shadow: 0 10px 30px rgba(0,0,0,.25); opacity: 0; transition: opacity .35s ease; text-align: center; pointer-events: none; }
#cursor-video { position: fixed; left: 0; top: 0; width: 22px; height: 22px; margin: -11px 0 0 -11px; border-radius: 50%; z-index: 2147483647;
  background: rgba(3, 105, 161, .35); border: 2px solid #0369a1; pointer-events: none; transition: width .12s, height .12s, margin .12s; }
#cursor-video.clique { width: 34px; height: 34px; margin: -17px 0 0 -17px; background: rgba(3, 105, 161, .55); }
#cartao-video { position: fixed; inset: 0; z-index: 2147483645; background: #0f172a; color: #e2e8f0; display: flex; flex-direction: column;
  align-items: center; justify-content: center; gap: 14px; font-family: 'Fira Sans', sans-serif; opacity: 0; transition: opacity .5s ease; pointer-events: none; }
#cartao-video h1 { font-size: 46px; font-weight: 600; color: #fff; margin: 0; }
#cartao-video p { font-size: 22px; margin: 0; color: #cbd5e1; }
#cartao-video small { font-size: 18px; color: #7dd3fc; }
`;

(async () => {
  const browser = await chromium.launch({ executablePath: CHROME, headless: true });
  const context = await browser.newContext({ viewport: { width: 1280, height: 720 }, recordVideo: { dir: SAIDA, size: { width: 1280, height: 720 } } });
  const page = await context.newPage();
  await page.addInitScript((estilo) => {
    window.addEventListener("DOMContentLoaded", () => {
      const s = document.createElement("style");
      s.textContent = estilo;
      document.head.appendChild(s);
      for (const id of ["legenda-video", "cursor-video", "cartao-video"]) {
        const el = document.createElement("div");
        el.id = id;
        document.body.appendChild(el);
      }
      document.addEventListener("mousemove", (e) => {
        document.getElementById("cursor-video").style.transform = `translate(${e.clientX}px, ${e.clientY}px)`;
      }, true);
    });
  }, ESTILO);

  const espera = (ms) => page.waitForTimeout(ms);
  const legenda = async (texto, ms) => {
    await page.evaluate((t) => {
      const el = document.getElementById("legenda-video");
      el.textContent = t;
      el.style.opacity = t ? "1" : "0";
    }, texto);
    if (ms) await espera(ms);
  };
  const cartao = async (html, ms) => {
    await page.evaluate((h) => {
      const el = document.getElementById("cartao-video");
      el.innerHTML = h;
      el.style.opacity = h ? "1" : "0";
    }, html);
    if (ms) await espera(ms);
  };
  const apontar = async (alvo) => {
    await alvo.scrollIntoViewIfNeeded();
    const caixa = await alvo.boundingBox();
    await page.mouse.move(caixa.x + caixa.width / 2, caixa.y + caixa.height / 2, { steps: 28 });
  };
  const clicar = async (alvo) => {
    await apontar(alvo);
    await page.evaluate(() => document.getElementById("cursor-video").classList.add("clique"));
    await alvo.click();
    await espera(160);
    await page.evaluate(() => document.getElementById("cursor-video").classList.remove("clique"));
  };
  const menu = (nome) => clicar(page.getByRole("navigation", { name: "Principal" }).getByRole("link", { name: nome, exact: true }));
  const rolarAte = async (alvo) => {
    await alvo.scrollIntoViewIfNeeded();
    await page.evaluate(() => window.scrollBy({ top: -120 }));
  };

  await page.goto(URL, { waitUntil: "networkidle" });
  await page.mouse.move(640, 360);
  await cartao("<h1>Radar do Cotador</h1><p>O protótipo em pouco mais de um minuto</p>", 3200);
  await cartao("", 600);

  await legenda("Painel: 6.892 preços lidos de PDFs reais. 86% passaram sem revisão humana, e o que falta está apontado.", 5200);
  const operadoras = page.getByText("Operadoras do Cotador").first();
  await apontar(operadoras);
  await rolarAte(operadoras);
  await legenda("As 9 operadoras da página do Cotador, conferidas no cadastro da ANS. A Saúde Sim teve o registro cancelado em 2022.", 5600);
  await page.evaluate(() => window.scrollTo({ top: 0 }));

  await menu("Documentos");
  await legenda("Cada PDF é lido duas vezes, de jeitos independentes, e guardado como prova da origem.", 3600);
  await clicar(page.getByRole("link", { name: /^unimed_guarulhos_pme_2026\.pdf/ }).first());
  await page.waitForLoadState("networkidle");
  await espera(800);
  await legenda("Unimed Guarulhos: cada preço aparece no lugar exato de onde saiu. Verde quer dizer que as leituras concordam.", 5200);
  const celula = page.locator('button[aria-label*="116,56"]').first();
  await clicar(celula);
  await legenda("Um só preço para revisar: R$ 116,56, abaixo do piso da nota técnica que a própria operadora registrou na ANS (R$ 122,77).", 6400);

  await menu("Documentos");
  await clicar(page.getByRole("link", { name: /ESCANEADA/ }).first());
  await page.waitForLoadState("networkidle");
  await espera(800);
  await legenda("O mesmo PDF escaneado, torto e sujo de propósito: o OCR leu 352 de 360 preços, sem nenhum errado.", 5600);

  await menu("Radar");
  await legenda("Radar: o que mudou aparece sozinho, sem ninguém procurar.", 3400);
  const mogiano = page.getByText(/Mogiano/).first();
  await rolarAte(mogiano);
  await apontar(mogiano);
  await legenda("Rede: a ANS deferiu a saída do Hospital Mogiano da rede de 9 planos publicados. Nenhum PDF de venda conta isso.", 6000);
  await page.evaluate(() => window.scrollTo({ top: 0 }));

  await menu("Cotação");
  await clicar(page.getByRole("button", { name: "Cotar" }));
  await espera(900);
  await legenda("Cotação para 38, 36 e 9 anos. A mais barata vem de material de 2025: outras duas fontes têm o mesmo produto 10,7% mais caro.", 6800);
  await clicar(page.locator("select").nth(1));
  await page.locator("select").nth(1).selectOption("RN");
  await clicar(page.getByRole("button", { name: "Cotar" }));
  await espera(900);
  const natal = page.getByText(/Natal Hospital Center/).first();
  await rolarAte(natal);
  await apontar(natal);
  await legenda("Com a UF do cliente, entram a rede hospitalar do plano no estado e o aviso de hospital saindo da rede, com a data.", 6400);
  await page.evaluate(() => window.scrollTo({ top: 0 }));

  await menu("Fontes");
  await legenda("Fontes: cada uma com suas capturas. O robots.txt é obedecido e só o que mudou é baixado.", 5200);
  await legenda("", 300);

  await cartao("<h1>Radar do Cotador</h1><p>Código e documentação: <small>github.com/GustavoHenriqueRS/radar-cotador</small></p>"
    + "<p>Protótipo no navegador: <small>gustavohenriquers.github.io/radar-cotador</small></p>", 5200);

  const video = page.video();
  await context.close();
  await browser.close();
  console.log(await video.path());
})();
