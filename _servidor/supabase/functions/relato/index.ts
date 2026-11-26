// Supabase Edge Function "relato": recebe o aviso "este frasco está diferente do anterior?"
// das fichas de produto e grava uma linha na tabela relatos_frasco.
//
// O que é gravado: o id do produto, o que mudou (cheiro, textura, cor, ardência) e o dia.
// O que NÃO é gravado: IP, navegador, texto livre, qualquer identificação de quem enviou.
// O IP só é usado em memória, para limitar envios seguidos, e não vai para o banco nem para o log.
//
// O relato não aparece no site nem vira selo sozinho. Ele serve para o editor decidir qual produto
// conferir de novo na loja; a mudança só é publicada quando entra no Extrato do cosmético
// (produtos/mudancas.json), com data e fonte.
//
// Variáveis: SUPABASE_URL e SUPABASE_SERVICE_ROLE_KEY já existem em toda Edge Function.
//   ALLOWED_ORIGINS  opcional, separado por vírgula (padrão: o domínio do site)
import { createClient } from "npm:@supabase/supabase-js@2";

const SITE = "https://produtoskincare.com.br";
const ORIGENS = (Deno.env.get("ALLOWED_ORIGINS") ?? `${SITE},https://www.produtoskincare.com.br`)
  .split(",").map((o) => o.trim()).filter(Boolean);
const MUDANCAS = ["cheiro", "textura", "cor", "ardencia"];
const LIMITE_POR_IP = 5;                 // relatos por janela
const JANELA_MS = 24 * 60 * 60 * 1000;   // 24 horas

const banco = createClient(Deno.env.get("SUPABASE_URL") ?? "", Deno.env.get("SUPABASE_SERVICE_ROLE_KEY") ?? "",
  { auth: { persistSession: false } });

// Limite simples por IP, em memória (vale por instância; não é à prova de abuso).
const contagem = new Map<string, { n: number; desde: number }>();
function permitido(ip: string): boolean {
  const agora = Date.now();
  const c = contagem.get(ip);
  if (!c || agora - c.desde > JANELA_MS) { contagem.set(ip, { n: 1, desde: agora }); return true; }
  c.n += 1;
  return c.n <= LIMITE_POR_IP;
}

// Só aceita produto que existe no catálogo do site.
let catalogo = { ids: new Set<string>(), em: 0 };
async function produtoExiste(id: string): Promise<boolean> {
  if (!catalogo.ids.size || Date.now() - catalogo.em > 60 * 60 * 1000) {
    try {
      const p = await (await fetch(`${SITE}/produtos.json`)).json();
      catalogo = { ids: new Set((p.produtos ?? []).map((x: { id: string }) => x.id)), em: Date.now() };
    } catch { /* mantém o catálogo anterior, se houver */ }
  }
  return catalogo.ids.has(id);
}

function cabecalhos(origem: string | null): Record<string, string> {
  const h: Record<string, string> = { "Vary": "Origin", "Cache-Control": "no-store" };
  if (origem && ORIGENS.includes(origem)) {
    h["Access-Control-Allow-Origin"] = origem;
    h["Access-Control-Allow-Headers"] = "content-type, authorization, apikey";
    h["Access-Control-Allow-Methods"] = "POST, OPTIONS";
  }
  return h;
}

function resposta(status: number, corpo: Record<string, unknown>, h: Record<string, string>): Response {
  return new Response(JSON.stringify(corpo), { status, headers: { ...h, "Content-Type": "application/json; charset=utf-8" } });
}

Deno.serve(async (req) => {
  const h = cabecalhos(req.headers.get("origin"));
  if (req.method === "OPTIONS") return new Response(null, { status: 204, headers: h });
  if (req.method !== "POST") return resposta(405, { erro: "Use POST." }, h);

  const ip = (req.headers.get("x-forwarded-for") ?? "").split(",")[0].trim() || "anon";
  if (!permitido(ip)) return resposta(429, { erro: "Muitos relatos seguidos deste endereço. Tente de novo amanhã." }, h);

  let corpo: { produto?: unknown; mudou?: unknown };
  try { corpo = await req.json(); } catch { return resposta(400, { erro: "Pedido inválido." }, h); }

  const produto = typeof corpo.produto === "string" ? corpo.produto.trim().slice(0, 80) : "";
  const mudou = Array.isArray(corpo.mudou)
    ? [...new Set(corpo.mudou.filter((m): m is string => typeof m === "string" && MUDANCAS.includes(m)))]
    : [];
  if (!produto || !mudou.length) return resposta(400, { erro: "Diga o produto e o que mudou." }, h);
  if (!(await produtoExiste(produto))) return resposta(400, { erro: "Produto fora do catálogo." }, h);

  const { error } = await banco.from("relatos_frasco").insert({ produto, mudou });
  if (error) {
    console.error("relato: falha ao gravar", error.code ?? "", String(error.message ?? "").slice(0, 200));
    return resposta(500, { erro: "Não foi possível registrar agora." }, h);
  }
  return resposta(200, { ok: true }, h);
});
