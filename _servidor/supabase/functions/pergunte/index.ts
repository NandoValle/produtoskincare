// Supabase Edge Function "pergunte": a IA de dúvidas de skincare do site.
// O navegador nunca vê a chave da API: ela fica no segredo ANTHROPIC_API_KEY do Supabase.
//
// Segredos/variáveis (supabase secrets set ...):
//   ANTHROPIC_API_KEY  obrigatório
//   CLAUDE_MODEL       opcional (padrão claude-haiku-5-5; claude-opus-5-5 é mais capaz e bem mais caro)
//   ALLOWED_ORIGINS    opcional, separado por vírgula (padrão: o domínio do site)
//
// Não guardamos as perguntas: nada é gravado em banco nem em log por esta função.
import Anthropic from "npm:@anthropic-ai/sdk@1.4.0";

const SITE = "https://produtoskincare.com.br";
const MODELO = Deno.env.get("CLAUDE_MODEL") ?? "claude-haiku-5-5";
const ORIGENS = (Deno.env.get("ALLOWED_ORIGINS") ?? `${SITE},https://www.produtoskincare.com.br`)
  .split(",").map((o) => o.trim()).filter(Boolean);

const MAX_MENSAGENS = 12;          // histórico enviado por pergunta
const MAX_CARACTERES = 1500;       // por mensagem
const LIMITE_POR_IP = 20;          // perguntas por janela
const JANELA_MS = 10 * 60 * 1000;  // 10 minutos

// Lê a chave de forma explícita (no Deno o SDK pode não enxergar process.env).
const CHAVE = (Deno.env.get("ANTHROPIC_API_KEY") ?? "").trim();
if (!CHAVE) console.error("pergunte: segredo ANTHROPIC_API_KEY ausente ou vazio");
const client = new Anthropic({ apiKey: CHAVE || undefined });

// Limite simples por IP, em memória (vale por instância; não é à prova de abuso).
const contagem = new Map<string, { n: number; desde: number }>();
function permitido(ip: string): boolean {
  const agora = Date.now();
  const c = contagem.get(ip);
  if (!c || agora - c.desde > JANELA_MS) {
    contagem.set(ip, { n: 1, desde: agora });
    return true;
  }
  c.n += 1;
  return c.n <= LIMITE_POR_IP;
}

// Catálogo e fichas do próprio site, para a IA indicar só o que existe.
let contexto = { texto: "", em: 0 };
async function contextoDoSite(): Promise<string> {
  if (contexto.texto && Date.now() - contexto.em < 60 * 60 * 1000) return contexto.texto;
  const partes: string[] = [];
  try {
    const p = await (await fetch(`${SITE}/produtos.json`)).json();
    partes.push("PRODUTOS DO CATÁLOGO (preço visto na data indicada; links de afiliado):");
    for (const x of p.produtos ?? []) {
      partes.push(`- ${x.nome} | passo: ${x.passo} | pele: ${(x.tipos ?? []).join(", ")} | ativos: ${(x.ativos ?? []).join(", ")} | R$ ${x.preco} em ${x.preco_em} | ${x.link}`);
    }
  } catch { /* segue sem catálogo */ }
  try {
    const f = await (await fetch(`${SITE}/ingredientes/ingredientes.json`)).json();
    partes.push("", "FICHAS DE INGREDIENTES DO SITE:");
    for (const x of f) partes.push(`- ${x.nome}: evidência ${x.evidencia} (${x.evidencia_motivo}) ${SITE}${x.url}`);
  } catch { /* segue sem fichas */ }
  contexto = { texto: partes.join("\n"), em: Date.now() };
  return contexto.texto;
}

const INSTRUCOES = `Você é a assistente de dúvidas do site Produto Skincare (${SITE}). Responda em português do Brasil, com calor e clareza, em textos curtos (até uns 180 palavras, listas quando ajudar). Comece a resposta visível logo.

Escopo: cuidados com a pele (skincare), protetor solar, ingredientes e ativos, rotina, tipos de pele, e o uso do site. Se a pergunta fugir disso, diga com gentileza que só ajuda com skincare.

Segurança, sempre:
- Você não é médica e não faz diagnóstico. Não indique remédios de receita nem doses de medicamentos.
- Para feridas que não cicatrizam, pintas que mudam, acne com nódulos ou dor, reação alérgica forte, rosácea, melasma persistente ou qualquer dúvida de saúde: recomende procurar um dermatologista, em destaque.
- Gestação e amamentação: diga para confirmar com o médico; evite sugerir retinoides.
- Diga quando a evidência sobre um ativo é limitada. Não invente estudos, números, preços nem produtos.

Produtos: só cite produtos da lista abaixo, no máximo 2 por resposta e só quando ajudar de verdade, com o preço e a data em que foi visto e o link. Avise que são links de afiliado. Quando fizer sentido, indique páginas do site: ${SITE}/provador/ (quiz de pele), ${SITE}/rotina-de-skincare/, ${SITE}/ingredientes/, ${SITE}/condicoes/, ${SITE}/ferramentas/ingredientes/.

Formatação: texto simples com **negrito** e listas com "- ". Links como URL completa.`;

