/* Regras de ativos do Produto Skincare: fonte única e versionada.
 *
 * Usada por:
 *   - /provador/ : contraindicações (pele sensível, retinol alto, ácidos fortes, fragrância)
 *                  e avisos de combinação na rotina sugerida;
 *   - /ferramentas/ingredientes/ : verificador de combinações (ok / horários diferentes / não combine).
 *
 * Nada aqui é decidido "na hora": cada resultado sai de uma regra escrita abaixo.
 * Para mudar uma regra:
 *   1. edite a regra;
 *   2. suba VERSAO e registre a mudança em HISTORICO;
 *   3. rode os testes: node _scripts/testar_regras.js
 *
 * Base: orientações de uso comuns em dermatologia cosmética, sem citação de estudo
 * específico. Antes de publicar mudanças, revise com farmacêutico(a) ou dermatologista.
 * Informativo: não substitui consulta médica.
 */
(function (raiz) {
  "use strict";

  var VERSAO = "1.0.0";
  var HISTORICO = [
    { versao: "1.0.0", data: "2026-11-05", nota: "Primeira versão: ativos reconhecidos, combinações (retinoide × AHA/BHA, × vitamina C, × peróxido de benzoíla, ácidos × pele irritada e outras) e contraindicações por perfil." }
  ];

  /* ===== ATIVOS RECONHECIDOS =====
   * termos: sem acento e em minúsculas (o texto é normalizado do mesmo jeito).
   * Termo terminado em "*" casa como prefixo (ex.: "adapalen*" pega adapaleno e adapalene);
   * os outros só casam como palavra inteira.
   * Ácido cítrico fica de fora de propósito: nas listas INCI ele costuma ser só ajuste de pH.
   */
  var ATIVOS = [
    { id: "retinol", nome: "Retinol", classe: "retinoide", termos: ["retinol"] },
    { id: "retinal", nome: "Retinal (retinaldeído)", classe: "retinoide", termos: ["retinal*", "retinaldeido"] },
    { id: "retinila", nome: "Éster de retinila (palmitato, acetato)", classe: "retinoide", termos: ["retinyl*", "retinila"] },
    { id: "hpr", nome: "HPR (retinoato de hidroxipinacolona)", classe: "retinoide", termos: ["hydroxypinacolone retinoate", "retinoato de hidroxipinacolona", "granactive"] },
    { id: "tretinoina", nome: "Tretinoína (ácido retinoico)", classe: "retinoide", termos: ["tretinoin*", "acido retinoico", "retinoic acid"] },
    { id: "adapaleno", nome: "Adapaleno", classe: "retinoide", termos: ["adapalen*"] },
    { id: "tazaroteno", nome: "Tazaroteno", classe: "retinoide", termos: ["tazaroten*"] },
    { id: "trifaroteno", nome: "Trifaroteno", classe: "retinoide", termos: ["trifaroten*"] },

    { id: "glicolico", nome: "Ácido glicólico", classe: "aha", termos: ["glycolic*", "acido glicolico", "glicolico"] },
    { id: "latico", nome: "Ácido lático", classe: "aha", termos: ["lactic acid", "acido latico", "acido lactico"] },
    { id: "mandelico", nome: "Ácido mandélico", classe: "aha", termos: ["mandelic*", "acido mandelico", "mandelico"] },
    { id: "aha", nome: "AHA (alfa-hidroxiácido)", classe: "aha", termos: ["aha", "ahas", "alfa hidroxiacido*", "alpha hydroxy*"] },

    { id: "salicilico", nome: "Ácido salicílico (BHA)", classe: "bha", termos: ["salicylic*", "acido salicilico", "salicilico", "bha"] },
    { id: "lha", nome: "LHA (ácido capriloil salicílico)", classe: "bha", termos: ["capryloyl salicylic*", "lha"] },

    { id: "vitc", nome: "Vitamina C", classe: "vitc", termos: ["vitamina c", "vitamin c", "vit c", "ascorb*"] },
    { id: "bpo", nome: "Peróxido de benzoíla", classe: "bpo", termos: ["benzoyl peroxide", "peroxido de benzoila", "bpo"] },

    { id: "niacinamida", nome: "Niacinamida", classe: "niacinamida", termos: ["niacinamid*", "nicotinamid*", "vitamina b3"] },
    { id: "azelaico", nome: "Ácido azelaico", classe: "azelaico", termos: ["azelaic*", "acido azelaico", "azelaico"] },
    { id: "tranexamico", nome: "Ácido tranexâmico", classe: "clareador", termos: ["tranexamic*", "acido tranexamico", "tranexamico"] },
    { id: "arbutina", nome: "Alfa-arbutina", classe: "clareador", termos: ["arbutin*", "arbutina"] },

    { id: "hialuronico", nome: "Ácido hialurônico", classe: "hidratante", termos: ["hyaluron*", "hialuron*"] },
    { id: "ceramidas", nome: "Ceramidas", classe: "hidratante", termos: ["ceramid*"] },
    { id: "pantenol", nome: "Pantenol", classe: "hidratante", termos: ["panthenol", "pantenol", "d pantenol", "vitamina b5"] },
    { id: "centella", nome: "Centella asiática", classe: "hidratante", termos: ["centella", "madecassos*", "cica"] },
    { id: "aveia", nome: "Aveia coloidal", classe: "hidratante", termos: ["aveia coloidal", "colloidal oat*", "avena sativa"] },
    { id: "glicerina", nome: "Glicerina", classe: "hidratante", termos: ["glycerin", "glicerina"] },
    { id: "zinco", nome: "Zinco (PCA de zinco)", classe: "hidratante", termos: ["zinc pca", "pca de zinco", "zinco"] },
    { id: "ferulico", nome: "Ácido ferúlico", classe: "antioxidante", termos: ["ferulic*", "acido ferulico", "ferulico"] },
    { id: "vitamina-e", nome: "Vitamina E", classe: "antioxidante", termos: ["tocopher*", "vitamina e"] },
    { id: "peptideos", nome: "Peptídeos", classe: "antioxidante", termos: ["peptid*", "peptide*", "matrixyl", "argireline"] },
    { id: "bakuchiol", nome: "Bakuchiol", classe: "antioxidante", termos: ["bakuchiol"] },
    { id: "filtro", nome: "Filtro solar", classe: "filtro", termos: ["filtro*", "fps", "spf", "protetor solar", "sunscreen"] }
  ];

  /* Estado da pele (não é ativo, mas entra no verificador como item). */
  var ESTADOS = {
    irritada: { id: "irritada", nome: "Pele irritada agora (ardendo, vermelha ou descamando)", classe: "irritada" }
  };

  var CLASSES = {
    retinoide: "retinoide", aha: "ácido esfoliante (AHA)", bha: "ácido salicílico (BHA)", vitc: "vitamina C",
    bpo: "peróxido de benzoíla", niacinamida: "niacinamida", azelaico: "ácido azelaico", clareador: "clareador",
    hidratante: "hidratante ou calmante", antioxidante: "antioxidante", filtro: "filtro solar", irritada: "pele irritada"
  };

  /* Classes que combinam com as outras: sem regra própria, o par sai "ok" com este motivo. */
  var NEUTRAS = {
    hidratante: "Hidratantes e calmantes (ácido hialurônico, ceramidas, pantenol, centella) combinam com os outros ativos e ajudam a pele a tolerá-los.",
    antioxidante: "Antioxidantes como vitamina E, ácido ferúlico e peptídeos costumam combinar com os outros ativos.",
    filtro: "Protetor solar combina com tudo e é indispensável com qualquer ativo.",
    clareador: "Clareadores suaves como ácido tranexâmico e alfa-arbutina costumam combinar com os outros ativos."
  };

  /* ===== COMBINAÇÕES =====
   * resultado: "ok" (pode usar junto) · "horarios" (use em horários diferentes) · "nao" (não combine)
   * sensivel: resultado que vale para pele sensível, quando é mais rígido (com sensivelMotivo).
   * nota: observação curta mostrada junto (exceções, receita).
   */
  var COMBINACOES = [
    { id: "retinoide-aha", a: "retinoide", b: "aha", resultado: "horarios",
      motivo: "Juntos na mesma aplicação, irritam e descamam bem mais. Use em noites alternadas.",
      sensivel: "nao", sensivelMotivo: "Em pele sensível, não junte os dois na rotina no começo: fique com um deles e observe a pele por algumas semanas." },
    { id: "retinoide-bha", a: "retinoide", b: "bha", resultado: "horarios",
      motivo: "Juntos na mesma aplicação, ressecam e irritam bem mais. Use em noites alternadas ou o ácido salicílico de manhã.",
      sensivel: "nao", sensivelMotivo: "Em pele sensível, não junte os dois na rotina no começo: fique com um deles e observe a pele por algumas semanas." },
    { id: "retinoide-vitc", a: "retinoide", b: "vitc", resultado: "horarios",
      motivo: "Os dois podem irritar. Use a vitamina C de manhã, antes do protetor, e o retinoide à noite." },
    { id: "bpo-retinoide", a: "bpo", b: "retinoide", resultado: "horarios",
      motivo: "O peróxido de benzoíla é oxidante e pode degradar o retinoide (principalmente a tretinoína), e os dois ressecam. Peróxido de manhã, retinoide à noite.",
      nota: "Existe medicamento que já junta adapaleno e peróxido de benzoíla: nesse caso, siga a receita.",
      sensivel: "nao", sensivelMotivo: "Em pele sensível, os dois juntos na rotina costumam ser demais. Use um deles, de preferência com orientação de um dermatologista." },
    { id: "aha-bha", a: "aha", b: "bha", resultado: "horarios",
      motivo: "Dois esfoliantes juntos aumentam a irritação. Alterne os dias, a não ser que venham juntos num produto que você já tolera.",
      sensivel: "nao", sensivelMotivo: "Em pele sensível, escolha um esfoliante só." },
    { id: "vitc-aha", a: "vitc", b: "aha", resultado: "horarios",
      motivo: "Vitamina C pura e ácidos esfoliantes têm pH baixo: juntos ardem mais. Vitamina C de manhã, ácido à noite." },
    { id: "vitc-bha", a: "vitc", b: "bha", resultado: "horarios",
      motivo: "Vitamina C pura e ácido salicílico têm pH baixo: juntos ardem mais. Vitamina C de manhã, ácido à noite." },
    { id: "bpo-vitc", a: "bpo", b: "vitc", resultado: "horarios",
      motivo: "O peróxido de benzoíla pode oxidar a vitamina C e tirar o efeito dela. Use em horários diferentes." },
    { id: "bpo-aha", a: "bpo", b: "aha", resultado: "horarios",
      motivo: "Os dois ressecam e irritam. Se usar ambos, separe manhã e noite." },
    { id: "bpo-bha", a: "bpo", b: "bha", resultado: "horarios",
      motivo: "Os dois ressecam e irritam. Se usar ambos, separe manhã e noite." },
    { id: "retinoide-retinoide", a: "retinoide", b: "retinoide", resultado: "nao",
      motivo: "Dois retinoides somam irritação sem ganho claro. Escolha um só." },
    { id: "vitc-niacinamida", a: "vitc", b: "niacinamida", resultado: "ok",
      motivo: "Pode usar junto. A ideia de que um anula o outro é um mito comum; se arder, separe manhã e noite." },
    { id: "retinoide-niacinamida", a: "retinoide", b: "niacinamida", resultado: "ok",
      motivo: "Combinação comum e costuma ser bem tolerada." },
    { id: "irritada-aha", a: "irritada", b: "aha", resultado: "nao",
      motivo: "Com a pele irritada, pare os ácidos esfoliantes até ela se recuperar. Fique com limpeza suave, hidratante e protetor; se não melhorar em alguns dias, procure um dermatologista." },
    { id: "irritada-bha", a: "irritada", b: "bha", resultado: "nao",
      motivo: "Com a pele irritada, pare o ácido salicílico até ela se recuperar. Fique com limpeza suave, hidratante e protetor; se não melhorar em alguns dias, procure um dermatologista." },
    { id: "irritada-retinoide", a: "irritada", b: "retinoide", resultado: "nao",
      motivo: "Com a pele irritada, pause o retinoide até ela se recuperar. Se ele for receitado, avise quem receitou." },
    { id: "irritada-bpo", a: "irritada", b: "bpo", resultado: "nao",
      motivo: "Com a pele irritada, pause o peróxido de benzoíla até ela se recuperar." },
    { id: "irritada-vitc", a: "irritada", b: "vitc", resultado: "nao",
      motivo: "Vitamina C, principalmente a pura, costuma arder na pele irritada. Pause até ela se recuperar." }
  ];

  /* ===== CONTRAINDICAÇÕES POR PERFIL (provador) =====
   * acao "remover": o produto sai das sugestões · "avisar": fica, com aviso.
   * quando: "sensivel" (só para pele sensível) ou "todos".
   * forte: true/false compara a concentração com LIMITE_FORTE (acima do limite = forte).
   * minimo: concentração mínima (%) para a regra valer.
   * fragrancia: true (tem perfume) / null (não sabemos).
   */
  var LIMITE_FORTE = { aha: 10, bha: 2 }; // % acima disso = "ácido forte" para uso em casa

  var PERFIL = [
    { id: "sens-retinoide", quando: "sensivel", classes: ["retinoide"], acao: "remover",
      motivo: "Retinoides (como o retinol) costumam irritar pele sensível e ficaram de fora. Se quiser usar, converse com um dermatologista e comece devagar." },
    { id: "sens-acido-forte", quando: "sensivel", classes: ["aha", "bha"], forte: true, acao: "remover",
      motivo: "Ácido esfoliante em concentração alta ficou de fora: em pele sensível, o risco de irritação é grande." },
    { id: "sens-acido", quando: "sensivel", classes: ["aha", "bha"], forte: false, acao: "avisar",
      curto: "Pele sensível: comece 1 a 2 noites por semana",
      motivo: "Ácido esfoliante em pele sensível: comece 1 a 2 noites por semana e pare se arder ou avermelhar." },
    { id: "sens-bpo", quando: "sensivel", classes: ["bpo"], acao: "avisar",
      curto: "Pele sensível: pode ressecar e irritar",
      motivo: "Peróxido de benzoíla resseca e pode irritar: em pele sensível, prefira a menor concentração e aplique só nas espinhas." },
    { id: "sens-vitc", quando: "sensivel", classes: ["vitc"], acao: "avisar",
      curto: "Pele sensível: pode arder, faça teste antes",
      motivo: "Vitamina C pode arder em pele sensível, sobretudo a forma pura (ácido ascórbico). Faça um teste numa área pequena antes." },
    { id: "sens-fragrancia", quando: "sensivel", fragrancia: true, acao: "remover",
      motivo: "Produto com fragrância ficou de fora: perfume é uma causa frequente de reação em pele sensível." },
    { id: "sens-fragrancia-desconhecida", quando: "sensivel", fragrancia: null, acao: "avisar",
      motivo: "Ainda não conferimos se este produto tem fragrância. Para pele sensível, prefira os \"sem fragrância\" e evite \"parfum\", \"fragrance\" e óleos essenciais na lista de ingredientes." },
    { id: "retinoide-alto", quando: "todos", classes: ["retinoide"], minimo: 0.5, acao: "avisar",
      curto: "Concentração mais alta de retinoide",
      motivo: "Retinoide em concentração mais alta (a partir de 0,5%). Se é o seu primeiro, prefira 0,3% ou menos e comece 2 noites por semana." },
    { id: "acido-forte", quando: "todos", classes: ["aha", "bha"], forte: true, acao: "avisar",
      curto: "Ácido em concentração alta",
      motivo: "Ácido esfoliante em concentração alta para uso em casa: use poucas vezes por semana, à noite, e protetor solar todos os dias." }
  ];

  var ROTULOS = { ok: "Pode usar junto", horarios: "Use em horários diferentes", nao: "Não combine" };
  var PESO = { ok: 0, horarios: 1, nao: 2 };

  /* ===== FUNÇÕES ===== */
  function normalizar(texto) {
    return String(texto == null ? "" : texto).normalize("NFD").replace(/[̀-ͯ]/g, "")
      .toLowerCase().replace(/[^a-z0-9%.,]+/g, " ").replace(/\s+/g, " ").trim();
  }

  function fonteDoTermo(termo) {
    var prefixo = termo.slice(-1) === "*";
    var base = (prefixo ? termo.slice(0, -1) : termo).replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    return { base: base, prefixo: prefixo };
  }
  var CACHE_RE = {};
  function reTermo(termo) {
    if (!CACHE_RE[termo]) {
      var f = fonteDoTermo(termo);
      CACHE_RE[termo] = new RegExp("\\b" + f.base + (f.prefixo ? "[a-z0-9]*" : "\\b"));
    }
    return CACHE_RE[termo];
  }

  /* Ativos encontrados num texto (lista de ingredientes, nomes separados por vírgula etc.). */
  function detectar(texto) {
    var t = normalizar(texto);
    return ATIVOS.filter(function (a) { return a.termos.some(function (termo) { return reTermo(termo).test(t); }); });
  }

  /* Maior concentração (%) escrita logo depois de um ativo da classe, ex.: "retinol 0,3%". */
  function concentracao(texto, classe) {
    var t = normalizar(texto), maior = null;
    ATIVOS.forEach(function (a) {
      if (a.classe !== classe) return;
      a.termos.forEach(function (termo) {
        var f = fonteDoTermo(termo);
        // aceita a palavra "acid"/"ácido" entre o nome e o número (INCI: "Glycolic Acid 7.5%")
        var re = new RegExp("\\b" + f.base + (f.prefixo ? "[a-z]*" : "") + "(?:\\s+acid[a-z]*)?\\s*(\\d+(?:[.,]\\d+)?)\\s*%", "g");
        var m;
        while ((m = re.exec(t))) {
          var n = parseFloat(m[1].replace(",", "."));
          if (isFinite(n) && (maior === null || n > maior)) maior = n;
        }
      });
    });
    return maior;
  }

  function regraDoPar(ca, cb) {
    for (var i = 0; i < COMBINACOES.length; i++) {
      var r = COMBINACOES[i];
      if ((r.a === ca && r.b === cb) || (r.a === cb && r.b === ca)) return r;
    }
    return null;
  }

  /* Resultado para dois itens (ativos de ATIVOS ou ESTADOS). ctx.sensivel deixa as regras mais rígidas. */
  function avaliarPar(x, y, ctx) {
    ctx = ctx || {};
    var r = regraDoPar(x.classe, y.classe);
    if (r) {
      var sens = !!(ctx.sensivel && r.sensivel && PESO[r.sensivel] > PESO[r.resultado]);
      return {
        resultado: sens ? r.sensivel : r.resultado,
        motivo: sens ? r.sensivelMotivo : r.motivo,
        nota: r.nota || "",
        regra: r.id,
        porSensibilidade: sens
      };
    }
    var neutra = NEUTRAS[x.classe] ? x.classe : NEUTRAS[y.classe] ? y.classe : null;
    if (neutra) return { resultado: "ok", motivo: NEUTRAS[neutra], nota: "", regra: "neutra-" + neutra, porSensibilidade: false };
    return {
      resultado: "ok",
      motivo: "Nenhum conflito registrado para este par nas regras v" + VERSAO + ". Mesmo assim, introduza um ativo novo por vez.",
      nota: "", regra: "sem-regra", porSensibilidade: false
    };
  }

  /* Todos os pares de uma lista de itens. Itens iguais (mesmo id) não formam par. */
  function avaliar(itens, ctx) {
    var pares = [], pior = "ok";
    for (var i = 0; i < itens.length; i++) {
      for (var j = i + 1; j < itens.length; j++) {
        if (itens[i].id === itens[j].id) continue;
        var r = avaliarPar(itens[i], itens[j], ctx);
        r.a = itens[i]; r.b = itens[j];
        pares.push(r);
        if (PESO[r.resultado] > PESO[pior]) pior = r.resultado;
      }
    }
    pares.sort(function (p, q) { return PESO[q.resultado] - PESO[p.resultado]; });
    return { resultado: pior, pares: pares, versao: VERSAO };
  }

  /* Fragrância: true / false / null (não sabemos). Usa o campo "fragrancia" do produto, se
     houver; senão, só reconhece "sem fragrância" / "sem perfume" escrito na descrição. */
  function fragrancia(produto) {
    if (produto && typeof produto.fragrancia === "boolean") return produto.fragrancia;
    var t = normalizar((produto && produto.porque) || "");
    return /\bsem (fragrancia|perfume)\b|\bfragrance free\b/.test(t) ? false : null;
  }

  function textoDoProduto(produto) {
    return [produto.nome, (produto.ativos || []).join(", ")].join(" ");
  }

  /* Contraindicações de um produto do catálogo para um perfil ({ sensivel }). */
  function contraindicacoes(produto, perfil) {
    perfil = perfil || {};
    var texto = textoDoProduto(produto);
    var classes = detectar(texto).map(function (a) { return a.classe; });
    var frag = fragrancia(produto);
    var out = [];
    PERFIL.forEach(function (r) {
      if (r.quando === "sensivel" && !perfil.sensivel) return;
      if ("fragrancia" in r) {
        if (frag === r.fragrancia) out.push(r);
        return;
      }
      var achadas = r.classes.filter(function (c) { return classes.indexOf(c) >= 0; });
      if (!achadas.length) return;
      if ("forte" in r) {
        var forte = achadas.some(function (c) {
          var n = concentracao(texto, c);
          return n !== null && LIMITE_FORTE[c] !== undefined && n > LIMITE_FORTE[c];
        });
        if (forte !== r.forte) return;
      }
      if ("minimo" in r) {
        var maior = Math.max.apply(null, achadas.map(function (c) { var n = concentracao(texto, c); return n === null ? -1 : n; }));
        if (maior < r.minimo) return;
      }
      out.push(r);
    });
    // Se o produto sai da rotina, os avisos dele não interessam mais.
    if (out.some(function (r) { return r.acao === "remover"; })) out = out.filter(function (r) { return r.acao === "remover"; });
    return out.map(function (r) { return { regra: r.id, acao: r.acao, motivo: r.motivo, curto: r.curto || "" }; });
  }

  var API = {
    VERSAO: VERSAO, HISTORICO: HISTORICO, ATIVOS: ATIVOS, ESTADOS: ESTADOS, CLASSES: CLASSES,
    COMBINACOES: COMBINACOES, PERFIL: PERFIL, LIMITE_FORTE: LIMITE_FORTE, ROTULOS: ROTULOS,
    normalizar: normalizar, detectar: detectar, concentracao: concentracao, fragrancia: fragrancia,
    avaliarPar: avaliarPar, avaliar: avaliar, contraindicacoes: contraindicacoes, textoDoProduto: textoDoProduto
  };
  if (typeof module === "object" && module.exports) module.exports = API;
  else raiz.PSRegras = API;
})(typeof window !== "undefined" ? window : this);
