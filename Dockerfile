FROM node:20-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production

# Copy source code
COPY . .

# Build the application
RUN npm run build

# Expose port for HTTP/SSE transport
EXPOSE 3000

# Run the server
CMD ["node", "dist/index.js"]
