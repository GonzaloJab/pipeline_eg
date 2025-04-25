# Use Node.js base image
FROM node:16-slim

# Set the working directory
WORKDIR /app

# Copy package.json and install dependencies
COPY frontend/package.json .
RUN npm install

# Copy the rest of the frontend code
COPY frontend/ .

# Expose the port for the frontend
EXPOSE 3000

# Start the Node.js server
CMD ["node", "server.js"]
