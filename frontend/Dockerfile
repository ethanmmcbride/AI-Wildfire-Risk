# ── Frontend (React + Vite) ──────────────────────────────────────────────────

# --- Stage 1: Build ---
FROM node:20-alpine AS build

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm ci

COPY . .
RUN npm run build

# --- Stage 2: Serve ---
FROM nginx:stable-alpine AS production

# Copy built assets to nginx
COPY --from=build /app/dist /usr/share/nginx/html

# SPA fallback: send all routes to index.html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
