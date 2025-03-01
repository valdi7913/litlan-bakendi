class Crossword:
    def __init__(self, dimension):
        self.dimension = dimension
        self.board = []
        for _ in range(dimension):
            row = []
            for _ in range(dimension):
                row.append(" ")
            self.board.append(row)

    def print_board(self):
        for i in range(self.dimension):
            print(self.dimension * "+---", end="+\n")
            print("|", end="")
            for j in range(self.dimension):
                print("",self.board[i][j], end=" |")
            print()
        print(self.dimension * "+---", end="+\n")

    def set_letter_in_cell(self, letter, row, col):
        self.board[row][col] = letter

    def set_word_on_axis(self, word, horizontal, index):
        if(horizontal):
            for col in range(self.dimension):
                self.board[index][col] = word[col]
        else:
            for row in range(self.dimension):
                self.board[row][index] = word[row]

    def get_word_on_axis(self, horizontal, index):
        word = ""
        if(horizontal):
            for col in range(self.dimension):
                word += self.board[index][col]
        else:
            for row in range(self.dimension):
                word += self.board[row][index]
        return word.strip()

    def get_pattern_on_axis(self, horizontal, index):
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
    