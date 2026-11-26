/* Clima: configuração do provedor (Open-Meteo), faixas de qualidade do ar e o aviso do topo do site.
 *
 * Quem carrega este arquivo:
 *  - /ferramentas/clima/ (tag <script> comum, antes do script da página), para usar CONFIG e as faixas;
 *  - /analytics.js, em qualquer outra página, e SÓ quando já existe uma cidade guardada neste aparelho
 *    (chave "ps_clima_cidade", gravada pela página de clima). Sem cidade guardada, este arquivo nem é baixado.
 *
 * O aviso do topo:
 *  - nunca pede cidade nem localização; usa só a cidade que a pessoa escolheu na página de clima;
 *  - aparece quando o UV máximo de hoje é 8 ou mais, ou quando o ar está na faixa "ruim" ou pior;
 *  - faz no máximo uma consulta por dia por cidade (o resultado do dia fica em "ps_clima_dia");
 *  - o botão de fechar vale até o fim do dia ("ps_clima_aviso_fechado").
 * Tudo fica no localStorage deste aparelho. Para o provedor vão só as coordenadas da cidade.
 */
(function () {
  "use strict";
  if (window.PSClima) return;

  // Consulta ao vivo do UV e da qualidade do ar. DESLIGADA até você confirmar a licença do serviço:
  // a Open-Meteo é gratuita para uso não comercial; um site com links de afiliado pode precisar
  // do plano comercial (com chave). Para ligar: ativo: true. Com plano pago, preencha chave e
  // troque as URLs pelas do plano (confira na documentação da Open-Meteo).
  // Este é o único interruptor: ele liga a consulta na página de clima e o aviso do topo.
  var CONFIG = {
    ativo: false,
    geocodificacao: "https://geocoding-api.open-meteo.com/v1/search",
    previsao: "https://api.open-meteo.com/v1/forecast",
    qualidadeAr: "https://air-quality-api.open-meteo.com/v1/air-quality",
    chave: ""
  };

  var CHAVE_CIDADE = "ps_clima_cidade";
  var CHAVE_DIA = "ps_clima_dia";
  var CHAVE_FECHADO = "ps_clima_aviso_fechado";
  var UV_AVISO = 8;   // "muito alto" na escala internacional do índice UV
  var AR_AVISO = 60;  // começo da faixa "ruim" do índice europeu

  /* Faixas do índice europeu de qualidade do ar (European AQI), como a Open-Meteo publica:
   * 0-20 bom, 20-40 razoável, 40-60 moderado, 60-80 ruim, 80-100 muito ruim, acima de 100 extremamente ruim.
   * Valor exatamente no limite cai na faixa pior. Os textos são os mesmos da tabela de /ferramentas/clima/.
   * Só limpeza: não há consenso de que cosmético proteja a pele da poluição, então nada disso é prometido aqui. */
  var FAIXAS_AR = [
    { ate: 20, nome: "Bom", cor: "#50ccaa", texto: "Nada a mudar na rotina." },
    { ate: 40, nome: "Razoável", cor: "#9bd34f", texto: "Nada a mudar na rotina." },
    { ate: 60, nome: "Moderado", cor: "#d4b300", texto: "Rotina de sempre. A limpeza habitual à noite basta." },
    { ate: 80, nome: "Ruim", cor: "#e07b00", texto: "À noite, limpe bem o rosto para tirar a sujeira, o suor e o protetor acumulados no dia." },
    { ate: 100, nome: "Muito ruim", cor: "#c8102e", texto: "À noite, limpe bem o rosto. Para a saúde, vale a orientação das autoridades locais." },
    { ate: Infinity, nome: "Extremamente ruim", cor: "#7b2c8e", texto: "À noite, limpe bem o rosto. Para a saúde, vale a orientação das autoridades locais." }
  ];
  function faixaAr(aqi) {
    for (var i = 0; i < FAIXAS_AR.length; i++) if (aqi < FAIXAS_AR[i].ate) return FAIXAS_AR[i];
    return FAIXAS_AR[FAIXAS_AR.length - 1];
  }

  function url(base, params) {
    if (CONFIG.chave) params.apikey = CONFIG.chave;
    return base + "?" + new URLSearchParams(params).toString();
  }
  function json(r) { if (!r.ok) throw new Error(r.status); return r.json(); }
  function num(v) { return typeof v === "number" && isFinite(v) ? v : null; }

  function hoje() {
    var d = new Date();
    return d.getFullYear() + "-" + ("0" + (d.getMonth() + 1)).slice(-2) + "-" + ("0" + d.getDate()).slice(-2);
  }
  function ler(chave) { try { return JSON.parse(localStorage.getItem(chave) || "null"); } catch (e) { return null; } }
  function gravar(chave, valor) { try { localStorage.setItem(chave, JSON.stringify(valor)); } catch (e) {} }

  function lerCidade() {
    var c = ler(CHAVE_CIDADE);
    return c && num(c.latitude) != null && num(c.longitude) != null ? c : null;
  }
  function esquecer() {
    try {
      localStorage.removeItem(CHAVE_CIDADE);
      localStorage.removeItem(CHAVE_DIA);
      localStorage.removeItem(CHAVE_FECHADO);
    } catch (e) {}
  }

  /* Qualidade do ar de hoje. Vão só latitude e longitude da cidade.
   * Devolve { aqi: pior hora de hoje, agora: índice agora, pm25: PM2,5 agora em µg/m³ }. */
  function buscarAr(lugar) {
    return fetch(url(CONFIG.qualidadeAr, {
      latitude: lugar.latitude, longitude: lugar.longitude, timezone: "auto", forecast_days: 1,
      current: "european_aqi,pm2_5", hourly: "european_aqi"
    })).then(json).then(function (d) {
      var horas = ((d.hourly && d.hourly.european_aqi) || []).filter(function (v) { return num(v) != null; });
      var agora = d.current ? num(d.current.european_aqi) : null;
      var pior = horas.length ? Math.max.apply(null, horas) : agora;
      if (pior == null) throw new Error("sem dado");
      return { aqi: pior, agora: agora, pm25: d.current ? num(d.current.pm2_5) : null };
    });
  }
  /* UV máximo de hoje (para o aviso; a página de clima faz a própria consulta, mais completa). */
  function buscarUv(lugar) {
    return fetch(url(CONFIG.previsao, {
      latitude: lugar.latitude, longitude: lugar.longitude, timezone: "auto", forecast_days: 1, daily: "uv_index_max"
    })).then(json).then(function (d) {
      var uv = d.daily && d.daily.uv_index_max ? num(d.daily.uv_index_max[0]) : null;
      if (uv == null) throw new Error("sem dado");
      return uv;
    });
  }

  /* Resultado do dia, guardado no aparelho: uma consulta por dia por cidade. */
  function lerDia(lugar) {
    var d = ler(CHAVE_DIA);
    return d && d.dia === hoje() && d.lat === lugar.latitude && d.lon === lugar.longitude ? d : null;
  }
  function guardarDia(lugar, uv, ar, pendente) {
    var d = { dia: hoje(), lat: lugar.latitude, lon: lugar.longitude, uv: num(uv), ar: ar ? { aqi: ar.aqi, pm25: ar.pm25 } : null };
    if (pendente) d.pendente = pendente;
    gravar(CHAVE_DIA, d);
    return d;
  }

  /* Texto do aviso, ou "" quando o dia não pede aviso. */
  function textoAviso(lugar, dia) {
    var uv = dia.uv != null ? Math.round(dia.uv) : null;
    var uvAlto = uv != null && uv >= UV_AVISO;
    var arRuim = !!(dia.ar && dia.ar.aqi >= AR_AVISO);
    if (!uvAlto && !arRuim) return "";
    var onde = lugar.name ? " em " + lugar.name : "";
    var ar = arRuim ? "ar " + faixaAr(dia.ar.aqi).nome.toLowerCase() : "";
    var indice = arRuim ? " (índice europeu " + Math.round(dia.ar.aqi) + ")" : "";
    if (uvAlto && arRuim) return "UV " + uv + " e " + ar + indice + " hoje" + onde + ": reaplique o protetor e limpe bem o rosto à noite.";
    if (uvAlto) return "UV " + uv + " hoje" + onde + ": reaplique o protetor.";
    return ar.charAt(0).toUpperCase() + ar.slice(1) + " hoje" + onde + indice + ": limpe bem o rosto à noite.";
  }

  var CSS =
    ".ps-clima-aviso{display:grid;grid-template-rows:0fr;transition:grid-template-rows .32s ease;" +
    "background:var(--papel-2,var(--champagne,#F0E9DF));color:var(--tinta,var(--ink,#17120E));" +
    "font-family:var(--fonte-corpo,var(--sans,'Manrope','Segoe UI',sans-serif));font-size:.92rem;line-height:1.45}" +
    ".ps-clima-aviso.aberto{grid-template-rows:1fr}" +
    ".ps-clima-aviso>div{overflow:hidden;min-height:0}" +
    ".ps-clima-aviso-linha{box-sizing:border-box;display:flex;align-items:center;gap:12px;max-width:1328px;margin:0 auto;" +
    "padding:6px 8px 6px 16px;border-bottom:1px solid var(--linha,var(--line,#E4DBCE))}" +
    ".ps-clima-aviso p{flex:1 1 auto;min-width:0;margin:0;overflow-wrap:anywhere}" +
    ".ps-clima-aviso a{color:var(--rosa,var(--gold,#755728));font-weight:600;text-decoration:underline;white-space:nowrap}" +
    ".ps-clima-aviso small{font-size:.86em;color:var(--suave,var(--muted,#5A4C41))}" +
    ".ps-clima-aviso button{flex:0 0 auto;width:44px;height:44px;border:0;border-radius:999px;background:transparent;" +
    "color:inherit;font:inherit;font-size:1.4rem;line-height:1;cursor:pointer}" +
    ".ps-clima-aviso button:hover{background:var(--linha,var(--line,#E4DBCE))}" +
    ".ps-clima-aviso button:focus-visible{outline:2px solid var(--rosa,var(--gold,#755728));outline-offset:-4px}" +
    "@media(prefers-reduced-motion:reduce){.ps-clima-aviso{transition:none}}" +
    "@media print{.ps-clima-aviso{display:none}}";

  function mostrarAviso(texto) {
    if (document.querySelector(".ps-clima-aviso") || !document.body) return;
    var estilo = document.createElement("style");
    estilo.textContent = CSS;
    document.head.appendChild(estilo);

    var caixa = document.createElement("div");
    caixa.className = "ps-clima-aviso";
    caixa.setAttribute("role", "status");
    var dentro = document.createElement("div");
    var linha = document.createElement("div");
    linha.className = "ps-clima-aviso-linha";
    var p = document.createElement("p");
    var fechar = document.createElement("button");
    fechar.type = "button";
    fechar.setAttribute("aria-label", "Fechar o aviso de clima até amanhã");
    fechar.title = "Fechar até amanhã";
    fechar.textContent = "×";
    linha.appendChild(p);
    linha.appendChild(fechar);
    dentro.appendChild(linha);
    caixa.appendChild(dentro);

    // Antes do cabeçalho (que é sticky): o aviso rola com a página e nunca cobre o menu.
    var topo = document.querySelector("body > .ps-topo");
    if (topo) document.body.insertBefore(caixa, topo);
    else {
      var pular = document.querySelector("body > .skip-link");
      document.body.insertBefore(caixa, pular ? pular.nextSibling : document.body.firstChild);
    }

    var semMovimento = window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches;
    fechar.addEventListener("click", function () {
      try { localStorage.setItem(CHAVE_FECHADO, hoje()); } catch (e) {}
      var tirar = function () { if (caixa.parentNode) caixa.parentNode.removeChild(caixa); };
      if (semMovimento) { tirar(); return; }
      caixa.classList.remove("aberto");
      setTimeout(tirar, 360);
    });

    // O texto entra depois de a região role="status" existir, para o leitor de tela anunciar.
    // A altura abre devagar (grid 0fr -> 1fr) para não empurrar a página de uma vez.
    requestAnimationFrame(function () {
      p.appendChild(document.createTextNode(texto + " "));
      var a = document.createElement("a");
      a.href = "/ferramentas/clima/";
      a.textContent = "Ver detalhes";
      p.appendChild(a);
      var fonte = document.createElement("small");
      fonte.textContent = " Previsão: Open-Meteo.";
      p.appendChild(fonte);
      caixa.classList.add("aberto");
    });
  }

  function aviso() {
    if (!CONFIG.ativo) return;
    if (location.pathname.indexOf("/ferramentas/clima") === 0) return; // lá o dado completo já está na página
    if ((document.documentElement.lang || "pt").toLowerCase().indexOf("pt") !== 0) return; // /en/ e /es/: sem aviso
    var lugar = lerCidade();
    if (!lugar) return;
    try { if (localStorage.getItem(CHAVE_FECHADO) === hoje()) return; } catch (e) { return; }

    var dia = lerDia(lugar);
    if (dia && !dia.pendente) { var t = textoAviso(lugar, dia); if (t) mostrarAviso(t); return; }

    // Primeira página do dia com esta cidade: uma consulta. Terminou (com resposta ou com erro do serviço),
    // fica gravado e não se repete hoje; abrir a página de clima consulta de novo. "pendente" conta as
    // consultas que não chegaram ao fim porque a pessoa mudou de página antes: até 3 por dia.
    var tentativas = (dia && dia.pendente) || 0;
    if (tentativas >= 3) return;
    guardarDia(lugar, null, null, tentativas + 1);
    Promise.all([buscarUv(lugar).catch(function () { return null; }), buscarAr(lugar).catch(function () { return null; })])
      .then(function (r) {
        var t = textoAviso(lugar, guardarDia(lugar, r[0], r[1]));
        if (t) mostrarAviso(t);
      }).catch(function () {});
  }

  window.PSClima = {
    CONFIG: CONFIG, CHAVE_CIDADE: CHAVE_CIDADE, CHAVE_DIA: CHAVE_DIA, CHAVE_FECHADO: CHAVE_FECHADO,
    UV_AVISO: UV_AVISO, AR_AVISO: AR_AVISO, FAIXAS_AR: FAIXAS_AR,
    url: url, faixaAr: faixaAr, lerCidade: lerCidade, esquecer: esquecer,
    buscarAr: buscarAr, buscarUv: buscarUv, lerDia: lerDia, guardarDia: guardarDia, textoAviso: textoAviso
  };

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", aviso);
  else aviso();
})();
