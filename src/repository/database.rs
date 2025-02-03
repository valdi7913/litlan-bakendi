use diesel::prelude::*;
use diesel::r2d2::{self, ConnectionManager};
use diesel_migrations::{embed_migrations, EmbeddedMigrations, MigrationHarness};
use dotenv::dotenv;
use std::env;

pub const MIGRATIONS: EmbeddedMigrations = embed_migrations!(); // Embeds the migrations from the "./migrations" directory

type DBPool = r2d2::Pool<ConnectionManager<PgConnection>>;

pub struct Database {
    pub pool: DBPool,
}

impl Database {
    /// Creates a new Database instance, sets up the connection pool,
    /// and runs any pending migrations.
    pub fn new() -> Self {
        dotenv().ok();
        
        let database_url = env::var("DATABASE_URL")
            .expect("DATABASE_URL must be set in .env");
        
        let manager = ConnectionManager::<PgConnection>::new(database_url);
        let pool: DBPool = r2d2::Pool::builder()
            .build(manager)
            .expect("Failed to create pool.");

        Self::run_migrations(&pool);
        
        Database { pool }
    }

    /// Runs all pending migrations using the embedded migrations.
    pub fn run_migrations(pool: &DBPool) {
        // Get a mutable connection from the pool; MigrationHarness requires a mutable reference.
        let mut conn = pool.get().expect("Failed to get database connection");

        // Run pending migrations. This call applies any migrations that have not yet been run.
        match conn.run_pending_migrations(MIGRATIONS) {
            Ok(report) => {
                println!("Migrations ran successfully!");
                for migration in report {
                    println!("Applied migration: {}", migration);
                }
            },
            Err(e) => eprintln!("Error running migrations: {}", e),
        }
    }
}

