# Use Node.js as the base image
FROM node:18

# Set the working directory
WORKDIR /app

# Copy package.json and package-lock.json
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy the entire project
COPY . .

# Build the React app for production
RUN npm run build

# Install `serve` globally
RUN npm install -g serve

# Expose the port `serve` uses
EXPOSE 3000

# Command to run `serve`
CMD ["serve", "-s", "build", "-l", "3000"]
