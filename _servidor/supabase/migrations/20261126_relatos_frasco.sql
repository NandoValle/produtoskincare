-- Relatos "este frasco está diferente do anterior?" enviados pelas fichas de produto.
-- Guarda só o produto, o que mudou e o dia. Sem IP, sem texto livre, sem identificação de quem enviou.
-- Só a função "relato" grava (com a chave de serviço). Ninguém lê nem grava pela chave pública:
-- a tabela tem RLS ligada e nenhuma política.

create table if not exists public.relatos_frasco (
  id      bigint generated always as identity primary key,
  produto text   not null check (char_length(produto) between 1 and 80),
  mudou   text[] not null check (
            cardinality(mudou) between 1 and 4
            and mudou <@ array['cheiro', 'textura', 'cor', 'ardencia']::text[]),
  dia     date   not null default (now() at time zone 'America/Sao_Paulo')::date
);

create index if not exists relatos_frasco_produto_dia on public.relatos_frasco (produto, dia);

alter table public.relatos_frasco enable row level security;
revoke all on public.relatos_frasco from anon, authenticated;

-- Leitura para a revisão do editor (painel do Supabase > SQL Editor):
--   select * from public.relatos_frasco_30d;
-- Relato não é prova: serve para decidir qual produto conferir de novo na loja e registrar no Extrato.
create or replace view public.relatos_frasco_30d
with (security_invoker = true) as
select produto,
       count(*)                                         as relatos,
       count(*) filter (where 'cheiro'   = any (mudou)) as cheiro,
       count(*) filter (where 'textura'  = any (mudou)) as textura,
       count(*) filter (where 'cor'      = any (mudou)) as cor,
       count(*) filter (where 'ardencia' = any (mudou)) as ardencia,
       min(dia) as primeiro, max(dia) as ultimo
from public.relatos_frasco
where dia >= (now() at time zone 'America/Sao_Paulo')::date - 30
group by produto
order by relatos desc;

revoke all on public.relatos_frasco_30d from anon, authenticated;
