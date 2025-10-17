# Deploy e Ambiente

## Visão Geral
- Frontend na Vercel (Next.js) com variáveis `NEXT_PUBLIC_*`.
- Backend na Railway com build por Docker (usa `Dockerfile` na raiz).
- Segredos e chaves só nas plataformas (Dashboard), nunca no repo.

## Frontend (Vercel)
- Variáveis em “Project Settings” → “Environment Variables”:
  - `NEXT_PUBLIC_BACKEND_URL` = `https://chatagno3afrios-production.up.railway.app`
  - `NEXT_PUBLIC_SUPABASE_URL` = `<URL do seu Supabase>`
  - `NEXT_PUBLIC_SUPABASE_ANON_KEY` = `<anon key do Supabase>`
- Em dev local, crie `.env.local` a partir de `.env.local.example`.
- Após atualizar as variáveis, faça um redeploy na Vercel.

## Backend (Railway)
- Serviço do backend deve usar “Use Dockerfile” (raiz `.`).
- Conectar ao repositório GitHub e habilitar “Deploy on Push”.
- Variáveis em “Variables” do serviço (não commitar no repo):
  - `ALLOWED_ORIGINS` = `https://dashboard-3afrios-agno.vercel.app,http://localhost:3000`
  - `SUPABASE_URL` = `<URL do Supabase>`
  - `SUPABASE_SERVICE_ROLE` = `<Service Role>`
  - `EVOLUTION_ENABLED` = `0` (mude para `1` quando tiver credenciais)
  - `EVOLUTION_BASE_URL`, `EVOLUTION_API_KEY`, `EVOLUTION_INSTANCE_ID`, `EVOLUTION_SEND_TEXT_PATH`
  - `OPENAI_ENABLED`, `OPENAI_API_KEY`, `OPENAI_MODEL` (se for usar)
  - `GOOGLE_ENABLED=0` por enquanto (ou configure todos os `GOOGLE_*` ao habilitar)
- Observações:
  - Não inclua domínio da Railway em `ALLOWED_ORIGINS`; só Vercel/localhost.
  - Sem curingas em CORS; precisa refletir `Origin` exatamente.
  - A Railway injeta `PORT` automaticamente; não precisa definir.

## Fluxo de Deploy
1) Commit/push no GitHub (branch configurada).
2) Railway: build por Docker, sobe `uvicorn server.main:app`.
3) Vercel: build do Next.js com `NEXT_PUBLIC_*` configuradas.

## Testes Rápidos
- Health do backend:
  - `https://SEU-SERVICO.up.railway.app/health`
- Preflight CORS:
  - Origin: `https://dashboard-3afrios-agno.vercel.app`
  - Método: `POST` para `/webhook`
- Proxy do frontend:
  - `https://SEU_FRONTEND.vercel.app/api/webhook` deve retornar OK com backend no ar.

## Desenvolvimento Local
- Frontend:
  - `.env.local` com `NEXT_PUBLIC_*`
  - `npm run dev`
- Backend:
  - `.env` com variáveis mínimas (`ALLOWED_ORIGINS`, `SUPABASE_*`)
  - `pip install -r server/requirements.txt`
  - `python -m uvicorn server.main:app --host 0.0.0.0 --port 8000`