use actix_web::{get, App, HttpResponse, HttpServer, Responder};
use serde::Serialize;
use chrono::{DateTime, Utc};
use sqlx::{PgPool, postgres::PgQueryResult};
use dotenv::dotenv;
use std::env; 

#[actix_web::main]
async fn main() -> std::io::Result<()> {
    dotenv().ok();

    let database_url = env::var("DATABASE_URL")
        .expect("DATABASE_URL must be set in .env");

//    let pool = PgPool::connect(&database_url)
//        .await
//        .expect("Failed to connect to the database.");


    HttpServer::new(|| {
        App::new()
        .service(hello)
        .service(crossword)
    })
    .bind(("127.0.0.1", 8080))?
    .run()
    .await
}

#[derive(Serialize)]
struct CrossWord {
    id: i32,
    date: DateTime::<Utc>,
    width: u8,
    height: u8,
}

impl CrossWord {
    fn new() -> Self {
        CrossWord {
            id: 1,
            date:chrono::Local::now().with_timezone(&Utc),
            width: 5u8,
            height: 5u8,
        }
    }
}

#[get("/")]
async fn hello() -> impl Responder {
    HttpResponse::Ok().body("Hello World")
}

#[get("/crossword")]
async fn crossword() -> impl Responder {
    let crossword = CrossWord::new();
    match serde_json::to_string(&crossword) {
        Ok(data) => HttpResponse::Ok()
            .content_type("application/json")
            .body(data),
        Err(_) => HttpResponse::InternalServerError().body("Failed to serialize crossword")
    }
}



