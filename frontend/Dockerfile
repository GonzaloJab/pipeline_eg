# Use Node.js base image
FROM node:18-slim

# Set the working directory
WORKDIR /app

ARG NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}

# Copy package.json and package-lock.json (if present) and install dependencies
COPY package.json ./
COPY package-lock.json ./
RUN npm install

# Copy the rest of the application
COPY . .

# Build the Next.js app
RUN npm run build

# Expose the port Next.js uses
EXPOSE 3000

# Start the Next.js server
CMD ["npm", "start"]