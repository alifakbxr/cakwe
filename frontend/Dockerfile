# Stage 1: Build static assets
FROM node:24-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

# Stage 2: Serve with lightweight Nginx
FROM nginx:alpine-slim
COPY --from=builder /app/dist /usr/share/nginx/html

# Reverse proxy /api to backend
# Reverse proxy /api to backend with extended timeout for AI generation
RUN echo 'server { \
    listen 80; \
    location / { \
        root /usr/share/nginx/html; \
        index index.html; \
        try_files $uri $uri/ /index.html; \
    } \
    location /api/ { \
        proxy_pass http://backend:8000; \
        proxy_set_header Host $host; \
        proxy_set_header X-Real-IP $remote_addr; \
        proxy_connect_timeout 300s; \
        proxy_send_timeout 300s; \
        proxy_read_timeout 300s; \
        send_timeout 300s; \
        client_max_body_size 20M; \
    } \
}' > /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
