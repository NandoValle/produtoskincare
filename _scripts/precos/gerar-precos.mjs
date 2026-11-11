#!/usr/bin/env node
/*
 * gerar-precos.mjs — gera /precos.json a partir de dados/precos.ndjson (append-only).
 *
 * Fontes:
 *   dados/precos.ndjson  → observações de preço (imutáveis; correção = nova observação)
 *   dados/tamanhos.json  → tamanho da embalagem (pendência editorial; null = sem custo/dia)
 *   dados/doses.json     → dose média diária por categoria (premissa sempre exibida)
 *   produtos.json        → catálogo (nome, marca, passo) — local ou via PRODUTOS_URL
 *
 * Uso:
 *   node gerar-precos.mjs                  # gera precos.json nesta pasta
 *   PRODUTOS_URL=https://produtoskincare.com.br/produtos.json node gerar-precos.mjs
 *
 * Regras de honestidade (não negociáveis):
 *   - selo só com n>=8 observações E produto com 30+ dias de histórico;
 *   - preço não conferido há >14 dias → badge "desatualizado" (selo apagado);
 *   - sem size_ml → sem custo por dia (nunca estimar volume escondido);
 *   - toda exibição carrega n de observações e data da conferência.
 */
import { readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const AQUI = dirname(fileURLToPath(import.meta.url));
const RAIZ = join(AQUI, "..", ".."); // raiz do repositório (= raiz publicada do site)
const JANELA_DIAS = 90;
const MIN_OBS = 8;
const MIN_IDADE_DIAS = 30;
const FRESCO_DIAS = 14;

// ---------- leitura ----------
const linhas = readFileSync(join(AQUI, "dados/precos.ndjson"), "utf8")
  .split("\n")
  .filter(Boolean)
  .map((l) => JSON.parse(l));
const tamanhos = JSON.parse(readFileSync(join(AQUI, "dados/tamanhos.json"), "utf8")).produtos;
const doses = JSON.parse(readFileSync(join(AQUI, "dados/doses.json"), "utf8"));

async function carregarCatalogo() {
  const url = process.env.PRODUTOS_URL;
  const bruto = url
    ? await (await fetch(url)).json()
    : JSON.parse(readFileSync(join(RAIZ, "produtos.json"), "utf8"));
  return new Map(bruto.produtos.map((p) => [p.id, p]));
}

const DOSE_POR_PASSO = { limpeza: "limpeza", tratamento: "tratamento", hidratacao: "hidratante", protetor: "protetor" };

// ---------- cálculo ----------
function percentil(ordenado, q) {
  if (ordenado.length === 0) return null;
  const pos = (ordenado.length - 1) * q;
  const baixo = Math.floor(pos), alto = Math.ceil(pos);
  return baixo === alto
    ? ordenado[baixo]
    : Math.round(ordenado[baixo] + (ordenado[alto] - ordenado[baixo]) * (pos - baixo));
}

function diasEntre(a, b) {
  return Math.round((new Date(b + "T12:00:00Z") - new Date(a + "T12:00:00Z")) / 86400000);
}

function calcular(produtoId, catalogo) {
  const hoje = new Date().toISOString().slice(0, 10);
  const obs = linhas
    .filter((o) => o.product_id === produtoId)
    .filter((o) => diasEntre(o.checked_at.slice(0, 10), hoje) <= JANELA_DIAS);

  // dedupe: melhor preço do dia (o que a pessoa realmente conseguiria pagar)
  const porDia = new Map();
  for (const o of obs) {
    const dia = o.checked_at.slice(0, 10);
    const anterior = porDia.get(dia);
    if (!anterior || o.price_cents < anterior.price_cents) porDia.set(dia, o);
  }
  const serie = [...porDia.entries()].sort((a, b) => a[0].localeCompare(b[0]));
  const valores = serie.map(([, o]) => o.price_cents).sort((a, b) => a - b);
  const atual = serie.length ? serie[serie.length - 1][1] : null;

  const n = serie.length;
  const idadeDias = atual ? diasEntre(atual.checked_at.slice(0, 10), hoje) : null;
  const primeiraObs = serie.length ? serie[0][0] : null;
  const idadeCatalogoDias = primeiraObs ? diasEntre(primeiraObs, hoje) : 0;

  let badge, motivo;
  if (!atual) {
    badge = "sem-historico"; motivo = "Sem observações de preço nos últimos 90 dias.";
  } else if (n < MIN_OBS || idadeCatalogoDias < MIN_IDADE_DIAS) {
    badge = "sem-historico";
    motivo = `Histórico em construção: ${n} observaç${n === 1 ? "ão" : "ões"} · primeiro registro em ${primeiraObs}. Selo a partir de ${MIN_OBS} observações e ${MIN_IDADE_DIAS} dias.`;
  } else if (idadeDias > FRESCO_DIAS) {
    badge = "desatualizado";
    motivo = `Preço não conferido há ${idadeDias} dias — o selo fica apagado até reconferir.`;
  } else {
    const p25 = percentil(valores, 0.25), p50 = percentil(valores, 0.5), p75 = percentil(valores, 0.75);
    if (atual.price_cents <= p25) { badge = "otimo"; motivo = "Entre os 25% mais baixos dos últimos 90 dias."; }
    else if (atual.price_cents <= p50) { badge = "bom"; motivo = "Abaixo da mediana dos últimos 90 dias."; }
    else if (atual.price_cents <= p75) { badge = "justo"; motivo = "Acima da mediana, dentro do esperado."; }
    else { badge = "alto"; motivo = "Acima de 75% dos preços dos últimos 90 dias — este produto costuma sair mais barato."; }
  }

  // custo por dia: só com tamanho real informado
  const cat = catalogo.get(produtoId) || {};
  const tam = tamanhos[produtoId] || {};
  const size = tam.size_ml ?? tam.size_g ?? null;
  let custo = null;
  if (size && atual) {
    const chaveDose = DOSE_POR_PASSO[cat.passo] || "outro";
    const dose = doses[chaveDose].dose_ml_dia;
    custo = {
      size_ml: size, dose_ml_dia: dose, dose_categoria: chaveDose,
      custo_dia_cents: Math.round((atual.price_cents * dose) / size),
      custo_30d_cents: Math.round((atual.price_cents * dose) / size) * 30,
      rendimento_dias: Math.round(size / dose),
      fonte_tamanho: tam.fonte || null,
    };
  }

  return {
    product_id: produtoId,
    nome: cat.nome || produtoId,
    marca: cat.marca || null,
    current: atual
      ? { price_cents: atual.price_cents, checked_at: atual.checked_at.slice(0, 10), retailer: atual.retailer, promo: !!atual.promo, url: atual.url || null }
      : null,
    window_days: JANELA_DIAS,
    n_observations: n,
    p25_cents: percentil(valores, 0.25),
    p50_cents: percentil(valores, 0.5),
    p75_cents: percentil(valores, 0.75),
    min_cents: valores.length ? valores[0] : null,
    max_cents: valores.length ? valores[valores.length - 1] : null,
    badge, badge_motivo: motivo,
    series: serie.map(([dia, o]) => [dia, o.price_cents]),
    custo,
  };
}

// ---------- geração ----------
const catalogo = await carregarCatalogo();
const saida = {
  versao: 1,
  gerado_em: new Date().toISOString(),
  janela_dias: JANELA_DIAS,
  regras: {
    selo_min_observacoes: MIN_OBS,
    selo_min_idade_dias: MIN_IDADE_DIAS,
    preco_fresco_dias: FRESCO_DIAS,
    aviso: "Preço conferido na data indicada; pode ter mudado na loja. Custo por dia é estimativa com base na dose média da categoria. Não é diagnóstico médico.",
  },
  produtos: {},
};
for (const id of catalogo.keys()) saida.produtos[id] = calcular(id, catalogo);

writeFileSync(join(RAIZ, "precos.json"), JSON.stringify(saida, null, 1) + "\n");

// Atualiza a tabela da página ferramentas/precos/index.html entre os marcadores.
// Assim a página é estática (funciona sem JS) e sempre atual no build.
const ROTULO_BADGE = {
  "otimo": "🟢 ótimo", "bom": "🔵 bom", "justo": "⚪ justo", "alto": "🔴 alto",
  "sem-historico": "➖ em construção", "desatualizado": "⏸ desatualizado",
};
function brl(cents) {
  return cents == null ? "—" : "R$ " + (cents / 100).toFixed(2).replace(".", ",");
}
function dataBR(iso) {
  return iso ? iso.slice(0, 10).split("-").reverse().join("/") : "—";
}
const paginaTabela = join(RAIZ, "ferramentas", "precos", "index.html");
try {
  const html = readFileSync(paginaTabela, "utf8");
  const ini = "<!-- tabela-gerada:inicio -->", fim = "<!-- tabela-gerada:fim -->";
  const a = html.indexOf(ini), b = html.indexOf(fim);
  if (a !== -1 && b !== -1) {
    const linhas = [...catalogo.entries()]
      .sort(([, x], [, y]) => (x.nome || "").localeCompare(y.nome || "", "pt-BR"))
      .map(([id, cat]) => {
        const p = saida.produtos[id];
        const custo = p.custo ? "≈ " + brl(p.custo.custo_dia_cents) + "/dia" : "—";
        return `      <tr>\n        <td><a href="/produtos/${id}/">${cat.nome}</a>${cat.marca ? ` <span class="ig-nota">${cat.marca}</span>` : ""}</td>\n        <td>${brl(p.current && p.current.price_cents)}</td>\n        <td>${dataBR(p.current && p.current.checked_at)}</td>\n        <td>${p.n_observations}</td>\n        <td><span class="ps-selo ps-selo-${p.badge}" title="${p.badge_motivo}">${ROTULO_BADGE[p.badge]}</span></td>\n        <td>${custo}</td>\n      </tr>`;
      })
      .join("\n");
    writeFileSync(paginaTabela, html.slice(0, a + ini.length) + "\n" + linhas + "\n    " + html.slice(b));
    console.log("tabela de ferramentas/precos/index.html atualizada");
  }
} catch (e) {
  if (e.code !== "ENOENT") throw e;
}

const comSelo = Object.values(saida.produtos).filter((p) => ["otimo", "bom", "justo", "alto"].includes(p.badge)).length;
const comCusto = Object.values(saida.produtos).filter((p) => p.custo).length;
console.log(`precos.json gerado: ${Object.keys(saida.produtos).length} produtos · ${comSelo} com selo · ${comCusto} com custo/dia`);
