// Worker mínimo do produtoskincare.com.br.
// O site continua sendo só arquivos estáticos; este script roda apenas para os .mp4
// (ver "run_worker_first" no wrangler.jsonc) e existe por um motivo: os arquivos
// estáticos da Cloudflare respondem pedidos por trecho ("Range: bytes=...") com o
// arquivo inteiro (200), e aí o navegador não consegue avançar/voltar no vídeo
// (e o Safari do iPhone pode nem tocar). Aqui o trecho pedido é recortado e
// devolvido com status 206.
// A pasta começa com _, então fica fora do site publicado (.assetsignore).

export default {
  async fetch(request, env) {
    const range = request.headers.get("Range");
    if ((request.method !== "GET" && request.method !== "HEAD") || !range) {
      return comAcceptRanges(await env.ASSETS.fetch(request));
    }

    // Pede o arquivo inteiro, sem o Range.
    const headers = new Headers(request.headers);
    headers.delete("Range");
    headers.delete("If-Range");
    // Sempre GET por dentro: um HEAD voltaria sem corpo e sem como medir o trecho.
    const resp = await env.ASSETS.fetch(new Request(request, { method: "GET", headers }));
    if (resp.status !== 200) return resp;

    // If-Range: se a versão do arquivo mudou, manda o arquivo inteiro.
    const ifRange = request.headers.get("If-Range");
    const etag = resp.headers.get("ETag");
    if (ifRange && ifRange !== etag) {
      return comAcceptRanges(request.method === "HEAD" ? new Response(null, resp) : resp);
    }

    const corpo = await resp.arrayBuffer();
    const total = corpo.byteLength;
    const trecho = lerRange(range, total);
    const saida = new Headers(resp.headers);
    saida.set("Accept-Ranges", "bytes");

    if (trecho === null) {
      // Formato que não tratamos (por exemplo, vários trechos): arquivo inteiro.
      return new Response(request.method === "HEAD" ? null : corpo, { status: 200, headers: saida });
    }
    if (trecho === "fora") {
      saida.set("Content-Range", `bytes */${total}`);
      saida.delete("Content-Length");
      return new Response(null, { status: 416, headers: saida });
    }

    const [inicio, fim] = trecho;
    saida.set("Content-Range", `bytes ${inicio}-${fim}/${total}`);
    saida.set("Content-Length", String(fim - inicio + 1));
    return new Response(request.method === "HEAD" ? null : corpo.slice(inicio, fim + 1), {
      status: 206,
      headers: saida,
    });
  },
};

// "bytes=100-199", "bytes=100-" ou "bytes=-500" -> [início, fim];
// "fora" se não couber no arquivo; null se não for um único trecho válido.
function lerRange(valor, total) {
  const m = /^bytes=(\d*)-(\d*)$/.exec(valor.trim());
  if (!m || (m[1] === "" && m[2] === "")) return null;
  let inicio, fim;
  if (m[1] === "") {
    const sufixo = Number(m[2]);
    if (sufixo === 0) return "fora";
    inicio = Math.max(0, total - sufixo);
    fim = total - 1;
  } else {
    inicio = Number(m[1]);
    if (m[2] !== "" && Number(m[2]) < inicio) return null;
    if (inicio >= total) return "fora";
    fim = m[2] === "" ? total - 1 : Math.min(Number(m[2]), total - 1);
  }
  return [inicio, fim];
}

function comAcceptRanges(resp) {
  if (resp.status !== 200) return resp;
  const r = new Response(resp.body, resp);
  r.headers.set("Accept-Ranges", "bytes");
  return r;
}
