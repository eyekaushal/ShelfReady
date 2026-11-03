# Local development image (used by docker-compose). Vercel builds the production bundle itself.
FROM node:22-alpine

WORKDIR /app

# Install dependencies first, so Docker can cache this layer between code changes.
COPY package.json package-lock.json ./
RUN npm ci

COPY . .

EXPOSE 5173
# --host so the dev server is reachable from outside the container.
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
