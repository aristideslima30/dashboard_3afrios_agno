# Dashboard 3A Frios 🧊

Dashboard profissional para gestão de leads, conversas e campanhas de marketing da 3A Frios.

## 🛠️ Instalação Rápida - Basta rodar esses  comandos

## ⚡ Instalação Express (se já tem Node.js)

```bash
git clone https://github.com/aristideslima30/Dash-3A-Frios.git
cd Dash-3A-Frios
npm install
npm run dev
```

Acesse: http://localhost:3000

## 📦 Scripts Disponíveis

- `npm run dev` - Executa o projeto em modo de desenvolvimento
- `npm run build` - Cria a versão de produção
- `npm start` - Executa a versão de produção
- `npm run lint` - Executa o linter para verificar o código

## 🏗️ Tecnologias Utilizadas (Mas isso é só pra curirosidade)

- **Next.js 15** - Framework React para produção
- **React 19** - Biblioteca para interfaces de usuário
- **TypeScript** - Superset do JavaScript com tipagem estática
- **Tailwind CSS** - Framework CSS utilitário
- **Radix UI** - Componentes acessíveis e customizáveis
- **Lucide React** - Ícones modernos
- **TanStack Query** - Gerenciamento de estado e cache
- **Supabase** - Backend como serviço

## 📁 Estrutura do Projeto

## 🚀 Deploy na Vercel

Frontend (Next.js 15) está pronto para Vercel.

1. Conecte o repositório GitHub (aristideslima30/Dash-3A-Frios) na Vercel.
2. Configure variáveis de ambiente:
   - `NEXT_PUBLIC_SUPABASE_URL`: URL do projeto Supabase (https://...supabase.co)
   - `NEXT_PUBLIC_SUPABASE_ANON_KEY`: Anon key do Supabase
   - `NEXT_PUBLIC_BACKEND_URL`: URL do backend no Railway (ex.: https://seu-backend.railway.app)
   - `NEXT_PUBLIC_EVOLUTION_SERVER_URL`, `NEXT_PUBLIC_EVOLUTION_INSTANCE`, `NEXT_PUBLIC_EVOLUTION_API_KEY`, `NEXT_PUBLIC_WHATSAPP_DRY_RUN` (opcional)
3. Build:
   - Install: `npm install`
   - Build: `npm run build`
4. Teste rápido: acesse `/api/webhook` para validar o proxy (retorna JSON).

## 🔧 Variáveis de Ambiente

Exemplo disponível em `env.example`. No Vercel:
- `NEXT_PUBLIC_SUPABASE_URL` e `NEXT_PUBLIC_SUPABASE_ANON_KEY` para o cliente.
- `NEXT_PUBLIC_BACKEND_URL` para proxy da rota `/api/webhook` (Next).
- O backend no Railway usa `SUPABASE_URL` e `SUPABASE_SERVICE_ROLE` (não exposto no frontend).

## 🧪 Smoke Test pós-deploy

- `GET https://seu-projeto.vercel.app/api/webhook` deve retornar `{ ok: true, route: 'webhook', mode: 'proxy' }`.
- Leads e conversas devem carregar do Supabase conforme disponíveis.
- Botão Manual ON/OFF visível no viewer; envio de mensagens depende de `NEXT_PUBLIC_BACKEND_URL` configurado.
