# Build step
FROM node:20-alpine

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

# Expose standard Vite port
EXPOSE 5173

# Run dev server accessible outside container
CMD ["npm", "run", "dev", "--", "--host"]