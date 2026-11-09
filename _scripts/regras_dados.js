/* Exporta, em JSON, o que os geradores em Python precisam das regras de /regras-ativos.js,
 * para que as páginas geradas usem exatamente as mesmas regras do site (fonte única).
 *
 * Uso: node _scripts/regras_dados.js < pedido.json
 * Pedido: { "pares": [["retinol", "vitc"], ["glicolico", "irritada"], ...] }  (ids de ATIVOS ou de ESTADOS)
 * Resposta: { versao, ativos, classes, pares: [{ a, b, normal, sensivel }], produtos: { id: [classes] } }
 */
"use strict";
const fs = require("fs");
const path = require("path");
const R = require(path.join(__dirname, "..", "regras-ativos.js"));

const pedido = JSON.parse(fs.readFileSync(0, "utf8") || "{}");
const porId = Object.fromEntries(R.ATIVOS.map(a => [a.id, a]).concat(Object.values(R.ESTADOS).map(e => [e.id, e])));
const limpar = r => ({ resultado: r.resultado, rotulo: R.ROTULOS[r.resultado], motivo: r.motivo, nota: r.nota || "", regra: r.regra });

const pares = (pedido.pares || []).map(([a, b]) => {
  if (!porId[a] || !porId[b]) throw new Error("ativo desconhecido: " + a + " / " + b);
  return { a, b, normal: limpar(R.avaliarPar(porId[a], porId[b], {})), sensivel: limpar(R.avaliarPar(porId[a], porId[b], { sensivel: true })) };
});

const catalogo = JSON.parse(fs.readFileSync(path.join(__dirname, "..", "produtos.json"), "utf8").replace(/^﻿/, ""));
const produtos = {};
catalogo.produtos.forEach(p => { produtos[p.id] = [...new Set(R.detectar(R.textoDoProduto(p)).map(a => a.classe))]; });

process.stdout.write(JSON.stringify({ versao: R.VERSAO, ativos: R.ATIVOS, classes: R.CLASSES, perfil: R.PERFIL, pares, produtos }));
