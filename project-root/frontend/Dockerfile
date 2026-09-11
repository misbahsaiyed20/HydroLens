# Not build-tested in the environment this was written in (no Docker
# daemon available there). Verify with `docker build .` before relying on
# it. NEXT_PUBLIC_API_BASE_URL must be passed at build time since Next.js
# inlines NEXT_PUBLIC_* vars into the client bundle — it cannot be changed
# at container runtime without a rebuild.
FROM node:20-slim AS build
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm install
COPY . .
ARG NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api
ENV NEXT_PUBLIC_API_BASE_URL=$NEXT_PUBLIC_API_BASE_URL
RUN npm run build

FROM node:20-slim
WORKDIR /app
ENV NODE_ENV=production
COPY --from=build /app/.next ./.next
COPY --from=build /app/node_modules ./node_modules
COPY --from=build /app/package.json ./package.json
EXPOSE 3000
CMD ["npm", "start"]
