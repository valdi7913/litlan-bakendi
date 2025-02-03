mod models;
mod handlers;
mod repository;

use actix_web::{get, App, HttpServer, Responder, web};
use serde::Serialize;
use sqlx::{PgPool, postgres::PgQueryResult};
use dotenv::dotenv;
use std::env; 
use handlers::crossword_handlers::{get_crossword};

#[actix_web::main]
async fn main() -> std::io::Result<()> {
    dotenv().ok();
    
    let database = repository::database::Database::new();
    let app_data = web::Data::new(database);

    println!("Connected to database");
    HttpServer::new(move || {
        App::new()
            .app_data(app_data.clone())
            .route("/crossword", web::get().to(get_crossword))
    })
    .bind(("0.0.0.0", 8080))?
    .run()
    .await
}