function cors(origem: string | null): Record<string, string> {
  const ok = origem && (ORIGENS.includes(origem) || /^http:\/\/localhost(:\d+)?$/.test(origem));
  return {
    "Access-Control-Allow-Origin": ok ? origem! : ORIGENS[0],
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Access-Control-Allow-Headers": "content-type, authorization, apikey, x-client-info",
    "Vary": "Origin",
  };
}

function erro(status: number, mensagem: string, h: Record<string, string>) {
  return new Response(JSON.stringify({ erro: mensagem }), {
    status,
    headers: { ...h, "Content-Type": "application/json; charset=utf-8" },
  });
}

Deno.serve(async (req) => {
  const h = cors(req.headers.get("origin"));
  if (req.method === "OPTIONS") return new Response(null, { headers: h });
  if (req.method !== "POST") return erro(405, "Use POST.", h);

  const ip = (req.headers.get("x-forwarded-for") ?? "").split(",")[0].trim() || "anon";
  if (!permitido(ip)) return erro(429, "Muitas perguntas seguidas. Espere alguns minutos e tente de novo.", h);

  let corpo: { mensagens?: { papel?: string; texto?: string }[] };
  try { corpo = await req.json(); } catch { return erro(400, "Pedido inválido.", h); }

  const mensagens = (corpo.mensagens ?? []).slice(-MAX_MENSAGENS)
    .filter((m) => (m.papel === "user" || m.papel === "assistant") && typeof m.texto === "string" && m.texto.trim())
    .map((m) => ({ role: m.papel as "user" | "assistant", content: m.texto!.slice(0, MAX_CARACTERES) }));
  while (mensagens.length && mensagens[0].role !== "user") mensagens.shift();
  if (!mensagens.length || mensagens[mensagens.length - 1].role !== "user") return erro(400, "Envie uma pergunta.", h);

  const sistema = [
    { type: "text" as const, text: INSTRUCOES + "\n\n" + (await contextoDoSite()), cache_control: { type: "ephemeral" as const } },
  ];

  const enc = new TextEncoder();
  if (!CHAVE) {
    console.error("pergunte: chamada sem ANTHROPIC_API_KEY");
    return new Response("A IA ainda não está configurada neste site. Tente mais tarde.", {
      headers: { ...h, "Content-Type": "text/plain; charset=utf-8", "Cache-Control": "no-store" },
    });
  }
  const corpoResposta = new ReadableStream({
    async start(controller) {
      try {
        // O Haiku não tem modelo de reserva quando recusa: a recusa é tratada abaixo (stop_reason "refusal").
        const stream = client.messages.stream({
          model: MODELO,
          max_tokens: 2000,
          output_config: { effort: "low" }, // conversa curta: esforço baixo é suficiente e mais rápido
          system: sistema,
          messages: mensagens,
        });

        for await (const ev of stream) {
          if (ev.type === "content_block_delta" && ev.delta.type === "text_delta") {
            controller.enqueue(enc.encode(ev.delta.text));
          }
        }
        const final = await stream.finalMessage();
        if (final.stop_reason === "refusal") {
          controller.enqueue(enc.encode("\n\nNão consigo responder a essa pergunta. Para questões de saúde da pele, procure um dermatologista."));
        } else if (final.stop_reason === "max_tokens") {
          controller.enqueue(enc.encode("\n\n(Resposta cortada por tamanho. Peça para eu continuar.)"));
        }
      } catch (e) {
        const status = e instanceof Anthropic.APIError ? e.status : 0;
        // Só o tipo e a mensagem do erro: nunca o conteúdo da conversa.
        const err = e as { name?: string; message?: string };
        console.error("pergunte: falha na API", status, err?.name ?? "", String(err?.message ?? "").slice(0, 300));
        controller.enqueue(enc.encode(status === 429
          ? "\n\nA IA está muito ocupada agora. Tente de novo em instantes."
          : "\n\nNão consegui responder agora. Tente de novo em instantes."));
      } finally {
        controller.close();
      }
    },
  });

  return new Response(corpoResposta, {
    headers: { ...h, "Content-Type": "text/plain; charset=utf-8", "Cache-Control": "no-store" },
  });
});
