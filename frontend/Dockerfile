# зависимости ставятся отдельным слоем – при правке кода npm ci не повторяется;
# Node 24: Vite 8 требует более новый Node, чем 22.16
FROM node:24-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund

# автотесты Vitest
FROM deps AS test
COPY . .
CMD ["npm", "test"]

# сборка: проверка типов (vue-tsc) и production-бандл Vite
FROM deps AS build
COPY . .
# адрес бэкенда: пусто – тот же домен через nginx; для GitHub Pages передаётся адрес Render
ARG VITE_API_BASE_URL=
ARG BASE=/
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
RUN npm run build -- --base=$BASE

# раздача собранной статики через nginx
FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
