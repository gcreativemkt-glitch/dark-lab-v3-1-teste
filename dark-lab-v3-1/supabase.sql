-- Executar uma única vez no SQL Editor do SEU projeto Supabase.
-- O serviço usa a chave secreta APENAS no servidor Streamlit e exige uma senha no app.
create table if not exists public.watchlist (
    channel_id text primary key,
    title text not null,
    note text default '',
    created_at timestamptz not null default now()
);
create table if not exists public.projects (
    id uuid primary key,
    name text not null,
    niche text default '',
    status text default 'Ideia',
    notes text default '',
    created_at timestamptz not null default now()
);
create table if not exists public.channel_snapshots (
    channel_id text not null,
    recorded_on date not null,
    subscribers bigint,
    views bigint,
    video_count integer,
    primary key(channel_id, recorded_on)
);
-- Nenhum acesso público/anônimo pelo cliente: o app acessa essas tabelas no servidor.
alter table public.watchlist enable row level security;
alter table public.projects enable row level security;
alter table public.channel_snapshots enable row level security;

-- Histórico de observações, para medir crescimento entre dias de coleta.
create table if not exists public.video_snapshots (
  video_id text not null,
  recorded_on date not null,
  views bigint not null,
  primary key (video_id, recorded_on)
);
alter table public.video_snapshots enable row level security;
