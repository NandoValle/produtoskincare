/* Previsão da pele ("Skin Forecast"): o que a pele pode pedir hoje, pelo clima.
   Uma só fonte para a home e para /ferramentas/clima/.

   Dois modos:
   - manual (sempre ligado): a pessoa diz o nível do UV, como está o ar e se vai suar. Nada sai do aparelho.
   - ao vivo (CONFIG.ativo): busca UV, umidade e temperatura da cidade no serviço de previsão.

   As regras só repetem o que a página /ferramentas/clima/ já diz (escala do UV e dicas de umidade).
   A nota de 0 a 100 é adequação ao dia, não qualidade do produto, e mostra de onde veio cada ponto.
   Funciona no navegador (window.PSPrevisao) e no Node (testes em _scripts/testar_previsao.js). */
(function (raiz) {
  "use strict";

  // Consulta ao vivo. DESLIGADA até você confirmar a licença do serviço:
  // a Open-Meteo é gratuita para uso não comercial; um site com links de afiliado pode precisar
  // do plano comercial (com chave). Para ligar: ativo: true. Com plano pago, preencha chave e
  // troque as URLs pelas do plano (confira na documentação da Open-Meteo).
  // Este é o único interruptor: a home e a página de clima leem daqui.
  var CONFIG = {
    ativo: false,
    geocodificacao: "https://geocoding-api.open-meteo.com/v1/search",
    previsao: "https://api.open-meteo.com/v1/forecast",
    chave: "",
    cacheHoras: 3,      // não consulta o serviço a cada visita
    viagemDias: 7       // "estou em outra cidade" vale por este prazo
  };

  var CHAVE = "ps_previsao_v1";        // { pele, manual:{dia,uv,ar,suor}, viagem:{lugar,ate}, cache:{...} }
  var CHAVE_CIDADE = "ps_clima_cidade"; // mesma chave que a página de clima já usava

  var NIVEIS = [
    { id: "baixo", rotulo: "Baixo", faixa: "0 a 2", uv: 1, cor: "#4c9a2a" },
    { id: "moderado", rotulo: "Moderado", faixa: "3 a 5", uv: 4, cor: "#d4b300" },
    { id: "alto", rotulo: "Alto", faixa: "6 a 7", uv: 6.5, cor: "#e07b00" },
    { id: "muito-alto", rotulo: "Muito alto", faixa: "8 a 10", uv: 9, cor: "#c8102e" },
    { id: "extremo", rotulo: "Extremo", faixa: "11 ou mais", uv: 11, cor: "#7b2c8e" }
  ];
  var PELES = [["oleosa", "Oleosa"], ["mista", "Mista"], ["normal", "Normal"], ["seca", "Seca"], ["sensivel", "Sensível"]];
  var PASSOS = [["limpeza", "Limpeza"], ["tratamento", "Tratamento"], ["hidratacao", "Hidratante"], ["protetor", "Protetor solar"]];
  var LOJAS = { amazon: "Amazon", shopee: "Shopee", mercadolivre: "Mercado Livre" };

  function nivelDoUV(uv) {
    if (uv == null || isNaN(uv)) return null;
    if (uv < 3) return NIVEIS[0];
    if (uv < 6) return NIVEIS[1];
    if (uv < 8) return NIVEIS[2];
    if (uv < 11) return NIVEIS[3];
    return NIVEIS[4];
  }
  function arDaUmidade(umid) {
    if (umid == null || isNaN(umid)) return "medio";
    return umid < 40 ? "seco" : umid > 75 ? "umido" : "medio";
  }

  /* ===== Regras: o que o dia pede ===== */
  // cond = { uv: número ou null, ar: "seco" | "medio" | "umido", suor: bool }
  function leitura(cond) {
    var n = nivelDoUV(cond.uv), pede = [];
    if (n && cond.uv >= 3) pede.push("proteção solar");
    if (cond.ar === "seco") pede.push("hidratação reforçada");
    if (cond.ar === "umido") pede.push("texturas leves");
    if (cond.suor) pede.push("reaplicação do protetor");
    var partes = [];
    if (n) partes.push("UV " + n.rotulo.toLowerCase() + (cond.uvExato != null ? " (" + Math.round(cond.uvExato) + ")" : ""));
    var pct = cond.umidade != null ? Math.round(cond.umidade) + "%" : "";
    if (cond.ar === "seco") partes.push("ar seco" + (pct ? " (" + pct + ")" : ""));
    else if (cond.ar === "umido") partes.push("ar úmido" + (pct ? " (" + pct + ")" : ""));
    else if (pct) partes.push("umidade " + pct);
    return {
      condicoes: partes.join(", "),
      pede: pede,
      frase: pede.length
        ? "Sua pele pode pedir " + juntar(pede) + "."
        : "Dia tranquilo para a pele: a rotina de sempre dá conta."
    };
  }
  function juntar(l) { return l.length < 2 ? l.join("") : l.slice(0, -1).join(", ") + " e " + l[l.length - 1]; }

  function rotinaDeHoje(cond, pele) {
    var uv = cond.uv, manha = [], noite = [], durante = [];
    manha.push({ passo: "Limpeza", texto: cond.ar === "seco" ? "Limpeza suave, com água morna ou fria: água muito quente resseca mais." : "Limpeza de sempre." });
    if (cond.ar === "seco") manha.push({ passo: "Hidratante", texto: "Prefira o mais encorpado que você tiver." + (pele === "oleosa" ? " Em pele oleosa, uma camada fina já ajuda." : "") });
    else if (cond.ar === "umido") manha.push({ passo: "Hidratante", texto: "Textura em gel costuma pesar menos no ar úmido e quente." });
    else manha.push({ passo: "Hidratante", texto: "O de sempre." });

    if (uv == null) manha.push({ passo: "Protetor solar", texto: "Último passo da manhã, todos os dias. Diga o nível do UV para ajustar a reaplicação." });
    else if (uv < 3) manha.push({ passo: "Protetor solar", texto: "UV baixo, pouco risco de queimadura. Para quem tem manchas ou melasma, o protetor diário continua valendo, porque a luz visível também escurece manchas." });
    else if (uv < 6) manha.push({ passo: "Protetor solar", texto: "Proteção necessária ao ar livre: protetor, óculos escuros e sombra perto do meio-dia." });
    else if (uv < 8) manha.push({ passo: "Protetor solar", texto: "FPS 30 ou mais" + (cond.ar === "umido" ? ", de preferência toque seco" : "") + ". Chapéu e roupa que cubra." });
    else if (uv < 11) manha.push({ passo: "Protetor solar", texto: "FPS 30 ou mais, com reforço de chapéu e roupa. Evite o sol direto no meio do dia." });
    else manha.push({ passo: "Protetor solar", texto: "FPS 30 ou mais e sombra sempre que puder: pele desprotegida pode queimar em poucos minutos." });

    if (uv != null && uv >= 6) durante.push("Reaplique o protetor a cada 2 horas fora de casa" + (cond.janela ? " (o UV passa de 3 entre " + cond.janela + ")" : "") + ".");
    else if (uv != null && uv >= 3 && cond.janela) durante.push("O UV passa de 3 entre " + cond.janela + ": reaplique se ficar ao ar livre.");
    if (cond.suor) durante.push("Depois de suar muito ou nadar, reaplique o protetor, mesmo que seja “resistente à água”.");

    noite.push({ passo: "Limpeza", texto: "Tire o protetor do dia." });
    noite.push({ passo: "Hidratante", texto: cond.ar === "seco" ? "Reforce o hidratante à noite, com uma textura mais encorpada." : "O de sempre." });
    return { manha: manha, durante: durante, noite: noite };
  }

  /* ===== Nota de adequação ao dia (0 a 100) ===== */
  function ehBusca(link) {
    var u = String(link || "");
    try { u = decodeURIComponent(u); } catch (e) {}
    return /amazon\.com\.br\/s[?/]|shopee\.com\.br\/search|lista\.mercadolivre\.com\.br/.test(u);
  }

  function pontuar(p, cond, pele) {
    var pts = 50, motivos = [], uv = cond.uv, ar = cond.ar, g = p.grupo || "", tipos = p.tipos || [];
    function soma(n, texto) { pts += n; motivos.push({ pontos: n, texto: texto }); }

    if (pele) {
      if ((p.evitar || []).indexOf(pele) >= 0) soma(-40, "não indicado para pele " + nomePele(pele));
      else if (tipos.indexOf(pele) >= 0) soma(15, "indicado para pele " + nomePele(pele));
      else if (tipos.indexOf("todos") >= 0) soma(8, "serve para todos os tipos de pele");
    }

    if (p.passo === "protetor") {
      if (uv == null) soma(10, "protetor é o último passo da manhã, todos os dias");
      else if (uv >= 8) soma(30, "UV muito alto ou extremo hoje");
      else if (uv >= 3) soma(20, "o UV passa de 3 hoje");
      else soma(5, "UV baixo hoje; segue valendo para quem tem manchas");
      if (ar === "umido" && (g === "protetor-toque-seco" || g === "protetor-gel")) soma(10, "textura leve para ar úmido");
      if (ar === "seco" && g === "protetor-hidratante") soma(10, "protetor hidratante para ar seco");
      if (ar === "umido" && g === "protetor-hidratante") soma(-5, "pode pesar no ar úmido");
    }

    if (p.passo === "hidratacao") {
      if (ar === "seco") {
        if (p.textura === "creme") soma(25, "textura encorpada para ar seco");
        else soma(5, "hidrata, mas a textura é leve para ar seco");
      } else if (ar === "umido") {
        if (p.textura === "gel") soma(20, "gel pesa menos no ar úmido");
        else soma(-10, "creme pode pesar no ar úmido");
      } else soma(5, "hidratante entra todo dia");
    }

    if (p.passo === "tratamento") {
      if (g === "serum-hidratacao" && ar === "seco") soma(20, "sérum hidratante para ar seco");
      else if (g === "serum-hidratacao" && ar === "umido") soma(5, "hidrata sem pesar");
    }

    if (p.passo === "limpeza") {
      if (ar === "seco" && g === "gel-limpeza-suave") soma(10, "limpeza suave para ar seco");
      if (ar === "seco" && g === "gel-limpeza-oleosa") soma(-10, "limpeza para pele oleosa pode ressecar no ar seco");
      if (g === "limpeza-oleo" && uv != null && uv >= 3) soma(5, "ajuda a tirar o protetor à noite");
    }

    if (ar === "seco" && (p.conc || []).indexOf("desidratacao") >= 0 && p.passo !== "hidratacao" && g !== "serum-hidratacao") soma(5, "voltado à desidratação");

    return { produto: p, nota: Math.max(0, Math.min(100, Math.round(pts))), motivos: motivos, busca: ehBusca(p.link) };
  }
  function nomePele(id) { for (var i = 0; i < PELES.length; i++) if (PELES[i][0] === id) return PELES[i][1].toLowerCase(); return id; }

  function ordenar(produtos, cond, pele) {
    return (produtos || []).map(function (p) { return pontuar(p, cond, pele); }).sort(function (a, b) {
      // no empate, vem antes quem tem oferta conferida
      return b.nota - a.nota || (a.busca ? 1 : 0) - (b.busca ? 1 : 0) || (b.produto.avaliacao || 0) - (a.produto.avaliacao || 0) || String(a.produto.nome).localeCompare(String(b.produto.nome));
    });
  }
  function melhorPorPasso(ordenados) {
    var saida = [];
    PASSOS.forEach(function (ps) {
      // só entra o passo em que o dia (ou a pele) deu algum motivo: nota acima do ponto de partida
      for (var i = 0; i < ordenados.length; i++) if (ordenados[i].produto.passo === ps[0]) { if (ordenados[i].nota > 50) saida.push({ passo: ps[1], item: ordenados[i] }); break; }
    });
    return saida;
  }

  /* ===== Previsão ao vivo: resposta do serviço -> condições ===== */
  function condicoesDaPrevisao(d) {
    var horas = (d.hourly && d.hourly.time) || [], uvs = (d.hourly && d.hourly.uv_index) || [];
    var agora = d.current && d.current.time ? d.current.time.slice(0, 13) : "";
    var i = -1;
    for (var k = 0; k < horas.length; k++) if (horas[k].slice(0, 13) === agora) { i = k; break; }
    var uvMax = d.daily && d.daily.uv_index_max ? d.daily.uv_index_max[0] : null;
    var acima = [];
    for (var j = 0; j < horas.length; j++) if (uvs[j] >= 3) acima.push(+horas[j].slice(11, 13));
    var umid = d.current ? d.current.relative_humidity_2m : null, temp = d.current ? d.current.temperature_2m : null;
    return {
      fonte: "previsao", uv: uvMax, uvExato: uvMax, uvAgora: i >= 0 ? uvs[i] : null,
      janela: acima.length ? acima[0] + "h e " + (acima[acima.length - 1] + 1) + "h" : "",
      umidade: umid, temperatura: temp, ar: arDaUmidade(umid), suor: temp != null && temp >= 30
    };
  }

  var API = {
    CONFIG: CONFIG, NIVEIS: NIVEIS, PELES: PELES, CHAVE: CHAVE,
    nivelDoUV: nivelDoUV, arDaUmidade: arDaUmidade, leitura: leitura, rotinaDeHoje: rotinaDeHoje,
    pontuar: pontuar, ordenar: ordenar, melhorPorPasso: melhorPorPasso, ehBusca: ehBusca,
    condicoesDaPrevisao: condicoesDaPrevisao
  };
  if (typeof module !== "undefined" && module.exports) { module.exports = API; return; }
  raiz.PSPrevisao = API;

  /* ===== Navegador: estado, busca e tela ===== */
  var doc = raiz.document;
  function esc(t) { return String(t == null ? "" : t).replace(/[&<>"']/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]; }); }
  function hoje() { var d = new Date(); return d.getFullYear() + "-" + String(d.getMonth() + 1).padStart(2, "0") + "-" + String(d.getDate()).padStart(2, "0"); }
  function ler() { try { return JSON.parse(localStorage.getItem(CHAVE) || "{}") || {}; } catch (e) { return {}; } }
  function gravar(e) { try { localStorage.setItem(CHAVE, JSON.stringify(e)); } catch (x) {} }
  function evento(nome) { try { if (raiz.PSAnalytics) raiz.PSAnalytics.evento(nome); } catch (e) {} }
  function url(base, params) { if (CONFIG.chave) params.apikey = CONFIG.chave; return base + "?" + new URLSearchParams(params).toString(); }

  function peleSalva() {
    var e = ler();
    if (e.pele) return e.pele;
    try { var p = localStorage.getItem("rt_pele") || ""; if (PELES.some(function (x) { return x[0] === p; })) return p; } catch (x) {}
    return "";
  }
  function lugarAtual() {
    var e = ler();
    if (e.viagem && e.viagem.ate >= hoje() && e.viagem.lugar) return { lugar: e.viagem.lugar, viagem: e.viagem };
    try { var c = JSON.parse(localStorage.getItem(CHAVE_CIDADE) || "null"); if (c && c.latitude != null) return { lugar: c }; } catch (x) {}
    return null;
  }
  function nomeLugar(l) { return [l.name, l.admin1].filter(Boolean).join(", "); }

  function buscarCidades(nome) {
    return fetch(url(CONFIG.geocodificacao, { name: nome, count: 5, language: "pt", format: "json" }))
      .then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
      .then(function (d) { return (d && d.results) || []; });
  }
  // Devolve a resposta do serviço; guarda por CONFIG.cacheHoras para não consultar a cada visita.
  function buscarPrevisao(lugar) {
    var e = ler(), id = lugar.latitude + "," + lugar.longitude, c = e.cache;
    if (c && c.id === id && c.dia === hoje() && Date.now() - c.em < CONFIG.cacheHoras * 3600000) return Promise.resolve(c.dados);
    return fetch(url(CONFIG.previsao, {
      latitude: lugar.latitude, longitude: lugar.longitude, timezone: "auto", forecast_days: 1,
      current: "temperature_2m,relative_humidity_2m", hourly: "uv_index", daily: "uv_index_max"
    })).then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); }).then(function (d) {
      var e2 = ler(); e2.cache = { id: id, dia: hoje(), em: Date.now(), dados: d }; gravar(e2);
      return d;
    });
  }
  API.buscarCidades = buscarCidades;
  API.buscarPrevisao = buscarPrevisao;

  var catalogo = null;
  function produtos() {
    if (!catalogo) catalogo = fetch("/produtos.json").then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); }).then(function (d) { return d.produtos || []; });
    return catalogo;
  }
  function dataBR(iso) { var m = /^(\d{4})-(\d{2})-(\d{2})/.exec(iso || ""); return m ? m[3] + "/" + m[2] + "/" + m[1] : ""; }
  function preco(v) { return typeof v === "number" ? "R$ " + v.toFixed(2).replace(".", ",") : ""; }

  function cartaoProduto(it, passo) {
    var p = it.produto;
    var motivos = it.motivos.map(function (m) { return "<li><b>" + (m.pontos > 0 ? "+" : "−") + Math.abs(m.pontos) + "</b> " + esc(m.texto) + "</li>"; }).join("");
    var compra = it.busca
      ? '<span class="pp-sem">sem oferta verificada</span>'
      : '<a class="pp-loja" href="' + esc(p.link) + '" target="_blank" rel="noopener sponsored" data-produto="' + esc(p.id) + '">Ver na ' + esc(LOJAS[p.plataforma] || "loja") + ' <span aria-hidden="true">↗</span></a>';
    var precoTxt = !it.busca && p.preco ? '<span class="pp-preco">' + preco(p.preco) + (p.preco_em ? " em " + dataBR(p.preco_em) : "") + "</span>" : "";
    return '<li class="pp-produto">' +
      (passo ? '<p class="pp-passo">' + esc(passo) + "</p>" : "") +
      '<p class="pp-nome">' + esc(p.nome) + "</p>" +
      '<p class="pp-nota"><strong>' + it.nota + '</strong><span>/100 para hoje</span></p>' +
      '<details class="pp-porque"><summary>De onde vem a nota</summary><ul><li><b>50</b> ponto de partida</li>' + motivos + "</ul></details>" +
      '<p class="pp-compra">' + precoTxt + compra + "</p></li>";
  }

  function montar(alvo, opcoes) {
    opcoes = opcoes || {};
    var est = ler(), pele = peleSalva(), cond = null, aviso = "";
    var manual = est.manual && est.manual.dia === hoje() ? est.manual : null;

    alvo.classList.add("pp");
    alvo.innerHTML =
      '<div class="pp-entrada">' +
        (CONFIG.ativo
          ? '<form class="pp-cidade" autocomplete="off"><label for="pp-cidade">Sua cidade</label><div class="pp-linha"><input id="pp-cidade" required minlength="2" placeholder="Ex.: Belo Horizonte"><button type="submit" class="pp-btn">Ver o dia</button></div>' +
            '<label class="pp-check"><input type="checkbox" id="pp-viagem"> Estou em outra cidade só por uns dias (volta à minha em ' + CONFIG.viagemDias + " dias)</label>" +
            '<div class="pp-opcoes" id="pp-opcoes"></div>' +
            '<p class="pp-fina">O nome da cidade vai ao serviço de previsão do tempo para buscar os dados. A localização exata do seu aparelho não é usada. <a href="/privacidade/">Privacidade</a></p></form>' +
            '<details class="pp-manual-det"><summary>Prefiro informar à mão</summary><div class="pp-manual"></div></details>'
          : '<div class="pp-manual"></div>') +
        '<fieldset class="pp-grupo"><legend>Sua pele (opcional)</legend><div class="pp-chips" data-grupo="pele">' +
          PELES.map(function (p) { return '<button type="button" data-v="' + p[0] + '" aria-pressed="false">' + p[1] + "</button>"; }).join("") +
        "</div></fieldset>" +
      "</div>" +
      '<div class="pp-saida" role="status" aria-live="polite"></div>';

    var saida = alvo.querySelector(".pp-saida");
    alvo.querySelectorAll(".pp-manual").forEach(function (m) {
      m.innerHTML =
        '<fieldset class="pp-grupo"><legend>Índice UV de hoje</legend><div class="pp-chips" data-grupo="uv">' +
          NIVEIS.map(function (n) { return '<button type="button" data-v="' + n.id + '" aria-pressed="false"><i style="--c:' + n.cor + '" aria-hidden="true"></i>' + n.rotulo + " <small>" + n.faixa + "</small></button>"; }).join("") +
          '<button type="button" data-v="" aria-pressed="false">Não sei</button></div>' +
          '<p class="pp-fina">O app de tempo do celular costuma mostrar o índice UV do dia.</p></fieldset>' +
        '<fieldset class="pp-grupo"><legend>O ar hoje</legend><div class="pp-chips" data-grupo="ar">' +
          '<button type="button" data-v="seco" aria-pressed="false">Seco</button><button type="button" data-v="medio" aria-pressed="false">Nem seco nem úmido</button><button type="button" data-v="umido" aria-pressed="false">Úmido</button></div></fieldset>' +
        '<label class="pp-check"><input type="checkbox" data-suor> Vou suar muito ou nadar</label>';
    });

    function marcar() {
      alvo.querySelectorAll(".pp-chips").forEach(function (g) {
        var grupo = g.getAttribute("data-grupo");
        var valor = grupo === "pele" ? pele : manual ? (grupo === "uv" ? (manual.uv || "") : manual.ar) : null;
        g.querySelectorAll("button").forEach(function (b) { b.setAttribute("aria-pressed", String(valor !== null && b.getAttribute("data-v") === valor && (grupo !== "pele" || !!pele))); });
      });
      var s = alvo.querySelector("[data-suor]"); if (s) s.checked = !!(manual && manual.suor);
    }

    function condManual() {
      if (!manual) return null;
      var n = null; NIVEIS.forEach(function (x) { if (x.id === manual.uv) n = x; });
      return { fonte: "manual", uv: n ? n.uv : null, ar: manual.ar || "medio", suor: !!manual.suor };
    }

    function desenhar() {
      marcar();
      if (!cond) {
        saida.innerHTML = aviso ? '<p class="pp-aviso">' + esc(aviso) + "</p>" : '<p class="pp-vazio">' + (CONFIG.ativo ? "Digite a cidade para ver o que o dia pede." : "Diga como está o dia aí e a rotina de hoje aparece aqui.") + "</p>";
        if (opcoes.aoMudar) opcoes.aoMudar(null);
        return;
      }
      var l = leitura(cond), r = rotinaDeHoje(cond, pele), n = nivelDoUV(cond.uv);
      var onde = cond.lugar ? "Hoje em " + nomeLugar(cond.lugar) : "Hoje";
      var passos = function (lista) { return lista.map(function (x) { return "<li><b>" + esc(x.passo) + "</b> " + esc(x.texto) + "</li>"; }).join(""); };
      var numeros = cond.fonte === "previsao"
        ? '<div class="pp-numeros">' +
            '<div><strong>' + (cond.uv != null ? Math.round(cond.uv) : "–") + "</strong><span>UV máximo" + (n ? ' · <i style="--c:' + n.cor + '" aria-hidden="true"></i>' + n.rotulo : "") + "</span></div>" +
            '<div><strong>' + (cond.uvAgora != null ? Math.round(cond.uvAgora) : "–") + "</strong><span>UV agora</span></div>" +
            '<div><strong>' + (cond.umidade != null ? Math.round(cond.umidade) + "%" : "–") + "</strong><span>umidade do ar</span></div>" +
            '<div><strong>' + (cond.temperatura != null ? Math.round(cond.temperatura) + "°" : "–") + "</strong><span>temperatura</span></div></div>"
        : "";
      saida.innerHTML =
        (aviso ? '<p class="pp-aviso">' + esc(aviso) + "</p>" : "") +
        '<p class="pp-onde">' + esc(onde) + (l.condicoes ? ": " + esc(l.condicoes) : "") + "</p>" +
        '<p class="pp-frase">' + esc(l.frase) + "</p>" + numeros +
        '<div class="pp-rotina">' +
          '<div><h3>Manhã</h3><ol>' + passos(r.manha) + "</ol></div>" +
          (r.durante.length ? '<div><h3>Durante o dia</h3><ul>' + r.durante.map(function (t) { return "<li>" + esc(t) + "</li>"; }).join("") + "</ul></div>" : "") +
          '<div><h3>Noite</h3><ol>' + passos(r.noite) + "</ol></div>" +
        "</div>" +
        '<p class="pp-fina">' + (cond.fonte === "previsao"
          ? "Dados: previsão de modelo meteorológico da Open-Meteo, não medição no local. Nuvens, altitude, areia e água mudam a exposição real. "
          : "Feito com o que você informou; nada saiu do aparelho. ") +
          'As dicas são as da página de <a href="/ferramentas/clima/">índice UV e clima</a>. Sugestão, não prescrição.</p>' +
        '<div class="pp-catalogo"><h3>Se faltar algum passo</h3><p class="pp-fina">Primeiro o que você já tem. Do catálogo do site, estes são os que mais combinam com o dia' + (pele ? " e com pele " + esc(nomePele(pele)) : "") + ". A nota mede adequação ao dia, não qualidade. Links de afiliado.</p><div data-catalogo><p class=\"pp-fina\">Lendo o catálogo…</p></div></div>";

      var caixa = saida.querySelector("[data-catalogo]");
      produtos().then(function (lista) {
        var ord = ordenar(lista, cond, pele), melhores = melhorPorPasso(ord);
        caixa.innerHTML = '<ul class="pp-produtos">' + melhores.map(function (m) { return cartaoProduto(m.item, m.passo); }).join("") + "</ul>" +
          '<details class="pp-todos"><summary>Ver os ' + ord.length + ' produtos do catálogo, do mais ao menos adequado hoje</summary><ul class="pp-produtos pp-lista">' +
          ord.map(function (it) { return cartaoProduto(it, ""); }).join("") + "</ul></details>";
      }).catch(function () { caixa.innerHTML = '<p class="pp-fina">Não consegui ler o catálogo agora. A rotina acima não depende dele.</p>'; });
      if (opcoes.aoMudar) opcoes.aoMudar({ cond: cond, leitura: l, onde: onde });
    }

    function usarManual() { cond = condManual(); aviso = ""; desenhar(); }
    function salvarManual(campo, valor) {
      manual = manual || { dia: hoje(), uv: "", ar: "medio", suor: false };
      manual.dia = hoje(); manual[campo] = valor;
      var e = ler(); e.manual = manual; gravar(e);
      evento("previsao/manual");
      usarManual();
    }

    function aoVivo(lugar, viagem) {
      saida.innerHTML = '<p class="pp-vazio">Buscando a previsão…</p>';
      buscarPrevisao(lugar).then(function (d) {
        cond = condicoesDaPrevisao(d); cond.lugar = lugar;
        aviso = viagem ? "Cidade temporária até " + dataBR(viagem.ate) + ". Depois, volta a valer a sua cidade." : "";
        evento("previsao/consulta");
        desenhar();
      }).catch(function () {
        // O serviço falhou: a tela nunca fica sem contexto. Vale o que a pessoa informar à mão.
        cond = condManual();
        aviso = "Não consegui buscar a previsão agora. Informe o dia à mão, logo abaixo, ou tente de novo em alguns minutos.";
        var det = alvo.querySelector(".pp-manual-det"); if (det) det.open = true;
        desenhar();
      });
    }

    alvo.addEventListener("click", function (ev) {
      var b = ev.target.closest ? ev.target.closest(".pp-chips button") : null;
      if (!b || !alvo.contains(b)) return;
      var grupo = b.parentNode.getAttribute("data-grupo"), v = b.getAttribute("data-v");
      if (grupo === "pele") {
        pele = pele === v ? "" : v;
        var e = ler(); e.pele = pele; gravar(e);
        desenhar();
      } else salvarManual(grupo, v);
    });
    alvo.addEventListener("change", function (ev) { if (ev.target.hasAttribute && ev.target.hasAttribute("data-suor")) salvarManual("suor", ev.target.checked); });

    var form = alvo.querySelector(".pp-cidade");
    if (form) {
      var campo = form.querySelector("#pp-cidade"), opc = form.querySelector("#pp-opcoes");
      var escolher = function (lugar) {
        var viagem = null;
        if (form.querySelector("#pp-viagem").checked) {
          var ate = new Date(); ate.setDate(ate.getDate() + CONFIG.viagemDias);
          viagem = { lugar: lugar, ate: ate.getFullYear() + "-" + String(ate.getMonth() + 1).padStart(2, "0") + "-" + String(ate.getDate()).padStart(2, "0") };
          var e = ler(); e.viagem = viagem; gravar(e);
        } else {
          var e2 = ler(); delete e2.viagem; gravar(e2);
          try { localStorage.setItem(CHAVE_CIDADE, JSON.stringify(lugar)); } catch (x) {}
        }
        aoVivo(lugar, viagem);
      };
      form.addEventListener("submit", function (ev) {
        ev.preventDefault();
        var nome = campo.value.trim(); if (nome.length < 2) return;
        opc.innerHTML = "";
        buscarCidades(nome).then(function (res) {
          if (!res.length) { aviso = "Não encontrei essa cidade. Confira o nome."; cond = null; desenhar(); return; }
          if (res.length === 1) { escolher(res[0]); return; }
          opc.innerHTML = res.map(function (r, k) { return '<button type="button" data-k="' + k + '">' + esc([r.name, r.admin1, r.country_code].filter(Boolean).join(", ")) + "</button>"; }).join("");
          opc.querySelectorAll("button").forEach(function (b) { b.addEventListener("click", function () { opc.innerHTML = ""; escolher(res[+b.getAttribute("data-k")]); }); });
        }).catch(function () { aviso = "Não consegui buscar a cidade agora. Informe o dia à mão ou tente de novo em alguns minutos."; cond = condManual(); var det = alvo.querySelector(".pp-manual-det"); if (det) det.open = true; desenhar(); });
      });
      var la = lugarAtual();
      if (la) { campo.value = la.lugar.name || ""; aoVivo(la.lugar, la.viagem); return; }
    }
    usarManual();
  }
  API.montar = montar;

  function iniciar() {
    var alvos = doc.querySelectorAll("[data-previsao-pele]");
    Array.prototype.forEach.call(alvos, function (alvo) {
      var faixa = doc.getElementById(alvo.getAttribute("data-faixa") || "");
      montar(alvo, {
        aoMudar: faixa ? function (r) {
          var texto = faixa.querySelector("[data-faixa-texto]");
          if (texto) texto.textContent = r ? r.onde + (r.leitura.condicoes ? ": " + r.leitura.condicoes : "") + ". " + r.leitura.frase : faixa.getAttribute("data-padrao") || "";
        } : null
      });
    });
  }
  if (doc) { if (doc.readyState === "loading") doc.addEventListener("DOMContentLoaded", iniciar); else iniciar(); }
})(typeof window !== "undefined" ? window : this);
