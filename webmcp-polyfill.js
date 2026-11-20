/*
 * Polyfill de document.modelContext (WebMCP) do Produto Skincare.
 *
 * Para que serve: em navegadores SEM WebMCP nativo, as ferramentas do site (webmcp.js) não
 * tinham onde se registrar. Este arquivo cria document.modelContext com a mesma interface da
 * especificação, para que um agente ou extensão que rode na página consiga listar as
 * ferramentas (getTools) e executá-las (executeTool) pelo caminho padrão.
 *
 * O que ele NÃO faz:
 *   - não substitui a API nativa: se o navegador já tem document.modelContext, sai sem fazer nada;
 *   - não conversa com o agente embutido do navegador (isso só a API nativa faz);
 *   - não enxerga ferramentas de outros documentos (iframes): cobre só esta página;
 *   - não valida os argumentos contra o inputSchema: cada ferramenta valida os seus.
 *
 * Especificação seguida (rascunho do W3C Web Machine Learning CG, 09/11/2026):
 *   https://webmachinelearning.github.io/webmcp/
 * Para saber se é o polyfill: document.modelContext.isPolyfill === true.
 */
(function () {
  "use strict";

  if (!window.isSecureContext || "modelContext" in document) return;
  if (typeof EventTarget !== "function" || typeof AbortController !== "function") return;

  var NOME_VALIDO = /^[A-Za-z0-9_.\-]{1,128}$/;
  var registro = new Map(); // nome -> { ferramenta, entrada, saida }

  function falha(tipo, mensagem) {
    return Promise.reject(new DOMException(mensagem, tipo));
  }

  // Serializa o schema como a especificação pede: se não der para virar JSON, a promessa rejeita.
  function serializar(schema) {
    if (schema === undefined || schema === null) return undefined;
    var texto = JSON.stringify(schema);
    if (texto === undefined) throw new TypeError("O schema da ferramenta não é serializável em JSON.");
    return texto;
  }

  function evento(tipo, nomeDaFerramenta) {
    var e = new Event(tipo);
    if (nomeDaFerramenta !== undefined) {
      Object.defineProperty(e, "toolName", { value: nomeDaFerramenta, enumerable: true });
    }
    return e;
  }

  function Contexto() {
    var alvo = Reflect.construct(EventTarget, [], Contexto);
    var manipuladores = {};
    ["toolchange", "toolactivated", "toolcancel"].forEach(function (tipo) {
      Object.defineProperty(alvo, "on" + tipo, {
        enumerable: true,
        get: function () { return manipuladores[tipo] || null; },
        set: function (fn) {
          if (manipuladores[tipo]) alvo.removeEventListener(tipo, manipuladores[tipo]);
          manipuladores[tipo] = typeof fn === "function" ? fn : null;
          if (manipuladores[tipo]) alvo.addEventListener(tipo, manipuladores[tipo]);
        }
      });
    });
    return alvo;
  }
  Contexto.prototype = Object.create(EventTarget.prototype, {
    constructor: { value: Contexto, writable: true, configurable: true }
  });

  function avisarMudanca(contexto) {
    setTimeout(function () { contexto.dispatchEvent(evento("toolchange")); }, 0);
  }

  function remover(contexto, nome) {
    if (!registro.has(nome)) return;
    registro.delete(nome);
    avisarMudanca(contexto);
  }

  Contexto.prototype.registerTool = function (ferramenta, opcoes) {
    var contexto = this;
    if (!ferramenta || typeof ferramenta !== "object") {
      return Promise.reject(new TypeError("registerTool espera um objeto com name, description e execute."));
    }
    if (typeof ferramenta.execute !== "function") {
      return Promise.reject(new TypeError("A ferramenta precisa de uma função execute."));
    }
    var nome = String(ferramenta.name === undefined ? "" : ferramenta.name);
    var descricao = String(ferramenta.description === undefined ? "" : ferramenta.description);
    if (registro.has(nome)) return falha("InvalidStateError", "Já existe uma ferramenta registrada com o nome " + nome + ".");
    if (!NOME_VALIDO.test(nome)) return falha("InvalidStateError", "Nome de ferramenta inválido: use até 128 letras, números, _, - ou ponto.");
    if (descricao === "") return falha("InvalidStateError", "A descrição da ferramenta não pode ser vazia.");

    var entrada, saida;
    try {
      entrada = serializar(ferramenta.inputSchema);
      saida = serializar(ferramenta.outputSchema);
    } catch (erro) {
      return Promise.reject(erro);
    }

    var sinal = opcoes && opcoes.signal;
    if (sinal && sinal.aborted) return Promise.resolve(undefined);

    registro.set(nome, { ferramenta: ferramenta, nome: nome, descricao: descricao, entrada: entrada, saida: saida });
    if (sinal) sinal.addEventListener("abort", function () { remover(contexto, nome); }, { once: true });
    avisarMudanca(contexto);
    return Promise.resolve(undefined);
  };

  Contexto.prototype.getTools = function (opcoes) {
    var origens = opcoes && opcoes.fromOrigins;
    if (origens !== undefined && origens !== null) {
      try {
        Array.prototype.forEach.call(origens, function (origem) {
          var url = new URL(origem);
          var confiavel = url.protocol === "https:" || url.hostname === "localhost" || url.hostname === "127.0.0.1" || url.hostname === "[::1]";
          if (!confiavel) throw new DOMException("Origem não confiável em fromOrigins: " + origem, "SecurityError");
        });
      } catch (erro) {
        return Promise.reject(erro instanceof DOMException ? erro : new DOMException("Origem inválida em fromOrigins.", "SecurityError"));
      }
    }
    var lista = [];
    registro.forEach(function (item) {
      var f = item.ferramenta;
      var exposta = { name: item.nome, description: item.descricao, window: window, origin: location.origin };
      if (f.title !== undefined) exposta.title = String(f.title);
      if (item.entrada !== undefined) exposta.inputSchema = JSON.parse(item.entrada);
      if (item.saida !== undefined) exposta.outputSchema = JSON.parse(item.saida);
      var a = f.annotations || {};
      exposta.annotations = {
        readOnlyHint: a.readOnlyHint === true,
        untrustedContentHint: a.untrustedContentHint === true,
        consequentialHint: a.consequentialHint === true,
        debugging: a.debugging === true
      };
      lista.push(exposta);
    });
    return Promise.resolve(lista);
  };

  Contexto.prototype.executeTool = function (alvo, entrada, opcoes) {
    var contexto = this;
    var nome = alvo && typeof alvo === "object" ? alvo.name : alvo;
    var item = registro.get(String(nome));
    if (!item) return falha("NotFoundError", "Ferramenta não registrada nesta página: " + nome + ".");

    var argumentos = entrada === undefined || entrada === null ? {} : entrada;
    if (typeof argumentos === "string") {
      try { argumentos = JSON.parse(argumentos); }
      catch (erro) { return falha("DataError", "Os argumentos não são um JSON válido."); }
    }
    if (!argumentos || typeof argumentos !== "object" || Array.isArray(argumentos)) {
      return falha("DataError", "Os argumentos precisam ser um objeto JSON.");
    }

    var controle = new AbortController();
    var externo = opcoes && opcoes.signal;
    if (externo && externo.aborted) return Promise.reject(externo.reason || new DOMException("Execução cancelada.", "AbortError"));

    return new Promise(function (resolver, rejeitar) {
      var encerrado = false;
      function aoCancelar() {
        if (encerrado) return;
        encerrado = true;
        controle.abort(externo.reason);
        contexto.dispatchEvent(evento("toolcancel", item.nome));
        rejeitar(externo.reason || new DOMException("Execução cancelada.", "AbortError"));
      }
      if (externo) externo.addEventListener("abort", aoCancelar, { once: true });
      function fechar() {
        encerrado = true;
        if (externo) externo.removeEventListener("abort", aoCancelar);
      }

      contexto.dispatchEvent(evento("toolactivated", item.nome));
      var resultado;
      try {
        resultado = item.ferramenta.execute(argumentos, { signal: controle.signal });
      } catch (erro) {
        fechar();
        rejeitar(erro);
        return;
      }
      Promise.resolve(resultado).then(function (valor) {
        if (encerrado) return;
        fechar();
        if (typeof valor === "string") { resolver(valor); return; }
        var texto;
        try { texto = JSON.stringify(valor === undefined ? null : valor); }
        catch (erro) { rejeitar(erro); return; }
        resolver(texto);
      }, function (erro) {
        if (encerrado) return;
        fechar();
        rejeitar(erro);
      });
    });
  };

  var contexto = new Contexto();
  Object.defineProperty(contexto, "isPolyfill", { value: true, enumerable: false });
  Object.defineProperty(document, "modelContext", { value: contexto, enumerable: true, configurable: true });
})();
