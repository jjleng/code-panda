# Stage 1: Build the Go binary
FROM golang:1.23-alpine AS builder

# Install build dependencies
RUN apk add --no-cache git

WORKDIR /app

# Copy only dependency files first
COPY go.mod go.sum ./
RUN go mod download

# Copy source and build
COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-w -s" -o /app/runner .

FROM alpine:3.21 AS final

# Add runtime dependencies and security
# tini is used as an init process to handle signals and reap zombie processes
RUN apk add --no-cache git ca-certificates tini nodejs pnpm

WORKDIR /app
COPY --from=builder /app/runner .
COPY static/ /app/static/

# Add environment file handling
ARG ENV_FILE=.env.development
ARG ENV=development
COPY ${ENV_FILE} .env.${ENV}

ENV ENV=${ENV}
ENV CONTROL_PORT=8088
ENV PROXY_PORT=3000

# Use tini as entrypoint
ENTRYPOINT ["/sbin/tini", "--"]
CMD ["./runner", "control", "--port", "${CONTROL_PORT}", "--proxy-port", "${PROXY_PORT}"]