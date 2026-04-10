# ── Frontend: React + Vite → Nginx ───────────────────────────────────────────
# Stage 1: Build
FROM node:20-alpine AS builder

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .
# Адрес бэкенда для продакшена: в docker-compose бэкенд доступен как "backend:8000"
# При необходимости переопределите через ARG VITE_API_URL
ARG VITE_API_URL=http://localhost:8000
ENV VITE_API_URL=${VITE_API_URL}

RUN npm run build

# Stage 2: Nginx
FROM nginx:1.25-alpine

# Конфиг nginx — проксирует API-запросы на бэкенд
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
