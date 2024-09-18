# Use the official Node 20 image as the base image
FROM node:20

# Set the working directory inside the container
WORKDIR /app

# Copy package.json and package-lock.json to the working directory
COPY package*.json ./

# Install app dependencies
RUN npm install

# Copy the rest of the app source code to the working directory
COPY . .

# Expose port 3000
EXPOSE 3000

# Start the Node.js app
CMD [ "node", "app.js" ]