import asyncpg
from datetime import datetime

class Database:
    def __init__(self, db_config):
        self.db_config = db_config
        self.pool = None

    async def connect(self):
        self.pool = await asyncpg.create_pool(**self.db_config)

    async def word_exists(self, word):
        query = "SELECT * FROM WORD WHERE text = $1"
        async with self.pool.acquire() as conn:
            result = await conn.fetch(query, word)
            return len(result) > 0
    
    async def get_words_that_match(self, pattern="_____"):
        query = "SELECT * FROM WORD WHERE text LIKE $1"
        async with self.pool.acquire() as conn:
            result = await conn.fetch(query, pattern)
            newresult = [row["text"] for row in result]
            return newresult

    async def get_random_word_that_matches(self, pattern = "____"):
        query = "SELECT * FROM WORD WHERE text LIKE $1 ORDER BY RANDOM() LIMIT 1"
        async with self.pool.acquire() as conn:
            result = await conn.fetchrow(query, pattern)
            return result['text'] if result else None

    async def insert_crossword(self, crossword, solutions=None):
        """
        Insert crossword solutions into the database
        
        Args:
            crossword: Crossword object containing the board
            solutions: List of 2D solution boards (optional, uses current crossword.board if None)
        
        Returns:
            List of inserted crossword IDs
        """
        inserted_ids = []
        
        # Use current crossword board if no solutions provided
        if solutions is None:
            solutions = [crossword.board]
        
        # Get current date
        current_date = datetime.now().date()
        
        for solution in solutions:
            # Check if this crossword solution already exists in the database
            is_duplicate = await self._check_duplicate_crossword(solution, crossword.dimension)
            if is_duplicate:
                print("Skipping duplicate crossword solution")
                continue
            
            # Start a transaction
            async with self.pool.acquire() as conn:
                async with conn.transaction():
                    # Insert the crossword
                    crossword_id = await conn.fetchval(
                        "INSERT INTO crossword (date, width, height) VALUES ($1, $2, $3) RETURNING id",
                        current_date, crossword.dimension, crossword.dimension
                    )
                    
                    # Insert all cells
                    cell_values = []
                    for y in range(crossword.dimension):
                        for x in range(crossword.dimension):
                            value = solution[y][x] if isinstance(solution[0][0], str) else solution[y][x]
                            is_blank = value == " "
                            cell_values.append((crossword_id, value, is_blank, x, y))
                    
                    # Use batch insert for cells
                    await conn.executemany(
                        "INSERT INTO cell (crossword_id, value, is_blank, x_coord, y_coord) VALUES ($1, $2, $3, $4, $5)",
                        cell_values
                    )
                    
                    # Generate and insert hints
                    hint_values = []
                    
                    # Get word definitions from the database
                    h_words = []
                    v_words = []
                    for i in range(crossword.dimension):
                        h_word = "".join(solution[i][j] for j in range(crossword.dimension) if solution[i][j] != " ")
                        v_word = "".join(solution[j][i] for j in range(crossword.dimension) if solution[j][i] != " ")
                        h_words.append(h_word)
                        v_words.append(v_word)
                    
                    # Fetch definitions for all words at once
                    all_words = h_words + v_words
                    definitions = await self._get_word_definitions(all_words)
                    
                    # Create horizontal hints
                    for y in range(crossword.dimension):
                        word = h_words[y]
                        if word:
                            hint_text = definitions.get(word, f"Definition for {word}")
                            hint_values.append((crossword_id, 0, y, 'Horizontal', hint_text))
                    
                    # Create vertical hints
                    for x in range(crossword.dimension):
                        word = v_words[x]
                        if word:
                            hint_text = definitions.get(word, f"Definition for {word}")
                            hint_values.append((crossword_id, x, 0, 'Vertical', hint_text))
                    
                    # Insert hints
                    await conn.executemany(
                        "INSERT INTO hint (crossword_id, x_coord, y_coord, direction, text) VALUES ($1, $2, $3, $4, $5)",
                        hint_values
                    )
                    
                    inserted_ids.append(crossword_id)
                    print(f"Inserted crossword with ID: {crossword_id}")
        
        return inserted_ids

    async def _check_duplicate_crossword(self, board, dimension):
        """
        Check if a crossword with the same content already exists in the database
        
        Args:
            board: 2D array representing the crossword solution
            dimension: Size of the crossword
            
        Returns:
            bool: True if duplicate found, False otherwise
        """
        # Extract all words from the crossword (horizontal and vertical)
        h_words = []
        v_words = []
        
        for i in range(dimension):
            h_word = "".join(board[i][j] for j in range(dimension) if board[i][j] != " ")
            v_word = "".join(board[j][i] for j in range(dimension) if board[j][i] != " ")
            h_words.append(h_word)
            v_words.append(v_word)
        
        # Sort words to create a unique signature
        all_words = sorted(h_words + v_words)
        signature = ",".join(all_words)
        
        # Query to find crosswords with same dimensions
        async with self.pool.acquire() as conn:
            # Get all crosswords with the same dimensions
            crossword_ids = await conn.fetch(
                "SELECT id FROM crossword WHERE width = $1 AND height = $2",
                dimension, dimension
            )
            
            for record in crossword_ids:
                crossword_id = record['id']
                
                # Get all cells for this crossword
                cells = await conn.fetch(
                    "SELECT x_coord, y_coord, value FROM cell WHERE crossword_id = $1 ORDER BY y_coord, x_coord",
                    crossword_id
                )
                
                # Reconstruct the board
                existing_board = [[" " for _ in range(dimension)] for _ in range(dimension)]
                for cell in cells:
                    existing_board[cell['y_coord']][cell['x_coord']] = cell['value']
                
                # Extract words
                existing_h_words = []
                existing_v_words = []
                for i in range(dimension):
                    h_word = "".join(existing_board[i][j] for j in range(dimension) if existing_board[i][j] != " ")
                    v_word = "".join(existing_board[j][i] for j in range(dimension) if existing_board[j][i] != " ")
                    existing_h_words.append(h_word)
                    existing_v_words.append(v_word)
                
                # Create signature
                existing_signature = ",".join(sorted(existing_h_words + existing_v_words))
                
                # Check if signatures match
                if signature == existing_signature:
                    return True
        
        return False

    async def _get_word_definitions(self, words):
        """
        Get definitions for a list of words
        
        Args:
            words: List of words to get definitions for
            
        Returns:
            Dict mapping words to their definitions
        """
        result = {}
        
        if not words:
            return result
            
        # Create placeholders for SQL query
        placeholders = ",".join(f"${i+1}" for i in range(len(words)))
        
        async with self.pool.acquire() as conn:
            # Get definitions for all words at once
            rows = await conn.fetch(
                f"SELECT text, definition FROM word WHERE text = ANY($1::text[])",
                words
            )
            
            for row in rows:
                result[row['text']] = row['definition']
        
        return result