// @generated automatically by Diesel CLI.

pub mod sql_types {
    #[derive(diesel::query_builder::QueryId, Clone, diesel::sql_types::SqlType)]
    #[diesel(postgres_type(name = "direction"))]
    pub struct Direction;
}

diesel::table! {
    cell (crossword_id, x_coord, y_coord) {
        crossword_id -> Int4,
        #[max_length = 1]
        value -> Varchar,
        is_blank -> Bool,
        x_coord -> Int4,
        y_coord -> Int4,
    }
}

diesel::table! {
    crossword (id) {
        id -> Int4,
        date -> Nullable<Date>,
        width -> Nullable<Int4>,
        height -> Nullable<Int4>,
    }
}

diesel::table! {
    use diesel::sql_types::*;
    use super::sql_types::Direction;

    hint (crossword_id, id) {
        crossword_id -> Int4,
        id -> Int4,
        x_coord -> Int4,
        y_coord -> Int4,
        direction -> Direction,
        #[max_length = 255]
        text -> Varchar,
    }
}

diesel::joinable!(cell -> crossword (crossword_id));
diesel::joinable!(hint -> crossword (crossword_id));

diesel::allow_tables_to_appear_in_same_query!(
    cell,
    crossword,
    hint,
);
