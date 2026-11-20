/* Som do Sonho — trilha ambiente opcional + sons suaves do ritual guiado.
   Tudo sintetizado via Web Audio API: nenhum arquivo de áudio, tudo local.
   Opt-in por natureza — nada toca sem a pessoa ligar. Salva a preferência
   em localStorage. Respeita prefers-reduced-motion (desliga automaticamente). */
(() => {
  "use strict";

  const CHAVE = "ps_som_sonho"; // {on:bool, vol:0..1}
  const ctxHolder = { ctx: null };

  function lerPreferencia() {
    try {
      return JSON.parse(localStorage.getItem(CHAVE)) || { on: false, vol: 0.5 };
    } catch { return { on: false, vol: 0.5 }; }
  }
  function salvarPreferencia(p) {
    try { localStorage.setItem(CHAVE, JSON.stringify(p)); } catch {}
  }

  let pref = lerPreferencia();

  /* ---------- contexto de áudio (só é criado após gesto do usuário) ---------- */
  function garantirCtx() {
    if (ctxHolder.ctx) return ctxHolder.ctx;
    const AC = window.AudioContext || window.webkitAudioContext;
    if (!AC) return null;
    ctxHolder.ctx = new AC();
    return ctxHolder.ctx;
  }

  /* ---------- trilha ambiente: ruído rosa filtrado + pad que respira ---------- */
  let ambiente = null; // { nodes, gain }

  function criarAmbiente() {
    const ctx = garantirCtx();
    if (!ctx || ambiente) return;
    const agora = ctx.currentTime;
    const vol = pref.vol * 0.22; // bem baixinho

    const saida = ctx.createGain();
    saida.gain.setValueAtTime(0, agora);
    saida.gain.linearRampToValueAtTime(vol, agora + 3.0); // fade-in suave 3s
    saida.connect(ctx.destination);

    // --- ruído rosa (chuva quente / ar) ---
    const duracao = 4;
    const taxa = ctx.sampleRate;
    const buf = ctx.createBuffer(1, taxa * duracao, taxa);
    const dados = buf.getChannelData(0);
    let b0 = 0, b1 = 0, b2 = 0;
    for (let i = 0; i < dados.length; i++) {
      const branco = Math.random() * 2 - 1;
      b0 = 0.99765 * b0 + branco * 0.0990460;
      b1 = 0.96300 * b1 + branco * 0.2965164;
      b2 = 0.57000 * b2 + branco * 1.0526913;
      dados[i] = (b0 + b1 + b2 + branco * 0.1848) * 0.11;
    }
    const ruido = ctx.createBufferSource();
    ruido.buffer = buf; ruido.loop = true;

    const lp = ctx.createBiquadFilter();
    lp.type = "lowpass"; lp.frequency.value = 420; lp.Q.value = 0.6;
    const hp = ctx.createBiquadFilter();
    hp.type = "highpass"; hp.frequency.value = 60;

    const ganhoRuido = ctx.createGain();
    ganhoRuido.gain.value = 0.7;
    ruido.connect(lp); lp.connect(hp); hp.connect(ganhoRuido); ganhoRuido.connect(saida);
    ruido.start(agora);

    // --- pad: 3 senos lentos que respiram ---
    const freqs = [110, 165, 220]; // Lá2, Mi3, Lá3 — acorde aberto
    const oscs = [];
    freqs.forEach((f, i) => {
      const o = ctx.createOscillator();
      o.type = "sine"; o.frequency.value = f;
      const g = ctx.createGain();
      g.gain.value = 0.045;
      // LFO de respiração (~0.06 Hz = ~17 s por ciclo)
      const lfo = ctx.createOscillator();
      lfo.type = "sine"; lfo.frequency.value = 0.055 + i * 0.012;
      const lfoGanho = ctx.createGain();
      lfoGanho.gain.value = 0.028;
      lfo.connect(lfoGanho); lfoGanho.connect(g.gain);
      o.connect(g); g.connect(saida);
      o.start(agora); lfo.start(agora);
      oscs.push(o, lfo);
    });

    // --- brilho: um seno agudo bem fraco, tipo luz ---
    const brilho = ctx.createOscillator();
    brilho.type = "sine"; brilho.frequency.value = 880;
    const gB = ctx.createGain(); gB.gain.value = 0.008;
    const lfoB = ctx.createOscillator(); lfoB.type = "sine"; lfoB.frequency.value = 0.033;
    const lfoBg = ctx.createGain(); lfoBg.gain.value = 0.006;
    lfoB.connect(lfoBg); lfoBg.connect(gB.gain);
    brilho.connect(gB); gB.connect(saida);
    brilho.start(agora); lfoB.start(agora);

    ambiente = { saida, sources: [ruido, ...oscs, brilho, lfoB] };
  }

  function pararAmbiente() {
    if (!ambiente || !ctxHolder.ctx) return;
    const ctx = ctxHolder.ctx;
    const agora = ctx.currentTime;
    ambiente.saida.gain.cancelScheduledValues(agora);
    ambiente.saida.gain.setValueAtTime(ambiente.saida.gain.value, agora);
    ambiente.saida.gain.linearRampToValueAtTime(0, agora + 1.8);
    const alvo = ambiente;
    ambiente = null;
    setTimeout(() => {
      alvo.sources.forEach(s => { try { s.stop(); } catch {} });
    }, 2000);
  }

  /* ---------- sons do ritual (sintetizados, com cauda de reverberação) ---------- */

  function envolver(g, ctx, t0, ataque, dur, pico) {
    g.gain.setValueAtTime(0, t0);
    g.gain.linearRampToValueAtTime(pico, t0 + ataque);
    g.gain.exponentialRampToValueAtTime(0.0001, t0 + dur);
  }

  /* campana suave — passo concluído */
  function somPasso() {
    const ctx = garantirCtx(); if (!ctx) return;
    const t0 = ctx.currentTime;
    const vol = pref.vol;
    [[660, 0.5], [990, 0.22]].forEach(([f, amp]) => {
      const o = ctx.createOscillator(); o.type = "sine"; o.frequency.value = f;
      const g = ctx.createGain(); envolver(g, ctx, t0, 0.012, 2.2, amp * vol * 0.35);
      o.connect(g); g.connect(ctx.destination);
      o.start(t0); o.stop(t0 + 2.4);
    });
  }

  /* sino longo — fim do ritual / tempo cumprido */
  function somSino() {
    const ctx = garantirCtx(); if (!ctx) return;
    const t0 = ctx.currentTime;
    const vol = pref.vol;
    [[220, 0.45], [330, 0.28], [440, 0.18], [554, 0.1]].forEach(([f, amp], i) => {
      const o = ctx.createOscillator(); o.type = "sine"; o.frequency.value = f;
      const g = ctx.createGain();
      envolver(g, ctx, t0 + i * 0.06, 0.02, 4.5, amp * vol * 0.4);
      o.connect(g); g.connect(ctx.destination);
      o.start(t0 + i * 0.06); o.stop(t0 + 5);
    });
  }

  /* clique discreto — pausar / retomar / pular */
  function somClique() {
    const ctx = garantirCtx(); if (!ctx) return;
    const t0 = ctx.currentTime;
    const vol = pref.vol;
    const o = ctx.createOscillator(); o.type = "triangle"; o.frequency.value = 520;
    const g = ctx.createGain(); envolver(g, ctx, t0, 0.004, 0.12, 0.12 * vol);
    o.connect(g); g.connect(ctx.destination);
    o.start(t0); o.stop(t0 + 0.15);
  }

  /* transição de etapa — tom suave de dois passos */
  function somTransicao() {
    const ctx = garantirCtx(); if (!ctx) return;
    const t0 = ctx.currentTime;
    const vol = pref.vol;
    [[440, 0], [587, 0.18]].forEach(([f, atraso]) => {
      const o = ctx.createOscillator(); o.type = "sine"; o.frequency.value = f;
      const g = ctx.createGain(); envolver(g, ctx, t0 + atraso, 0.015, 1.4, 0.22 * vol);
      o.connect(g); g.connect(ctx.destination);
      o.start(t0 + atraso); o.stop(t0 + atraso + 1.6);
    });
  }

  /* ---------- API pública ---------- */
  const SonhoSom = {
    estaAtivo: () => pref.on,
    volume: () => pref.vol,
    reduzMovimento: () => matchMedia("(prefers-reduced-motion: reduce)").matches,

    ligar() {
      if (this.reduzMovimento()) return false;
      pref.on = true; salvarPreferencia(pref);
      const ctx = garantirCtx();
      if (ctx && ctx.state === "suspended") ctx.resume();
      criarAmbiente();
      return true;
    },
    desligar() {
      pref.on = false; salvarPreferencia(pref);
      pararAmbiente();
    },
    alternar() {
      if (pref.on) { this.desligar(); return false; }
      return this.ligar();
    },
    definirVolume(v) {
      pref.vol = Math.min(1, Math.max(0, v));
      salvarPreferencia(pref);
      if (ambiente && ctxHolder.ctx) {
        ambiente.saida.gain.setTargetAtTime(pref.vol * 0.22, ctxHolder.ctx.currentTime, 0.1);
      }
    },
    passo: somPasso,
    sino: somSino,
    clique: somClique,
    transicao: somTransicao
  };

  window.SonhoSom = SonhoSom;

  /* ---------- controle flutuante opt-in (injetado automaticamente) ---------- */
  function injetarControle() {
    if (document.getElementById("ps-som-sonho")) return;
    if (SonhoSom.reduzMovimento()) return; // sem controles desnecessários

    const caixa = document.createElement("div");
    caixa.id = "ps-som-sonho";
    caixa.setAttribute("role", "group");
    caixa.setAttribute("aria-label", "Som do sonho");
    caixa.innerHTML = `
      <button type="button" id="ps-som-botao" aria-pressed="false" title="Ligar ou desligar o som do sonho">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <path d="M11 5L6 9H3v6h3l5 4V5z"/>
          <path class="ps-som-onda" d="M15.5 8.5a5 5 0 010 7"/>
          <path class="ps-som-onda ps-som-onda2" d="M18.5 6a9 9 0 010 12"/>
          <line class="ps-som-x" x1="22" y1="9" x2="16" y2="15" style="display:none"/>
          <line class="ps-som-x" x1="16" y1="9" x2="22" y2="15" style="display:none"/>
        </svg>
        <span class="ps-som-rotulo">Som do sonho</span>
      </button>
      <div class="ps-som-painel" hidden>
        <label for="ps-som-volume">Volume</label>
        <input type="range" id="ps-som-volume" min="0" max="100" value="50" aria-label="Volume do som do sonho">
      </div>`;
    document.body.appendChild(caixa);

    const estilos = document.createElement("style");
    estilos.textContent = `
      #ps-som-sonho{position:fixed;right:16px;bottom:16px;z-index:90;font-family:var(--fonte-corpo,'Inter',sans-serif)}
      #ps-som-botao{display:inline-flex;align-items:center;gap:8px;min-height:48px;padding:10px 16px;border-radius:999px;border:1px solid var(--linha-2,rgba(26,22,20,.14));background:var(--papel,#fff);color:var(--tinta,#1a1614);cursor:pointer;font:inherit;font-size:.85rem;box-shadow:0 4px 18px rgba(26,22,20,.1);transition:all .25s}
      #ps-som-botao:hover{border-color:var(--rosa,#b4546a);transform:translateY(-2px)}
      #ps-som-botao[aria-pressed=true]{background:var(--rosa,#b4546a);color:#fff;border-color:var(--rosa,#b4546a)}
      #ps-som-botao[aria-pressed=true] .ps-som-onda{opacity:1}
      .ps-som-onda{opacity:.35}
      #ps-som-botao[aria-pressed=false] .ps-som-onda2{display:none}
      .ps-som-painel{margin-top:8px;padding:12px 16px;border-radius:14px;border:1px solid var(--linha-2,rgba(26,22,20,.14));background:var(--papel,#fff);box-shadow:0 4px 18px rgba(26,22,20,.1);display:flex;align-items:center;gap:10px;font-size:.82rem;color:var(--suave,#7a6e65)}
      .ps-som-painel input[type=range]{flex:1;accent-color:var(--rosa,#b4546a);min-height:24px}
      @media(max-width:560px){#ps-som-sonho{right:12px;bottom:12px}.ps-som-rotulo{display:none}#ps-som-botao{padding:12px;border-radius:50%}}
    `;
    document.head.appendChild(estilos);

    const botao = caixa.querySelector("#ps-som-botao");
    const painel = caixa.querySelector(".ps-som-painel");
    const slider = caixa.querySelector("#ps-som-volume");

    function sincronizar() {
      const on = SonhoSom.estaAtivo();
      botao.setAttribute("aria-pressed", String(on));
      painel.hidden = !on;
      slider.value = String(Math.round(SonhoSom.volume() * 100));
      botao.title = on ? "Desligar o som do sonho" : "Ligar o som do sonho";
      botao.querySelectorAll(".ps-som-x").forEach(l => l.style.display = on ? "none" : "");
    }
    sincronizar();

    botao.addEventListener("click", () => {
      const ativo = SonhoSom.alternar();
      if (ativo) { somClique(); }
      sincronizar();
    });
    slider.addEventListener("input", () => {
      SonhoSom.definirVolume(slider.value / 100);
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", injetarControle);
  } else {
    injetarControle();
  }
})();
