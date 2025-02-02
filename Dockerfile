# Use Rust official image
FROM rust:1.84.1 AS builder

# Set the working directory inside the container
WORKDIR /usr/src/app

# Copy Cargo files first (to leverage Docker caching)
COPY Cargo.toml Cargo.lock ./

# Copy the source code
COPY . .

# Build the Rust project in release mode
RUN cargo build --release

# Use a smaller runtime image for final deployment
FROM rust:1.84.1 

# Set working directory inside the final container
WORKDIR /app

# Copy the built binary from the builder stage
COPY --from=builder /usr/src/app/target/release/litlan-backend /app/

# Expose the necessary port (if applicable)
EXPOSE 8080  

# Run the binary
CMD ["./litlan-backend"]

