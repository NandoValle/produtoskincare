/*
 * Ferramentas WebMCP do Produto Skincare.
 *
 * WebMCP deixa um agente de IA no navegador usar o site por "ferramentas" com nome,
 * descrição e parâmetros, em vez de clicar na tela.
 *   Especificação (rascunho do W3C Web Machine Learning CG, 02/11/2026):
 *     https://webmachinelearning.github.io/webmcp/
 *   Guia do Chrome: https://developer.chrome.com/docs/ai/webmcp/imperative-api
 *
 * Todas as ferramentas daqui só LEEM arquivos públicos do site (produtos.json, quiz.json,
 * rotinas/rotinas.json). Nenhuma compra, cadastra, envia ou grava nada.
 * A quarta ferramenta, "montar_rotina", é o formulário "Já sabe seu tipo de pele?" da página
 * inicial (API declarativa: atributos toolname/tooldescription no <form>).
 *
 * Sem WebMCP no navegador, este script não faz nada e o site segue igual. O caminho
 * manual é o mesmo formulário da página inicial e o /provador/.
 */
(function () {
  "use strict";

  // Detecção de recurso: só segue em contexto seguro e com document.modelContext.registerTool.
  if (!window.isSecureContext || !("modelContext" in document)) return;
  var mc = document.modelContext;
  if (!mc || typeof mc.registerTool !== "function") return;

  var SITE = location.origin;
  var TIPOS = ["oleosa", "seca", "mista", "normal"];
  var TIPOS_BUSCA = TIPOS.concat("sensivel");
  var PREOCUPACOES = ["acne", "manchas", "poros", "idade", "desidratacao"];
  var PASSOS = ["limpeza", "tratamento", "hidratacao", "protetor"];
  var CONDICOES = ["acne", "anti-age", "melasma", "rosacea"];
  var FAIXAS = ["economica", "media", "premium"];
  var AVISO = "Preços conferidos na data indicada; podem ter mudado na loja. Os links de loja são de " +
    "afiliado: o site pode receber comissão, sem custo extra para quem compra. Sugestão cosmética, " +
    "não é diagnóstico médico: em caso de acne intensa, lesões, dor ou irritação persistente, procure um dermatologista.";

  // ---------- leitura dos arquivos (uma vez por página), com cancelamento ----------
  var cache = {};

  function cancelado(sinal) {
    return sinal && sinal.reason ? sinal.reason : new DOMException("Execução cancelada.", "AbortError");
  }

  // Rejeita a promessa se o agente ou a pessoa cancelar (AbortSignal de options.signal).
  function comCancelamento(promessa, sinal) {
    if (!sinal) return promessa;
    if (sinal.aborted) return Promise.reject(cancelado(sinal));
    return new Promise(function (resolver, rejeitar) {
      function aoCancelar() { rejeitar(cancelado(sinal)); }
      sinal.addEventListener("abort", aoCancelar, { once: true });
      promessa.then(function (valor) {
        sinal.removeEventListener("abort", aoCancelar);
        resolver(valor);
      }, function (erro) {
        sinal.removeEventListener("abort", aoCancelar);
        rejeitar(erro);
      });
    });
  }

  function carregar(caminho, sinal) {
    if (!cache[caminho]) {
      cache[caminho] = fetch(caminho, { credentials: "same-origin" }).then(function (r) {
        if (!r.ok) throw new Error("Não foi possível ler " + caminho + " (HTTP " + r.status + ").");
        return r.json();
      });
      cache[caminho].catch(function () { delete cache[caminho]; });
    }
    return comCancelamento(cache[caminho], sinal);
  }

  // ---------- utilidades ----------
  function normalizar(texto) {
    return String(texto || "").normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();
  }

  function conferirOpcao(nome, valor, opcoes) {
    if (valor === undefined || valor === null || valor === "") return undefined;
    if (opcoes.indexOf(valor) === -1) {
      throw new TypeError("Valor inválido para " + nome + ": use " + opcoes.join(", ") + ".");
    }
    return valor;
  }

  function sinalDe(opcoes) { return opcoes && opcoes.signal; }

  function pagina(caminho) { return SITE + caminho; }

  function resumoProduto(p) {
    return {
      id: p.id,
      nome: p.nome,
      marca: p.marca,
      passo: p.passo,
      periodo: p.periodo,
      tipos_de_pele: p.tipos,
      preocupacoes: p.conc,
      ativos: p.ativos,
      preco_brl: typeof p.preco === "number" ? p.preco : null,
      preco_conferido_em: p.preco_em || null,
      avaliacao: p.avaliacao,
      num_avaliacoes: p.num_avaliacoes,
      loja: p.plataforma,
      link_loja: p.link,
      pagina: pagina("/produtos/" + p.id + "/"),
      por_que: p.porque
    };
  }

  // ---------- ferramentas ----------
  var buscarProdutos = {
    name: "buscar_produtos",
    title: "Buscar produtos de skincare",
    description: "Busca no catálogo de produtos de skincare do Produto Skincare (produtos vendidos no Brasil, com preço conferido em loja e data da conferência). Filtra por texto livre (nome, marca ou ativo, ex.: \"niacinamida\"), tipo de pele, preocupação, passo da rotina e preço máximo em reais. Devolve os mais bem avaliados primeiro, com link da página do produto e link da loja (afiliado). Só leitura: não compra nem adiciona nada ao carrinho.",
    inputSchema: {
      type: "object",
      properties: {
        termo: { type: "string", maxLength: 80, description: "Texto livre: nome, marca ou ativo (ex.: \"vitamina C\", \"CeraVe\"). Opcional." },
        tipo_pele: { type: "string", enum: TIPOS_BUSCA, description: "Tipo de pele: oleosa, seca, mista, normal ou sensivel. Opcional." },
        preocupacao: { type: "string", enum: PREOCUPACOES, description: "Preocupação: acne, manchas, poros, idade (sinais de idade) ou desidratacao. Opcional." },
        passo: { type: "string", enum: PASSOS, description: "Passo da rotina: limpeza, tratamento, hidratacao ou protetor (protetor solar). Opcional." },
        preco_max: { type: "number", minimum: 1, description: "Preço máximo por produto, em reais. Opcional." },
        limite: { type: "integer", minimum: 1, maximum: 10, default: 5, description: "Quantos produtos devolver (1 a 10, padrão 5)." }
      },
      additionalProperties: false
    },
    annotations: { readOnlyHint: true },
    execute: function (args, opcoes) {
      args = args || {};
      var tipo = conferirOpcao("tipo_pele", args.tipo_pele, TIPOS_BUSCA);
      var conc = conferirOpcao("preocupacao", args.preocupacao, PREOCUPACOES);
      var passo = conferirOpcao("passo", args.passo, PASSOS);
      var teto = typeof args.preco_max === "number" && args.preco_max > 0 ? args.preco_max : Infinity;
      var limite = Math.min(Math.max(parseInt(args.limite, 10) || 5, 1), 10);
      var palavras = normalizar(args.termo).split(/\s+/).filter(Boolean);
      return carregar("/produtos.json", sinalDe(opcoes)).then(function (dados) {
        var achados = dados.produtos.filter(function (p) {
          var tipos = p.tipos || [];
          if (tipo && tipos.indexOf(tipo) === -1 && tipos.indexOf("todos") === -1) return false;
          if (tipo && (p.evitar || []).indexOf(tipo) !== -1) return false;
          if (conc && (p.conc || []).indexOf(conc) === -1) return false;
          if (passo && p.passo !== passo) return false;
          if (teto !== Infinity && !(typeof p.preco === "number" && p.preco <= teto)) return false;
          if (palavras.length) {
            var texto = normalizar([p.nome, p.marca, p.passo, (p.ativos || []).join(" "), p.porque].join(" "));
            return palavras.every(function (w) { return texto.indexOf(w) !== -1; });
          }
          return true;
        }).sort(function (a, b) {
          return (b.avaliacao || 0) - (a.avaliacao || 0) || (b.num_avaliacoes || 0) - (a.num_avaliacoes || 0);
        });
        return JSON.stringify({
          encontrados: achados.length,
          mostrando: Math.min(achados.length, limite),
          catalogo_atualizado_em: dados.atualizado_em,
          produtos: achados.slice(0, limite).map(resumoProduto),
          todos_os_produtos: pagina("/produtos/"),
          aviso: AVISO
        });
      });
    }
  };

  var explicarTipo = {
    name: "explicar_tipo_de_pele",
    title: "Explicar um tipo de pele",
    description: "Explica um tipo de pele (oleosa, seca, mista ou normal) com os cuidados do dia a dia recomendados pelo Produto Skincare, e devolve os links do guia desse tipo e do provador já com a rotina. Use quando a pessoa já sabe o tipo de pele. Para descobrir o tipo, mande a pessoa ao provador (quiz ou selfie). Só leitura.",
    inputSchema: {
      type: "object",
      properties: {
        tipo_pele: { type: "string", enum: TIPOS, description: "Tipo de pele: oleosa, seca, mista ou normal." }
      },
      required: ["tipo_pele"],
      additionalProperties: false
    },
    annotations: { readOnlyHint: true },
    execute: function (args, opcoes) {
      var tipo = conferirOpcao("tipo_pele", (args || {}).tipo_pele, TIPOS);
      if (!tipo) throw new TypeError("Informe tipo_pele: " + TIPOS.join(", ") + ".");
      return carregar("/quiz.json", sinalDe(opcoes)).then(function (quiz) {
        var r = quiz.resultado || {};
        return JSON.stringify({
          tipo_pele: tipo,
          explicacao: (r.explicacoes || {})[tipo] || null,
          dicas: (r.dicas || {})[tipo] || [],
          guia: pagina("/pele/" + tipo + "/"),
          rotina_no_provador: pagina("/provador/?tipo=" + tipo),
          descobrir_o_tipo: pagina("/provador/"),
          aviso: "Estimativa cosmética, não é diagnóstico médico."
        });
      });
    }
  };

  var verRotina = {
    name: "ver_rotina_por_condicao",
    title: "Ver rotina por condição e faixa de preço",
    description: "Devolve a rotina de skincare de manhã e de noite que o Produto Skincare montou para uma condição (acne, anti-age, melasma ou rosacea) numa faixa de preço (economica, media ou premium): produto de cada passo com preço e link, ativos com nível de evidência, cuidados e quando procurar um dermatologista. Só leitura.",
    inputSchema: {
      type: "object",
      properties: {
        condicao: { type: "string", enum: CONDICOES, description: "Condição: acne, anti-age (sinais de idade), melasma ou rosacea." },
        faixa: { type: "string", enum: FAIXAS, default: "economica", description: "Faixa de preço: economica, media (intermediária) ou premium. Padrão: economica." }
      },
      required: ["condicao"],
      additionalProperties: false
    },
    annotations: { readOnlyHint: true },
    execute: function (args, opcoes) {
      args = args || {};
      var condicao = conferirOpcao("condicao", args.condicao, CONDICOES);
      if (!condicao) throw new TypeError("Informe condicao: " + CONDICOES.join(", ") + ".");
      var faixa = conferirOpcao("faixa", args.faixa, FAIXAS) || "economica";
      var sinal = sinalDe(opcoes);
      return Promise.all([carregar("/rotinas/rotinas.json", sinal), carregar("/produtos.json", sinal)]).then(function (res) {
        var rotinas = res[0], porId = {};
        res[1].produtos.forEach(function (p) { porId[p.id] = p; });
        var r = rotinas.rotinas[condicao];
        var extras = rotinas.extras || {};
        function item(i) {
          var saida = { passo: i.passo };
          var p = i.id && porId[i.id];
          var x = i.extra && extras[i.extra];
          if (p) {
            saida.produto = p.nome;
            saida.marca = p.marca;
            saida.preco_brl = typeof p.preco === "number" ? p.preco : null;
            saida.preco_conferido_em = p.preco_em || null;
            saida.loja = p.plataforma;
            saida.link_loja = p.link;
            saida.pagina = pagina("/produtos/" + p.id + "/");
          } else if (x) {
            saida.produto = x.nome;
            saida.marca = x.marca;
            saida.preco_brl = null;
            saida.preco_texto = "ver na loja";
            saida.loja = x.plataforma;
            saida.link_loja = x.link;
          }
          if (i.nota) saida.nota = i.nota;
          if (i.repetido) saida.mesmo_produto_da_manha = true;
          return saida;
        }
        var f = r.faixas[faixa];
        return JSON.stringify({
          condicao: r.titulo,
          faixa: (rotinas.faixas[faixa] || {}).nome || faixa,
          resumo: r.resumo,
          manha: (f.manha || []).map(item),
          noite: (f.noite || []).map(item),
          ativos: r.ativos,
          cuidados: r.cuidados,
          quando_procurar_dermatologista: r.derma,
          pagina: pagina("/rotinas/" + condicao + "/"),
          guia_da_condicao: r.condicao ? pagina(r.condicao) : null,
          rotinas_atualizadas_em: rotinas.atualizado_em,
          aviso: AVISO
        });
      });
    }
  };

  var FERRAMENTAS = [buscarProdutos, explicarTipo, verRotina];

  // ---------- registro ----------
  // Cada registro recebe um AbortSignal: abortar remove as ferramentas (ex.: ao sair da página).
  var controle = null;

  function registrar() {
    if (controle && !controle.signal.aborted) return;
    controle = new AbortController();
    FERRAMENTAS.forEach(function (ferramenta) {
      try {
        Promise.resolve(mc.registerTool(ferramenta, { signal: controle.signal })).catch(function (erro) {
          if (window.console) console.warn("WebMCP: não registrou " + ferramenta.name, erro);
        });
      } catch (erro) {
        if (window.console) console.warn("WebMCP: não registrou " + ferramenta.name, erro);
      }
    });
  }

  window.addEventListener("pagehide", function () { if (controle) controle.abort(); });
  window.addEventListener("pageshow", function (e) { if (e.persisted) registrar(); });
  registrar();
})();
