import asyncio
from datetime import datetime
from random import randint, shuffle
import marisa_trie
from generation.Database import Database
from generation.Crossword import Crossword

# Database connection details
DB_CONFIG = {
    "user": "postgres",
    "password": "postgres",
    "database": "litlandb",
    "host": "localhost",
    "port": 5432
}

def run_trie_test(trie, n, five_letter_words):
    random_indexes = [randint(0, len(five_letter_words)-1) for _ in range(n)]
    start = datetime.now()
    for r in random_indexes:
        random_word = five_letter_words[r]
        keys = len(trie.keys(random_word)) > 0
    end = datetime.now()
    return (end-start)

def bench_mark(trie, five_letter_words, number_of_doublings):
    n = 10
    for x in range(number_of_doublings):
        multiplier = 2**x
        elapsed_time = run_trie_test(trie, n*multiplier, five_letter_words)
        print(x, n*multiplier, elapsed_time)

async def main():
    # Connect to the database and get word list
    db = Database(DB_CONFIG)
    await db.connect()
    five_letter_words = await db.get_words_that_match("_____")
    trie = marisa_trie.Trie(five_letter_words)
    
    # Set up the crossword grid
    SIZE = 5
    crossword = Crossword(SIZE)
    
    # Icelandic alphabet
    icelandic_alphabet = ['A', 'Á', 'B', 'D', 'Ð', 'E', 'É', 'F', 'G', 'H', 'I', 'Í', 'J', 'K', 'L', 'M', 'N', 'O', 'Ó', 'P', 'R', 'S', 'T', 'U', 'Ú', 'V', 'X', 'Y', 'Ý', 'Þ', 'Æ', 'Ö']
    lower_icelandic_alphabet = [letter.lower() for letter in icelandic_alphabet]
    print(lower_icelandic_alphabet)
    
    # Option for requiring unique words
    UNIQUE = True
    # Maximum number of solutions to find
    MAX_SOLUTIONS = 10
    solutions = []
    
    def backtrack(pos=0):
        """Backtracking algorithm to fill the word square"""
        if pos == SIZE * SIZE:
            # We've filled the entire grid - check if solution is unique
            if UNIQUE:
                row_words = [crossword.get_word_on_axis(True, r) for r in range(SIZE)]
                col_words = [crossword.get_word_on_axis(False, c) for c in range(SIZE)]
                if len(set(row_words + col_words)) < SIZE * 2:
                    return False  # Not all words are unique
            
            # Valid solution found
            solutions.append([row[:] for row in crossword.board])
            print(f"Solution {len(solutions)}:")
            crossword.print_board()
            print()
            return len(solutions) >= MAX_SOLUTIONS
        
        row, col = pos // SIZE, pos % SIZE
 
        for letter in lower_icelandic_alphabet:
            # Try this letter
            crossword.set_letter_in_cell(letter, row, col)
            
            # Check if current row and column prefixes could lead to valid words
            row_prefix = crossword.get_word_on_axis(True, row)
            col_prefix = crossword.get_word_on_axis(False, col)
            
            # Use the trie to check if these prefixes could form valid words
            row_valid = len(trie.keys(row_prefix)) > 0
            col_valid = len(trie.keys(col_prefix)) > 0
            
            # If we have a complete row/column, check if it's a valid word
            if col == SIZE - 1:  # Complete row
                row_valid = row_prefix in five_letter_words
            
            if row == SIZE - 1:  # Complete column
                col_valid = col_prefix in five_letter_words
            
            # If both prefixes are valid, continue with next position
            if row_valid and col_valid:
                if backtrack(pos + 1):
                    return True
            
            # Backtrack by removing this letter
            crossword.set_letter_in_cell(" ", row, col)
        
        return False
    
    print("Starting word square generation...")
    start_time = datetime.now()
    backtrack(0)
    end_time = datetime.now()
    
    print(f"Search completed in {end_time - start_time}")
    if not solutions:
        print("No solutions found.")
    else:
        print(f"Saving {len(solutions)} solutions to the database...")
        crossword_ids = await db.insert_crossword(crossword, solutions)
        print(f"Saved {len(crossword_ids)} unique solutions.")
    
    await db.pool.close()  # Close the connection pool when done
    
if __name__ == "__main__":
    asyncio.run(main())