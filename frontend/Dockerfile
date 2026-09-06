# Multi-stage build for frontend
FROM node:20-alpine AS build

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

# Production serve stage using lightweight nginx
FROM nginx:alpine

COPY --from=build /app/dist /usr/share/nginx/html

# Custom nginx config to proxy API requests to backend
RUN echo 'server { \
    listen 80; \
    location / { \
        root /usr/share/nginx/html; \
        index index.html index.htm; \
        try_files $uri $uri/ /index.html; \
    } \
    location /api/ { \
        proxy_pass https://varuna-sonar-backend.onrender.com/api/; \
        proxy_set_header Host varuna-sonar-backend.onrender.com; \
        proxy_set_header X-Real-IP $remote_addr; \
        proxy_ssl_server_name on; \
    } \
    location /static/ { \
        proxy_pass https://varuna-sonar-backend.onrender.com/static/; \
        proxy_set_header Host varuna-sonar-backend.onrender.com; \
        proxy_ssl_server_name on; \
    } \
}' > /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
