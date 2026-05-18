# DentalFlow EHR API - Docker Image
# Mock EHR REST API for local development and demo

FROM node:20-alpine

WORKDIR /app

# Install dependencies
COPY package.json .
RUN npm install --production

# Copy source
COPY server.js .

# Port
ENV PORT=3001
EXPOSE 3001

# Health check
HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=3 \
  CMD node -e "require('http').get('http://localhost:3001/health', r => process.exit(r.statusCode === 200 ? 0 : 1))"

CMD ["node", "server.js"]
