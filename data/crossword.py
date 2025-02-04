import random
import time
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
    
    async def get_words_that_match(self, pattern="_____"):
        query = "SELECT * FROM WORD WHERE text LIKE $1"
        async with self.pool.acquire() as conn:
            result = await conn.fetchrows(query, pattern)
            return result if result else None

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

    def reset_inverse_of_pattern(self,index, horizontal, pattern):
        if horizontal:
            for col,letter in enumerate(pattern):
                if letter == "_":
                    self.board[index][col] = " "
        else:
            for row,letter in enumerate(pattern):
                if letter == "_":
                    self.board[row][index] = " "
    

class CrosswordGenerator:
    def __init__(self, db, dimension=5):
        self.db = db
        self.crossword = Crossword(dimension)
        self.queue = []
        self.consecutive_backsteps = 0
        self.max_consecutive_backsteps = 2
        self.pattern = "_" * self.crossword.dimension
 
    async def generate(self):
        horizontal = random.choice([True, False])

        while len(self.queue) < 5:
            time.sleep(1)
            #todo random-ize-a áttina líka
            available_indecies = [
                i for i in range(self.crossword.dimension) if (i, horizontal) not in self.crossword.used_indices
            ]

            if not available_indecies:
                self.backtrack()
                continue

            index = random.choice(available_indecies)
            self.pattern = self.crossword.get_word_on_axis(horizontal, index)
            word = await self.db.get_random_word_that_matches(self.pattern)

            if not word:
                self.consecutive_backsteps+= 1
                if self.consecutive_backsteps > self.max_consecutive_backsteps:
                    self.backtrack()

                self.backtrack()
                continue

            self.crossword.set_word_on_axis(word, horizontal, index)
            self.queue.append((word, index, horizontal, self.pattern))
            print("Word: ",word, "Pattern")
            self.consecutive_backsteps = 0

            #Todo skoða að bæta við not horizontal check-i og sjá hvort öll þau pattern séu til, ef ekki backtrack-a

            horizontal = not horizontal
            self.pattern = self.crossword.get_word_on_axis(horizontal, index)
            self.crossword.print_board()
    
    # Skoða scoring function til að hámarka möguleg valin orð
    async def calculate_word_score(self, word, index, horizontal):
        score = 0
        self.crossword.set_word_on_axis(word,horizontal,index)
        for index in range(self.dimension):
            horizontal_pattern = self.crossword.get_word_on_axis(True, index)
            vertical_pattern = self.crossword.get_word_on_axis(False, index)

            horizontal_rows = await self.db.get_words_that_match(horizontal_pattern)
            vertical_rows = await self.db.get_words_that_match(vertical_pattern)

            if(horizontal_rows):
                score += len(horizontal_rows)

            if(vertical_rows):
                score += len(vertical_rows)
        
        self.backtrack()

        return score

    async def get_all_words_that_match(self):
        pass        

    async def select_next_word(self):
        pass

    def backtrack(self):
        if not self.queue:
            print("Backtracking failed: No words to remove")
            return
        
        word, index, horizontal, pattern = self.queue.pop()
        self.crossword.reset_inverse_of_pattern(index, horizontal, pattern)
        print(f"Backtracking: Removing {word} from {'horizontal' if horizontal else 'vertical'} {index}")
        self.crossword.used_indices.remove((index, horizontal))
        self.consecutive_backsteps = 0
        self.pattern = pattern


# Example usage
import asyncio

async def main():
    db = Database(DB_CONFIG)
    await db.connect()

    generator = CrosswordGenerator(db)
    await generator.generate()

asyncio.run(main())