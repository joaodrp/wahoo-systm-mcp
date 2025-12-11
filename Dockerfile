# Build stage
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install all dependencies (including dev dependencies for build)
RUN npm ci

# Copy source code
COPY . .

# Build the application
RUN npm run build

# Production stage
FROM node:20-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install only production dependencies, skip scripts (husky)
RUN npm ci --omit=dev --ignore-scripts

# Copy built application from builder
COPY --from=builder /app/dist ./dist

# Expose port for HTTP/SSE transport
EXPOSE 3000

# Run the server
CMD ["node", "dist/src/index.js"]
