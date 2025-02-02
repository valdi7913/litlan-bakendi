use serde::{Serialize};
use chrono::{DateTime, Utc};

#[derive(Serialize)]
pub struct Crossword {
    id: i32,
    date: DateTime::<Utc>,
    width: u8,
    height: u8,
}

impl Crossword {
    pub fn new() -> Self {
        Crossword {
            id: 1,
            date:chrono::Local::now().with_timezone(&Utc),
            width: 5u8,
            height: 5u8,
        }
    }
}

