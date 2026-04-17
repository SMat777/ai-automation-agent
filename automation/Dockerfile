FROM node:20-slim

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm ci --omit=dev

COPY src/ src/
COPY tsconfig.json .

CMD ["npx", "tsx", "src/index.ts"]
