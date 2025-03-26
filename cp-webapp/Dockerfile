# Base image for dependencies and building
FROM node:23-alpine AS builder

# Install pnpm
RUN npm install -g pnpm

# Set working directory
WORKDIR /app

# Copy package.json and related files
COPY package.json pnpm-lock.yaml* ./

# Install dependencies
RUN pnpm install --frozen-lockfile

# Copy application code
COPY . .

# Add environment file handling
ARG ENV_FILE=.env.development
ARG ENV=development
COPY ${ENV_FILE} .env.${ENV}
ENV ENV=${ENV}

# Build the application
RUN pnpm build

# Production image
FROM node:23-alpine AS runner
WORKDIR /app

# Pass ARG from previous stage
ARG ENV
ENV ENV=${ENV}
ENV NODE_ENV production

# Install pnpm
RUN npm install -g pnpm

# Copy necessary files from builder stage
COPY --from=builder /app/next.config.ts ./
COPY --from=builder /app/public ./public
COPY --from=builder /app/package.json ./package.json
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/.env.${ENV} ./.env.${ENV}

# Set environment variable
ENV ENV=${ENV}

# Run the application
CMD ["pnpm", "start"]

# Expose the port the app will run on
EXPOSE 3000
