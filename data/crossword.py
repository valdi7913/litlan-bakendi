import copy
import random
import asyncpg

# Database connection details
DB_CONFIG = {
    "user": "postgres",
    "password": "postgres",
    "database": "litlandb",
    "host": "localhost",  # e.g., "localhost" or an IP address
    "port": 5432  # Default PostgreSQL port
}

class Database:
    def __init__(self, db_config):
        self.db_config = db_config
        self.pool = None

    async def connect(self):
        self.pool = await asyncpg.create_pool(**self.db_config)

    async def word_exists(self, word):
        query = "SELECT * FROM WORD WHERE text = $1"
        async with self.pool.acquire() as conn:
            result = await conn.fetch()
    
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


class Crossword:

    def __init__(self, dimension):
        self.dimension = dimension
        self.board = []
        for _ in range(dimension):
            row = []
            for _ in range(dimension):
                row.append(" ")
            self.board.append(row)
        self.used_indices = set()

    def print_board(self):
        for i in range(self.dimension):
            print(self.dimension * "+---", end="+\n")
            print("|", end="")
            for j in range(self.dimension):
                print("",self.board[i][j], end=" |")
            print()
        print(self.dimension * "+---", end="+\n")

    def set_word_on_axis(self, word, horizontal, index):
        if(horizontal):
            for col in range(self.dimension):
                self.board[index][col] = word[col]
        else:
            for row in range(self.dimension):
                self.board[row][index] = word[row]
        self.used_indices.add((index, horizontal))

    def get_word_on_axis(self, horizontal, index):
        word = ""
        if(horizontal):
            for col in range(self.dimension):
                word += self.board[index][col]
        else:
            for row in range(self.dimension):
                word += self.board[row][index]
        word = word.replace(' ', "_")
        return word

    def reset_inverse_of_pattern(self, index, horizontal, pattern):
        if horizontal:
            for col in range(self.dimension):
                self.board[index][col] = " "
        else:
            for row in range(self.dimension):
                self.board[row][index] = " "
    

