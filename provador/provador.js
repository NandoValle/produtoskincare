// Provador de pele: quiz que sugere uma rotina com os produtos da vitrine.
// Roda 100% no navegador. As respostas ficam só na URL; nada é enviado ou salvo.
'use strict';

const VALIDADE_DIAS = 100; // mesma regra da home (link de afiliado do TikTok Shop)
const DIA = 86400000;
const TIPOS = ['oleosa', 'mista', 'seca', 'normal'];
const NOME_PASSO = { limpeza: 'Limpeza', tratamento: 'Tratamento', hidratacao: 'Hidratação', protetor: 'Protetor solar' };
const NOME_EVIDENCIA = { forte: 'evidência forte', moderada: 'evidência moderada', emergente: 'evidência emergente' };
const PONTOS_EVIDENCIA = { forte: 2, moderada: 1 };

let quiz = null;
let produtos = [];
let estado = novoEstado();
let telas = [];
let indice = 0;

function novoEstado() {
  return { modo: 'quiz', respostas: {}, tipo: null, sensivel: 0, preocupacoes: [], situacoes: [], orcamento: 'livre', passos: '3' };
}

/* ---------- utilidades ---------- */
const $ = id => document.getElementById(id);
function el(tag, attrs = {}, texto) {
  const n = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) n.setAttribute(k, v);
  if (texto != null) n.textContent = texto;
  return n;
}
function hostOficial(url) {
  try { const h = new URL(url).hostname.toLowerCase(); return h === 'tiktok.com' || h.endsWith('.tiktok.com'); }
  catch (e) { return false; }
}
function linkValido(p) {
  if (!hostOficial(p.link) || !p.link_gerado_em) return false;
  const gerado = new Date(p.link_gerado_em + 'T00:00:00');
  if (isNaN(gerado)) return false;
  return gerado.getTime() + VALIDADE_DIAS * DIA >= Date.now();
}
function brl(v) { return typeof v === 'number' ? v.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' }) : ''; }
function dataBR(iso) { const [a, m, d] = String(iso || '').split('-'); return d ? `${d}/${m}/${a}` : ''; }
const lista = v => (Array.isArray(v) ? v : v ? [v] : []);
function mostrar(id) {
  for (const t of document.querySelectorAll('.tela')) t.hidden = t.id !== id;
  window.scrollTo(0, 0);
}

/* ---------- fluxo de telas ---------- */
function montarTelas() {
  const t = [];
  if (estado.modo === 'quiz') quiz.perguntas.forEach(p => t.push({ tipo: 'pergunta', p }));
  t.push({ tipo: 'preocupacoes' }, { tipo: 'situacoes' }, { tipo: 'preferencias' });
  telas = t;
}

function opcaoRadio(nome, valor, texto, marcado) {
  const l = el('label', { class: 'opcao' });
  const i = el('input', { type: 'radio', name: nome, value: valor });
  if (marcado) i.checked = true;
  l.append(i, document.createTextNode(texto));
  return l;
}
function opcaoCheck(nome, valor, texto, marcado) {
  const l = el('label', { class: 'opcao' });
  const i = el('input', { type: 'checkbox', name: nome, value: valor });
  if (marcado) i.checked = true;
  l.append(i, document.createTextNode(texto));
  return l;
}
function grupo(legenda, ajuda, filhos) {
  const f = el('fieldset');
  f.append(el('legend', {}, legenda));
  if (ajuda) f.append(el('p', { class: 'ajuda' }, ajuda));
  const box = el('div', { class: 'opcoes' });
  box.append(...filhos);
  f.append(box);
  return f;
}

function desenharTela() {
  const tela = telas[indice];
  const total = telas.length;
  $('barra').style.width = `${Math.round((indice / total) * 100)}%`;
  $('passo-n').textContent = `Pergunta ${indice + 1} de ${total}`;
  $('erro-pergunta').textContent = '';
  $('btn-proximo').textContent = indice === total - 1 ? 'Ver minha rotina' : 'Próximo';
  const alvo = $('pergunta');
  let conteudo;

  if (tela.tipo === 'pergunta') {
    const p = tela.p;
    conteudo = grupo(p.titulo, p.ajuda, p.opcoes.map((o, i) => opcaoRadio('r', String(i), o.texto, estado.respostas[p.id] === i)));
  } else if (tela.tipo === 'preocupacoes') {
    conteudo = grupo('O que você mais quer melhorar?', 'Escolha até 2. Pode pular se quiser só uma rotina básica.',
      quiz.preocupacoes.map(c => opcaoCheck('c', c.id, c.texto, estado.preocupacoes.includes(c.id))));
  } else if (tela.tipo === 'situacoes') {
    const filhos = quiz.situacoes.map(s => opcaoCheck('s', s.id, s.texto, estado.situacoes.includes(s.id)));
    conteudo = grupo('Alguma dessas situações vale para você?', 'Isso deixa a sugestão mais segura. Se nenhuma valer, é só seguir.', filhos);
  } else {
    conteudo = el('div');
    conteudo.append(
      grupo('Quanto quer gastar por produto?', null,
        quiz.orcamentos.map(o => opcaoRadio('o', o.id, o.texto, estado.orcamento === o.id))),
      el('div', { style: 'height:20px' }),
      grupo('Que tamanho de rotina você prefere?', null, [
        opcaoRadio('n', '3', 'Simples: 3 passos', estado.passos === '3'),
        opcaoRadio('n', '5', 'Completa: com tratamento de manhã e de noite', estado.passos === '5')
      ])
    );
  }
  alvo.replaceChildren(conteudo);
  // limita preocupações a 2
  if (tela.tipo === 'preocupacoes') {
    alvo.addEventListener('change', limitarDuas);
  } else {
    alvo.removeEventListener('change', limitarDuas);
  }
  const primeiro = alvo.querySelector('input');
  if (primeiro) primeiro.focus({ preventScroll: true });
}

function limitarDuas(e) {
  const marcados = [...$('pergunta').querySelectorAll('input[name="c"]:checked')];
  if (marcados.length > 2) {
    e.target.checked = false;
    $('erro-pergunta').textContent = 'Escolha no máximo 2.';
  } else {
    $('erro-pergunta').textContent = '';
  }
}

function salvarTela() {
  const tela = telas[indice];
  const f = $('form-pergunta');
  if (tela.tipo === 'pergunta') {
    const v = f.querySelector('input[name="r"]:checked');
    if (!v) { $('erro-pergunta').textContent = 'Escolha uma opção para continuar.'; return false; }
    estado.respostas[tela.p.id] = Number(v.value);
  } else if (tela.tipo === 'preocupacoes') {
    estado.preocupacoes = [...f.querySelectorAll('input[name="c"]:checked')].map(i => i.value).slice(0, 2);
  } else if (tela.tipo === 'situacoes') {
    estado.situacoes = [...f.querySelectorAll('input[name="s"]:checked')].map(i => i.value);
  } else {
    estado.orcamento = (f.querySelector('input[name="o"]:checked') || {}).value || 'livre';
    estado.passos = (f.querySelector('input[name="n"]:checked') || {}).value || '3';
  }
  return true;
}

/* ---------- perfil ---------- */
function calcularPerfil() {
  const pontos = Object.fromEntries(TIPOS.map(t => [t, 0]));
  let sensivel = estado.sensivel;
  let tipo = estado.tipo;
  let confianca = 'alta';
  let segundo = null;

  if (estado.modo === 'quiz') {
    for (const p of quiz.perguntas) {
      const o = p.opcoes[estado.respostas[p.id]];
      if (!o) continue;
      for (const [t, v] of Object.entries(o.pontos || {})) pontos[t] += v;
      if (typeof o.sensivel === 'number') sensivel = Math.max(sensivel, o.sensivel);
    }
    // desempate: mista > normal > oleosa > seca (a mais comum primeiro)
    const ordem = ['mista', 'normal', 'oleosa', 'seca'];
    const ranking = [...ordem].sort((a, b) => pontos[b] - pontos[a]);
    tipo = ranking[0];
    segundo = ranking[1];
    const margem = pontos[tipo] - pontos[segundo];
    confianca = pontos[tipo] === 0 ? 'baixa' : margem >= 3 ? 'alta' : margem >= 1 ? 'media' : 'baixa';
  }
  if (estado.situacoes.includes('vasinhos')) sensivel = Math.max(sensivel, 2);
  return { tipo, segundo, confianca, sensivel };
}

/* ---------- URL (compartilhar sem salvar nada) ---------- */
function paraURL(perfil) {
  const q = new URLSearchParams();
  q.set('t', perfil.tipo);
  if (perfil.sensivel) q.set('s', String(perfil.sensivel));
  if (estado.preocupacoes.length) q.set('p', estado.preocupacoes.join(','));
  if (estado.situacoes.length) q.set('x', estado.situacoes.join(','));
  if (estado.orcamento !== 'livre') q.set('o', estado.orcamento);
  if (estado.passos !== '3') q.set('n', estado.passos);
  if (perfil.confianca !== 'alta') q.set('c', perfil.confianca + (perfil.segundo ? '-' + perfil.segundo : ''));
  return q;
}
function deURL() {
  const q = new URLSearchParams(location.search);
  const t = q.get('t');
  if (!TIPOS.includes(t)) return null;
  const valid = (v, ok) => (v || '').split(',').filter(x => ok.includes(x));
  estado = novoEstado();
  estado.modo = 'url';
  estado.tipo = t;
  estado.sensivel = Math.min(2, Math.max(0, Number(q.get('s')) || 0));
  estado.preocupacoes = valid(q.get('p'), quiz.preocupacoes.map(c => c.id)).slice(0, 2);
  estado.situacoes = valid(q.get('x'), quiz.situacoes.map(s => s.id));
  estado.orcamento = quiz.orcamentos.some(o => o.id === q.get('o')) ? q.get('o') : 'livre';
  estado.passos = q.get('n') === '5' ? '5' : '3';
  const [conf, seg] = (q.get('c') || 'alta').split('-');
  return {
    tipo: t,
    sensivel: estado.sensivel,
    confianca: ['alta', 'media', 'baixa'].includes(conf) ? conf : 'alta',
    segundo: TIPOS.includes(seg) ? seg : null
  };
}

/* ---------- recomendação ---------- */
function candidatos(perfil) {
  const vetados = estado.situacoes.includes('gestante') ? quiz.ingredientes_vetados.gestante : [];
  const max = (quiz.orcamentos.find(o => o.id === estado.orcamento) || {}).max ?? null;
  const ok = produtos.filter(p => {
    if (!p.rotina || !linkValido(p)) return false;
    const tipos = lista(p.tipos_pele);
    if (!tipos.includes('todos') && !tipos.includes(perfil.tipo)) return false;
    const evitar = lista(p.evitar_para);
    if (evitar.includes(perfil.tipo)) return false;
    if (perfil.sensivel >= 1 && evitar.includes('sensivel')) return false;
    if (lista(p.ingredientes).some(i => vetados.includes(i))) return false;
    return true;
  });
  const pontuar = p => {
    let s = lista(p.tipos_pele).includes(perfil.tipo) ? 3 : 1;
    s += 2 * lista(p.preocupacoes).filter(c => estado.preocupacoes.includes(c)).length;
    if (typeof p.preco === 'number' && (max === null || p.preco <= max)) s += 1;
    if (typeof p.preco === 'number') s += 1;
    s += PONTOS_EVIDENCIA[p.evidencia] || 0;
    return s;
  };
  // agrupa anúncios do mesmo produto: mostra o mais barato com preço conhecido
  const grupos = new Map();
  for (const p of ok) {
    const g = p.grupo || p.nome;
    if (!grupos.has(g)) grupos.set(g, []);
    grupos.get(g).push(p);
  }
  return [...grupos.values()].map(itens => {
    const comPreco = itens.filter(i => typeof i.preco === 'number').sort((a, b) => a.preco - b.preco);
    const rep = comPreco[0] || itens[0];
    return { p: rep, pontos: pontuar(rep), outras: itens.length - 1 };
  });
}

function escolher(cands, passo, periodo, exigirPreocupacao) {
  return cands
    .filter(c => lista(c.p.passo).includes(passo) && lista(c.p.periodo).includes(periodo))
    .filter(c => !exigirPreocupacao || lista(c.p.preocupacoes).some(x => estado.preocupacoes.includes(x)))
    .sort((a, b) => b.pontos - a.pontos || (a.p.preco ?? 1e9) - (b.p.preco ?? 1e9));
}

function montarRotina(perfil) {
  const cands = candidatos(perfil);
  const receita = estado.situacoes.includes('receita');
  const temPreocupacao = estado.preocupacoes.length > 0;
  const tratarManha = estado.passos === '5' && temPreocupacao && !receita && perfil.sensivel === 0;
  const tratarNoite = temPreocupacao && !receita;
  const plano = {
    manha: ['limpeza', ...(tratarManha ? ['tratamento'] : []), 'hidratacao', 'protetor'],
    noite: ['limpeza', ...(tratarNoite ? ['tratamento'] : []), 'hidratacao']
  };
  const rotina = {};
  const atendidas = new Set();
  for (const [periodo, passos] of Object.entries(plano)) {
    let anterior = null;
    rotina[periodo] = passos.map(passo => {
      const opcoes = escolher(cands, passo, periodo, passo === 'tratamento');
      const principal = opcoes[0] || null;
      // o kit hidratante + protetor já cobre o passo seguinte
      if (principal && anterior && principal.p.grupo && principal.p.grupo === anterior.p.grupo) {
        return { passo, incluso: anterior.p };
      }
      if (passo === 'tratamento' && principal) {
        lista(principal.p.preocupacoes).filter(x => estado.preocupacoes.includes(x)).forEach(x => atendidas.add(x));
      }
      anterior = principal;
      return { passo, principal, alternativa: opcoes[1] || null };
    });
  }
  const faltando = estado.preocupacoes.filter(c => !atendidas.has(c) && !receita);
  return { rotina, faltando, receita };
}

/* ---------- resultado ---------- */
function alerta(titulo, texto) {
  const a = el('div', { class: 'alerta', role: 'note' });
  a.append(el('strong', {}, titulo), document.createTextNode(texto));
  return a;
}

function cartaoEtapa(item, n) {
  const titulo = `Passo ${n} · ${NOME_PASSO[item.passo]}`;
  if (item.incluso) {
    const c = el('div', { class: 'etapa lacuna' });
    c.append(el('span', { class: 'num' }, titulo), el('p', {}, `Já incluso no ${item.incluso.nome}, do passo anterior.`));
    return c;
  }
  if (!item.principal) {
    const c = el('div', { class: 'etapa lacuna' });
    const chave = item.passo === 'tratamento' ? estado.preocupacoes[0] : item.passo;
    c.append(
      el('span', { class: 'num' }, titulo),
      el('h3', {}, 'O que procurar'),
      el('p', {}, quiz.o_que_procurar[chave] || 'Ainda não temos um produto da vitrine para este passo.'),
      el('p', { class: 'meta' }, 'Ainda não temos um produto da vitrine que sirva aqui.')
    );
    return c;
  }
  const p = item.principal.p;
  const c = el('article', { class: 'etapa' });
  c.append(p.foto ? el('img', { src: '../' + p.foto, alt: p.nome, loading: 'lazy', decoding: 'async' }) : el('span'));
  const corpo = el('div');
  corpo.append(el('span', { class: 'num' }, titulo));
  const h = el('h3', {}, p.nome);
  if (NOME_EVIDENCIA[p.evidencia]) h.append(el('span', { class: 'selo' }, NOME_EVIDENCIA[p.evidencia]));
  corpo.append(h);
  if (p.porque) corpo.append(el('p', {}, p.porque));
  const preco = typeof p.preco === 'number' ? `${brl(p.preco)} · preço visto em ${dataBR(p.preco_em)}` : 'Preço na loja';
  corpo.append(el('p', { class: 'meta' }, preco + (item.principal.outras ? ` · também em mais ${item.principal.outras} loja(s)` : '')));
  corpo.append(el('a', { class: 'botao', href: p.link, target: '_blank', rel: 'sponsored nofollow noopener' }, 'Ver no TikTok Shop'));
  if (item.alternativa) {
    const a = item.alternativa.p;
    const alt = el('p', { class: 'alt' }, 'Alternativa: ');
    alt.append(el('a', { href: a.link, target: '_blank', rel: 'sponsored nofollow noopener' }, a.nome));
    if (typeof a.preco === 'number') alt.append(document.createTextNode(` (${brl(a.preco)})`));
    corpo.append(alt);
  }
  c.append(corpo);
  return c;
}

function desenharResultado(perfil) {
  const { rotina, faltando, receita } = montarRotina(perfil);
  const info = quiz.tipos[perfil.tipo];
  const box = $('tela-resultado');
  const filhos = [];

  filhos.push(el('h1', {}, 'Sua rotina'));
  const tipoCard = el('div', { class: 'cartao' });
  tipoCard.append(el('span', { class: 'rotulo' }, 'Seu tipo de pele'));
  tipoCard.append(el('h2', {}, info.nome + (perfil.sensivel >= 1 ? ' e sensível' : '')));
  tipoCard.append(el('p', { style: 'margin:0' }, info.explicacao));
  if (perfil.confianca === 'baixa') {
    tipoCard.append(el('p', { class: 'aviso-legal' },
      `Suas respostas ficaram divididas${perfil.segundo ? ' entre ' + info.nome.toLowerCase() + ' e ' + quiz.tipos[perfil.segundo].nome.toLowerCase() : ''}. Para confirmar, faça o teste do rosto limpo e refaça o provador.`));
  }
  filhos.push(tipoCard);

  if (estado.situacoes.includes('gestante')) filhos.push(alerta('Gravidez e amamentação', 'Tiramos da sugestão ativos que costumam ser evitados nessa fase, como retinoides e ácido salicílico. Mesmo assim, confirme cada produto com seu médico.'));
  if (receita) filhos.push(alerta('Você usa tratamento com receita', 'Por isso a sugestão traz só limpeza, hidratação e protetor. Fale com seu médico antes de acrescentar qualquer ativo.'));
  if (estado.situacoes.includes('vasinhos')) filhos.push(alerta('Procure um dermatologista', 'Vermelhidão que não passa e vasinhos aparentes podem ser sinal de rosácea, que precisa de avaliação médica. Deixamos a rotina com o mínimo de ativos.'));
  if (perfil.sensivel >= 1) filhos.push(alerta('Faça o teste de contato', 'Antes de usar um produto novo no rosto todo, aplique um pouco atrás da orelha ou no queixo por 2 a 3 dias. Se arder ou ficar vermelho, não use.'));

  // abas manhã/noite
  const abas = el('div', { class: 'abas', role: 'tablist', 'aria-label': 'Período da rotina' });
  const paineis = {};
  for (const [periodo, rotulo] of [['manha', 'Manhã'], ['noite', 'Noite']]) {
    const b = el('button', { type: 'button', role: 'tab', id: 'aba-' + periodo, 'aria-controls': 'painel-' + periodo, 'aria-selected': String(periodo === 'manha') }, rotulo);
    abas.append(b);
    const painel = el('div', { role: 'tabpanel', id: 'painel-' + periodo, 'aria-labelledby': 'aba-' + periodo });
    painel.hidden = periodo !== 'manha';
    rotina[periodo].forEach((item, i) => painel.append(cartaoEtapa(item, i + 1)));
    paineis[periodo] = painel;
  }
  abas.addEventListener('click', e => {
    const b = e.target.closest('[role="tab"]');
    if (!b) return;
    for (const x of abas.children) x.setAttribute('aria-selected', String(x === b));
    for (const [k, p] of Object.entries(paineis)) p.hidden = 'aba-' + k !== b.id;
  });
  filhos.push(abas, el('p', { class: 'aviso-legal' }, 'Contém links de afiliado: se você comprar pelos botões, posso receber comissão, sem custo extra para você.'), paineis.manha, paineis.noite);

  if (faltando.length) {
    const c = el('div', { class: 'cartao' });
    c.append(el('span', { class: 'rotulo' }, 'Para completar'));
    const ul = el('ul', { style: 'margin:8px 0 0;padding-left:20px' });
    for (const f of faltando) {
      const nome = (quiz.preocupacoes.find(x => x.id === f) || {}).texto || f;
      const li = el('li');
      li.append(el('strong', {}, nome + ': '), document.createTextNode(quiz.o_que_procurar[f] || ''));
      ul.append(li);
    }
    c.append(ul, el('p', { class: 'aviso-legal', style: 'margin:8px 0 0' }, 'Ainda não temos esses produtos na vitrine.'));
    filhos.push(c);
  }

  if (!receita) {
    const c = el('div', { class: 'cartao comecar' });
    c.append(el('span', { class: 'rotulo' }, 'Como começar'));
    const ol = el('ol');
    ['Nas semanas 1 e 2, use só limpeza, hidratação e protetor solar.',
     'A partir da semana 3, inclua o tratamento à noite, 2 a 3 vezes por semana.',
     'Se a pele tolerar bem, aumente a frequência aos poucos. Um ativo novo de cada vez.',
     'Protetor solar todas as manhãs, mesmo em dias nublados ou dentro de casa.'
    ].forEach(t => ol.append(el('li', {}, t)));
    c.append(ol);
    filhos.push(c);
  }

  filhos.push(el('p', { class: 'aviso-legal' }, 'Isto é uma sugestão de cosméticos, não um diagnóstico, e não substitui a avaliação de um dermatologista. Em caso de lesões, dor, acne intensa ou irritação que não passa, procure um médico.'));

  const acoes = el('div', { class: 'linha-acoes' });
  const refazer = el('button', { class: 'btn', type: 'button' }, 'Refazer');
  refazer.onclick = () => { history.replaceState(null, '', location.pathname); estado = novoEstado(); mostrar('tela-inicio'); };
  const copiar = el('button', { class: 'btn', type: 'button' }, 'Copiar link da minha rotina');
  copiar.onclick = async () => {
    try { await navigator.clipboard.writeText(location.href); copiar.textContent = 'Link copiado'; }
    catch (e) { window.prompt('Copie o link:', location.href); }
  };
  acoes.append(refazer, copiar, el('a', { class: 'btn', href: '../' }, 'Ver a vitrine'));
  filhos.push(acoes);

  box.replaceChildren(...filhos);
  mostrar('tela-resultado');
}

function finalizar() {
  const perfil = calcularPerfil();
  history.replaceState(null, '', location.pathname + '?' + paraURL(perfil).toString());
  desenharResultado(perfil);
}

/* ---------- eventos ---------- */
function iniciar() {
  $('btn-comecar').onclick = () => { estado = novoEstado(); montarTelas(); indice = 0; desenharTela(); mostrar('tela-perguntas'); };
  $('btn-sei-tipo').onclick = () => {
    estado = novoEstado();
    estado.modo = 'sei';
    $('opcoes-sei').replaceChildren(...TIPOS.map(t => opcaoRadio('tipo', t, quiz.tipos[t].nome, false)));
    mostrar('tela-sei');
  };
  for (const b of document.querySelectorAll('[data-voltar-inicio]')) b.onclick = () => mostrar('tela-inicio');
  $('form-sei').onsubmit = e => {
    e.preventDefault();
    const v = e.target.querySelector('input[name="tipo"]:checked');
    if (!v) { $('erro-sei').textContent = 'Escolha um tipo para continuar.'; return; }
    estado.tipo = v.value;
    estado.sensivel = e.target.querySelector('input[name="sensivel"]').checked ? 2 : 0;
    montarTelas(); indice = 0; desenharTela(); mostrar('tela-perguntas');
  };
  $('form-pergunta').onsubmit = e => {
    e.preventDefault();
    if (!salvarTela()) return;
    if (indice < telas.length - 1) { indice++; desenharTela(); } else finalizar();
  };
  $('btn-voltar').onclick = () => {
    salvarTelaSilenciosa();
    if (indice > 0) { indice--; desenharTela(); }
    else mostrar(estado.modo === 'sei' ? 'tela-sei' : 'tela-inicio');
  };

  const perfilURL = deURL();
  if (perfilURL) desenharResultado(perfilURL);
}
function salvarTelaSilenciosa() {
  const erro = $('erro-pergunta').textContent;
  salvarTela();
  $('erro-pergunta').textContent = erro;
}

Promise.all([
  fetch('quiz.json', { cache: 'no-cache' }).then(r => r.json()),
  fetch('../produtos.json', { cache: 'no-cache' }).then(r => r.json()).catch(() => [])
]).then(([q, p]) => {
  quiz = q;
  produtos = Array.isArray(p) ? p : [];
  iniciar();
}).catch(err => {
  console.error('Provador não carregou:', err);
  $('tela-inicio').append(el('p', { class: 'erro' }, 'Não foi possível carregar o provador. Atualize a página para tentar de novo.'));
});
