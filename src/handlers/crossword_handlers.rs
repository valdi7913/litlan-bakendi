use actix_web::{Responder, HttpResponse};
use crate::models::crossword::Crossword;
use chrono::{DateTime, Utc};


pub async fn get_crossword() -> impl Responder {
    let crossword = Crossword::new();
    match serde_json::to_string(&crossword) {
        Ok(data) => HttpResponse::Ok()
            .content_type("application/json")
            .body(data),
        Err(_) => HttpResponse::InternalServerError().body("Failed to serialize crossword")
    }
}