class CrosswordGenerator:
    def __init__(self, db, dimension=5):
        self.db = db
        self.crossword = Crossword(dimension)
        self.queue = []
        self.consecutive_backsteps = 0
        self.max_consecutive_backsteps = 2
        self.ind = 0
 
    async def generate(self):
        horizontal = random.choice([True, False])
        pattern = "_" * self.crossword.dimension

        while len(self.queue) < 8:
            available_indices = [
                i for i in range(self.crossword.dimension) if (i, horizontal) not in self.crossword.used_indices
            ]

            if not available_indices:
                self.backtrack()
                continue

            index = random.choice(available_indices)
            word = ""
            if len(self.queue) == 0:
                word = await self.db.get_random_word_that_matches(pattern)
                print("Selected random word:", word)
            else: 
                (score, word, index, horizontal) = await self.select_next_word()
                if score == 0:
                    print("word has score 0 backtracking")
                    self.backtrack()
                    continue
                print("Selected best word:", word)

            if not word:
                self.consecutive_backsteps += 1
                if self.consecutive_backsteps > self.max_consecutive_backsteps:
                    self.backtrack()

                self.backtrack()
                continue

            pattern = self.crossword.get_word_on_axis(horizontal, index)
            self.crossword.set_word_on_axis(word, horizontal, index)
            self.queue.append((word, index, horizontal, pattern))
            print("Word: ", word, "Pattern")
            self.consecutive_backsteps = 0

            horizontal = not horizontal
            pattern = self.crossword.get_word_on_axis(horizontal, index)
            self.crossword.print_board()

        print(self.queue)

    async def lookahead_calculate_word_score(self, word, index, horizontal):
        # Simulate placing the word on the board
        next_board = copy.deepcopy(self.crossword)
        next_board.set_word_on_axis(word, horizontal, index)

        # Calculate the immediate score (original logic)
        immediate_score = 0
        for row in range(self.crossword.dimension):
            vertical_pattern = next_board.get_word_on_axis(False, row)
            if vertical_pattern.find("_") == -1:
                continue
            vertical_rows = await self.db.get_words_that_match(vertical_pattern)
            if len(vertical_rows) == 0:
                return 0  # Invalid move, no words match the pattern
            immediate_score += len(vertical_rows)

        for col in range(self.crossword.dimension):
            horizontal_pattern = next_board.get_word_on_axis(True, col)
            if horizontal_pattern.find("_") == -1:
                continue
            horizontal_rows = await self.db.get_words_that_match(horizontal_pattern)
            if len(horizontal_rows) == 0:
                return 0  # Invalid move, no words match the pattern
            immediate_score += len(horizontal_rows)

        # Lookahead: Evaluate the maximum number of valid words after two moves
        lookahead_score = 0
        for next_index in range(self.crossword.dimension):
            for next_horizontal in [True, False]:
                if (next_index, next_horizontal) in next_board.used_indices:
                    continue  # Skip already used indices

                # Get the pattern for the next move
                next_pattern = next_board.get_word_on_axis(next_horizontal, next_index)
                if next_pattern.find("_") == -1:
                    continue  # Skip fully filled patterns

                # Get all words that match the next pattern
                next_words = await self.db.get_words_that_match(next_pattern)
                if not next_words:
                    continue  # No valid words for this pattern

                # Simulate placing each possible word for the next move
                max_next_move_score = 0
                for next_word in next_words:
                    # Create a new board for the second move
                    second_move_board = copy.deepcopy(next_board)
                    second_move_board.set_word_on_axis(next_word, next_horizontal, next_index)

                    # Calculate the score for the second move
                    second_move_score = 0
                    for row in range(self.crossword.dimension):
                        vertical_pattern = second_move_board.get_word_on_axis(False, row)
                        if vertical_pattern.find("_") == -1:
                            continue
                        vertical_rows = await self.db.get_words_that_match(vertical_pattern)
                        second_move_score += len(vertical_rows)

                    for col in range(self.crossword.dimension):
                        horizontal_pattern = second_move_board.get_word_on_axis(True, col)
                        if horizontal_pattern.find("_") == -1:
                            continue
                        horizontal_rows = await self.db.get_words_that_match(horizontal_pattern)
                        second_move_score += len(horizontal_rows)

                    # Track the maximum score for the second move
                    if second_move_score > max_next_move_score:
                        max_next_move_score = second_move_score

                # Add the maximum second move score to the lookahead score
                lookahead_score += max_next_move_score

        # Combine immediate score and lookahead score
        total_score = immediate_score + lookahead_score
        return total_score
    
    async def calculate_word_score(self, word, index, horizontal):
        score = 0
        nextBoard = copy.deepcopy(self.crossword)
        nextBoard.set_word_on_axis(word, horizontal, index)

        for row in range(self.crossword.dimension):
            vertical_pattern = nextBoard.get_word_on_axis(False, row)

            if vertical_pattern.find("_") == -1:
                continue            
            
            vertical_rows = await self.db.get_words_that_match(vertical_pattern)

            if len(vertical_rows) == 0:
                return 0

            score += len(vertical_rows) 
            
        for col in range(self.crossword.dimension):
            horizontal_pattern = nextBoard.get_word_on_axis(True, col)
            if horizontal_pattern.find("_") == -1:
                continue            

            horizontal_rows = await self.db.get_words_that_match(horizontal_pattern)

            if len(horizontal_rows) == 0: 
                return 0

            score += len(horizontal_rows)

        return score

    async def get_all_valid_words(self):
        all_words_that_match = []
        for index in range(self.crossword.dimension):
            horizontal_pattern = self.crossword.get_word_on_axis(True, index)
            horizontal_words = await self.db.get_words_that_match(horizontal_pattern)
            hword = [(horizontal_word, index, True) for horizontal_word in horizontal_words]

            all_words_that_match.extend(hword)

            vertical_pattern = self.crossword.get_word_on_axis(False, index)
            vertical_words = await self.db.get_words_that_match(vertical_pattern)
            vword = [(vertical_word, index, False) for vertical_word in vertical_words]

            all_words_that_match.extend(vword)
        
        for (usedWord, _, _, _) in self.queue:
            print(f"removing {usedWord} from list")
            print(all_words_that_match[0][0])
            all_words_that_match = list(filter(lambda x: x[0] != usedWord, all_words_that_match))

        return random.choices(all_words_that_match, k=100)

    async def select_next_word(self):
        all_words = await self.get_all_valid_words()
        print(f"Ranking {len(all_words)} valid words")
        scored_words = []
        for (word, index, horizontal) in all_words:
            score = await self.calculate_word_score(word, index, horizontal)
            scored_words.append((score, word, index, horizontal))

        scored_words.sort(reverse=True, key=lambda x: x[0])
 
        N = 1
        topN = scored_words[0:N]
        print(f"Best {topN}", topN)
        return random.choice(topN) if scored_words else None

    def backtrack(self):
        if not self.queue:
            print("Backtracking failed: No words to remove")
            return
        
        word, index, horizontal, pattern = self.queue.pop()
        self.crossword.reset_inverse_of_pattern(index, horizontal, pattern)
        print(f"Backtracking: Removing {word} from {'horizontal' if horizontal else 'vertical'} {index}")
        self.crossword.used_indices.remove((index, horizontal))
        self.consecutive_backsteps = 0


# Example usage
import asyncio

async def main():
    db = Database(DB_CONFIG)
    await db.connect()

    generator = CrosswordGenerator(db)
    await generator.generate()
    await db.pool.close()

asyncio.run(main())