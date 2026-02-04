# Use Node.js environment
FROM node:20-slim

WORKDIR /app

# Copy package.json and install dependencies
COPY package.json ./
# copying package-lock.json if it existed would be better, but we only saw package.json
RUN npm install

# Copy source code
COPY . .

# Expose port (Vite default is 5173, but config says 3000)
EXPOSE 3000

# Start development server
CMD ["npm", "run", "dev"]
