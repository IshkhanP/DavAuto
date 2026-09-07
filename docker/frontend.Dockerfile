FROM node:20-alpine

WORKDIR /app

# Copy package files first for layer caching
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install

# Copy the rest of the frontend source
COPY frontend/ .

EXPOSE 5173

CMD ["npm", "run", "dev"]