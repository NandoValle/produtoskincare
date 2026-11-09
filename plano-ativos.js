/* Planos de introdução de ativos do Modo 12 semanas (/ferramentas/12-semanas/): fonte única e versionada.
 *
 * Cada plano é uma lista de etapas { de, ate, normal, sensivel } (semanas, de 1 a 12).
 * O texto diz QUANTAS VEZES por semana usar, nunca quanto produto nem qual concentração:
 * isso é da bula do produto ou da receita.
 *
 * RASCUNHO v0.1: escrito a partir das próprias regras do site (/regras-ativos.js, ex.: "comece 2 noites
 * por semana" para retinoide e "1 a 2 noites por semana" para ácido em pele sensível) e de orientações
 * de uso comuns. Ainda não foi revisado por farmacêutico(a) ou dermatologista: a página diz isso.
 * Para mudar: edite, suba VERSAO e registre em HISTORICO.
 */
(function (raiz) {
  "use strict";
  var VERSAO = "0.1.0";
  var HISTORICO = [
    { versao: "0.1.0", data: "2026-11-09", nota: "Primeira versão (rascunho, sem revisão profissional): retinoide, ácido esfoliante (AHA), ácido salicílico, vitamina C e ácido azelaico." }
  ];

  var PLANOS = {
    retinoide: {
      nome: "Retinol ou outro retinoide", periodo: "noite",
      antes: "Use à noite, na pele seca, e protetor solar todos os dias. Não comece um ácido esfoliante nas mesmas semanas.",
      etapas: [
        { de: 1, ate: 2, normal: "2 noites por semana, com 2 ou 3 dias de intervalo (ex.: segunda e quinta)", sensivel: "1 noite por semana" },
        { de: 3, ate: 4, normal: "3 noites por semana, em dias alternados", sensivel: "2 noites por semana, com intervalo" },
        { de: 5, ate: 8, normal: "Noite sim, noite não", sensivel: "2 a 3 noites por semana, em dias alternados" },
        { de: 9, ate: 12, normal: "Todas as noites, se a pele estiver tolerando bem. Se não, fique na etapa anterior", sensivel: "Noite sim, noite não, se a pele estiver tolerando bem" }
      ]
    },
    aha: {
      nome: "Ácido esfoliante (glicólico, lático, mandélico)", periodo: "noite",
      antes: "Use à noite e protetor solar todos os dias. Não use na mesma noite de um retinoide.",
      etapas: [
        { de: 1, ate: 4, normal: "1 a 2 noites por semana", sensivel: "1 noite por semana" },
        { de: 5, ate: 8, normal: "2 noites por semana, com intervalo", sensivel: "1 a 2 noites por semana" },
        { de: 9, ate: 12, normal: "Até 3 noites por semana, se a pele estiver tolerando bem", sensivel: "Até 2 noites por semana, se a pele estiver tolerando bem" }
      ]
    },
    bha: {
      nome: "Ácido salicílico (BHA)", periodo: "noite",
      antes: "Use à noite e protetor solar todos os dias. Não use na mesma noite de um retinoide.",
      etapas: [
        { de: 1, ate: 4, normal: "2 noites por semana", sensivel: "1 noite por semana" },
        { de: 5, ate: 8, normal: "3 noites por semana, em dias alternados", sensivel: "1 a 2 noites por semana" },
        { de: 9, ate: 12, normal: "Noite sim, noite não, se a pele estiver tolerando bem", sensivel: "Até 3 noites por semana, se a pele estiver tolerando bem" }
      ]
    },
    vitc: {
      nome: "Vitamina C", periodo: "manha",
      antes: "Use de manhã, antes do protetor solar. Faça um teste numa área pequena antes de passar no rosto todo.",
      etapas: [
        { de: 1, ate: 2, normal: "Manhã sim, manhã não", sensivel: "2 a 3 manhãs por semana" },
        { de: 3, ate: 12, normal: "Todas as manhãs, se não arder", sensivel: "Manhã sim, manhã não; todas as manhãs a partir da semana 5, se não arder" }
      ]
    },
    azelaico: {
      nome: "Ácido azelaico", periodo: "noite",
      antes: "Siga a frequência da bula. Comece só à noite.",
      etapas: [
        { de: 1, ate: 2, normal: "Noite sim, noite não", sensivel: "2 a 3 noites por semana" },
        { de: 3, ate: 4, normal: "Todas as noites", sensivel: "Noite sim, noite não" },
        { de: 5, ate: 12, normal: "Todas as noites; manhã e noite só se a bula indicar e a pele tolerar", sensivel: "Todas as noites, se a pele tolerar" }
      ]
    }
  };

  var SEMPRE = [
    "Siga a bula do produto. Se ele foi receitado, siga a receita: ela vale mais que este plano.",
    "Ardência leve e passageira pode acontecer. Se arder forte, avermelhar ou descamar, volte uma etapa; se não melhorar em alguns dias, pare e procure um dermatologista.",
    "Comece um ativo novo por vez. Gravidez, amamentação ou tratamento de pele em andamento: fale com seu médico antes."
  ];

  function etapa(plano, semana, sensivel) {
    var p = PLANOS[plano];
    if (!p) return null;
    for (var i = 0; i < p.etapas.length; i++) {
      var e = p.etapas[i];
      if (semana >= e.de && semana <= e.ate) return { de: e.de, ate: e.ate, texto: sensivel ? e.sensivel : e.normal, indice: i };
    }
    return null;
  }

  var API = { VERSAO: VERSAO, HISTORICO: HISTORICO, PLANOS: PLANOS, SEMPRE: SEMPRE, etapa: etapa };
  if (typeof module === "object" && module.exports) module.exports = API;
  else raiz.PSPlano = API;
})(typeof window !== "undefined" ? window : this);
