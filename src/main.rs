mod models;
mod handlers;

use actix_web::{get, App, HttpServer, Responder, web};
use serde::Serialize;
use sqlx::{PgPool, postgres::PgQueryResult};
use dotenv::dotenv;
use std::env; 
use handlers::crossword_handlers::{get_crossword};

#[actix_web::main]
async fn main() -> std::io::Result<()> {
    dotenv().ok();

//    let database_url = env::var("DATABASE_URL")
//        .expect("DATABASE_URL must be set in .env");
//
//    let pool = PgPool::connect(&database_url)
//        .await
//        .expect("Failed to connect to the database.");

    println!("Connected to database");
    HttpServer::new(move || {
        App::new()
            .route("/crossword", web::get().to(get_crossword))
    })
    .bind(("0.0.0.0", 8080))?
    .run()
    .await
}


