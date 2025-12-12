# Build stage
FROM node:20-alpine AS build

WORKDIR /app

# Copy package files
COPY package*.json ./
COPY tsconfig*.json ./
COPY vite.config.ts ./
COPY tailwind.config.ts ./
COPY postcss.config.js ./
COPY eslint.config.js ./
COPY components.json ./
COPY index.html ./

# Copy source code
COPY src ./src
COPY public ./public

# Install dependencies
RUN npm ci

# Build the application
RUN npm run build

# Production stage (Nginx)
FROM nginx:alpine

# Remove default nginx config
RUN rm -f /etc/nginx/conf.d/default.conf

# Copy built application to nginx
COPY --from=build /app/dist /usr/share/nginx/html

# Create nginx config with proper routing
RUN cat > /etc/nginx/conf.d/default.conf << 'EOF'
server {
    listen 80;
    server_name _;
    
    # Gzip compression
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 6;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    # Root location for SPA
    location / {
        root /usr/share/nginx/html;
        try_files $uri $uri/ /index.html;
        expires 1h;
        add_header Cache-Control "public, immutable";
    }
    
    # Static assets with long cache
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        root /usr/share/nginx/html;
        expires 30d;
        add_header Cache-Control "public, immutable";
        access_log off;
    }
    
    # Disable caching for html files
    location ~* \.html?$ {
        root /usr/share/nginx/html;
        expires -1;
        add_header Cache-Control "public, must-revalidate, proxy-revalidate";
    }
}
EOF

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
