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


# Production stage with Nginx
FROM nginx:alpine AS production
WORKDIR /usr/share/nginx/html
# Copy built assets to nginx html directory
COPY --from=build /app/dist ./
# Expose ports
EXPOSE 80 443
CMD ["nginx", "-g", "daemon off;"]
