#!/usr/bin/python

import os
import sys
import re
import random

#### from solver import * list.

__all__ = [ 'bin9', 'bit_count', 'puzzle_list',
            'row_list', 'col_list', 'reg_list', 'box_list',
            'read_puzzle_file', 'select_puzzle', 'print_puzzle',
            'clear_board', 'reset_all_states',
            'find_solution', 'get_progress_counts',
            'update_all_hints', 'update_all_states',
            'solve_all_puzzles' ]

#### Importable variable names.

puzzle_list = []                        # Puzzle list

row_list = []                           # List of Boxes by row
col_list = []                           # List of Boxes by column
reg_list = []                           # List of Boxes by region

box_list = []                           # Complete list of Boxes

bit_count = []                          # Bit count array

#### Creates a 9 digit binary number string from an integer parameter.

def bin9(x):
    s = ""
    for i in range(9):
        s += ((x << i) & 0x100) and "1" or "0"
    return s

#### Form the bit_count list where bit_count[n] contains the number
#### of set bits in any number 0 to 511.  For example bit_count[6] == 2
#### because there are 2 bits set in the number 6.

for n in range(512):
    count = 0
    for i in range(9):
        if (n>>i) & 1:
            count += 1
            
    bit_count.append(count)
        
#### Defines a Box on the Board which may hold a digit 1..9.

class Box:

    #### Initializes a Box object
    
    def __init__(self, row, col):
        reg = 3 * (row//3) + (col//3)
        
        self.row = row                  # Box row number
        self.col = col                  # Box column number
        self.reg = reg                  # Box region number
        
        row_list[self.row].append(self)
        col_list[self.col].append(self)
        reg_list[self.reg].append(self)
        box_list.append(self)

        self.start = 0                  # Start number (if non-zero)
        self.choice = 0                 # Choice number (if non-zero)
        self.solution = 0               # Final solution (if known)
        self.maybe  = 0
        self.user = 0x1ff               # User state values
        self.state = 0x1ff              # Current state
        self.hint  = 0x1ff              # Current hint

    #### Prints an instance for debugging.

    def print_instance(self):
        sys.stdout.write(
            "Box: row=%d  col=%d  reg=%d  " %
            (self.row, self.col, self.reg))
        
        sys.stdout.write(
            "start=%d  choice=%d  solution=%d  " %
            (self.start, self.choice, self.solution))

        sys.stdout.write(
            "user=%09s  state=%09s  hint=%09s\n" %
            (bin9(self.user), bin9(self.state), bin9(self.hint)))

#### Clears the game.
        
def clear_board():

    row_list[:] = [[] for i in range(9)]
    col_list[:] = [[] for i in range(9)]
    reg_list[:] = [[] for i in range(9)]

    box_list[:] = []

#### Creates the board.

def create_board():

    # Create 81 Boxes filling the rows, columns and regions.

    for row in range(9):
        for col in range(9):
            Box(row, col)

#### Reads in puzzles from a specified file.

def read_puzzle_file(filename):

    input = open(filename, "r")
    puzzle_list[:] = input.readlines()

    for line in puzzle_list:
        assert(len(line) == 82)

#### Selects a puzzle to play.
        
def select_puzzle(number = -1):

    for i in range(9):
        assert(len(row_list[i]) == 9)
        assert(len(col_list[i]) == 9)
        assert(len(reg_list[i]) == 9)

    assert(len(box_list) == 81)

    if number < 0:
        number = random.randint(0, len(puzzle_list)-1)
                            
    puzzle = puzzle_list[number]

    for i in range(81):
        b = row_list[i/9][i%9]
        b.start = "123456789".find(puzzle[i]) + 1
        b.choice = 0
        b.user = 0x1ff

    reset_all_states()

    return number

#### Updates the failure, hint and state counts.
#### fail_count is the number of boxes w/o solutions.
#### state_count is the number of possibilities remaining in state variables.
#### hint_count is the number of possiblities remaining in hint variables.
        
def get_progress_counts():
    
    fail_count = 0
    state_count = -81
    hint_count = -81
    
    for b in box_list:
        if b.state == 0 or b.hint == 0:
            fail_count += 1
        state_count += bit_count[b.state]
        hint_count  += bit_count[b.hint]
    
    return (fail_count, state_count, hint_count)

#### Prints the entire puzzle.
        
def print_puzzle(comment):

    print
    print("========", comment)

    for r in range(9):

        if r == 3 or r == 6:
            sys.stdout.write(103*'-')
            sys.stdout.write("\n")

        for c in range(9):

            if c != 0:
                sys.stdout.write("  ")
            if c == 3 or c == 6:
                sys.stdout.write("|  ")

            b = row_list[r][c]
            for i in range(9):
                if (b.hint >> i) & 1:
                    sys.stdout.write(str(i+1))
                else:
                    sys.stdout.write(".")

        sys.stdout.write("\n")
        
    sys.stdout.write(" ")

    for i in range(81):
        if i % 9 == 0:
            print
        box_list[i].print_instance()

    (fail_count, state_count, hint_count) = get_progress_counts()

    print("fail_count:", fail_count, \
          "  state_count:", state_count, \
          "  hint_count:", hint_count)
    print
        
#### Reset the state and hint variables to discard any computations we
#### did on them.  After calling this procedure, state and hint variables
#### will show only the effect of the start and choice values, and the
#### the user bits.   Does not clear out the solution, however.

def reset_all_states():

    # Reset all states.
    
    for b in box_list:

        # Process starting position, final user choice, and set of
        # numbers the user has selected.

        if b.start != 0:
            b.state = 1 << (b.start-1)

        elif b.choice != 0:
            b.state = 1 << (b.choice-1)

        else:
            b.state = b.user

        b.hint = b.state

#### Update hints for one row, column, or region.
####
#### Hint levels can be 0 to 8.   For example hint_level 2 will look for
#### a set of two boxes that contain the same 2 set bits.  If such a set of
#### of boxes is found, those two bits will be eliminated from other boxes
#### in the same list.

hint_threshold = [ 999999, 999999, 3, 5, 7, 8, 6, 4, 2 ]

def update_hint(box, hint_level):
    
    if hint_level == 0:
        return

    # Do special case processing on boxes with less than
    # two state bits set. In the process, create a new list
    # of boxes with 2 or more bits set.

    dup = 0
    present = 0
    
    for b in box:
        if bit_count[b.state] == 1:
            dup |= b.state & present
            present |= b.state

    newbox = []
    for b in box:
        b.hint &= ~dup
        if bit_count[b.state] >= 2:
            b.hint &= ~present
            newbox.append(b)

    # Loop to update hint variables at the selected level.
    
    n = len(newbox)
    for boxset in range(1, 2**n - 1):

        boxcount = bit_count[boxset]

        if hint_level >= hint_threshold[boxcount]:

            # Find the union of the state variables in the
            # selected set of boxes.
            
            union = 0
            for s in range(n):
                if ((boxset >> s) & 1) != 0:
                    union |= newbox[s].state

            # If the union contains precisely "level" bits,
            # clear any corresponding set bits in all boxes
            # not in the set.
            
            if bit_count[union] == boxcount:
                for s in range(n):
                    if ((boxset >> s) & 1) == 0:
                        newbox[s].hint &= ~union

##### Update the hint variables at the selected hint level.  This includes
##### eliminating possibilities on each row, column and region.
        
def update_all_hints(hint_level):

    for group in (row_list, col_list, reg_list):
        for boxes in group:
            update_hint(boxes, hint_level)

##### Update the state variables to include all the computation done
##### on the hint variables.
        
def update_all_states():
    change = False

    for b in box_list:
        if b.state != b.hint:
            b.state = b.hint
            change = True

    return change

#### Attempts to find a solution without guessing.

def attempt_solution():

    while True:
        change = False
        for group in (row_list, col_list, reg_list):
            for boxes in group:
                update_hint(boxes, 8)
                for b in boxes:
                    if b.state != b.hint:
                        b.state = b.hint
                        change = True
        if not change:
            break

#### Searches for a solution from the current state.  If necessary,
#### makes one or more guesses and then calls itself recursively
#### to check for a solution, given the guess.

def search_for_solution():
    global solution_count

    # Attempt to find a solution without guessing.
    
    attempt_solution()

    (fail_count, state_count, hint_count) = get_progress_counts()

    if fail_count != 0:
        return False

    # If this is the first solution found, store the solution
    # path.

    if state_count == 0:
        if solution_count == 0:
            for b in box_list:
                assert(bit_count[b.state] == 1)
                for s in range(9):
                    if (b.state >> s) & 1:
                        b.solution = s+1
                        assert(b.start == 0 or b.start == b.solution)
                        break

        solution_count += 1
        return True

    # Find the first box with the smallest number of
    # possiblities.

    min_state = 10

    for b in box_list:
        n = bit_count[b.state]
        if n > 1 and min_state > n:
            min_hint = n
            box = b

    # Save the current state, so we can restore the
    # state after a bad guess.

    save_state = [b.state for b in box_list]

    # Loop to try different guesses in the selected box.

    possible = box.state
    found = False
    previous_count = solution_count

    while possible:

        # Guess one of the possible states, and remove
        # it from the list of remaining possible states.

        box.state = possible
        possible &= possible - 1
        box.state ^= possible
        box.hint = box.state

        # Now that the guess is made, call ourself recursively
        # to search for a solution.

        if search_for_solution():

            # Return success unless this Box is on the first
            # solution path down the tree.

            if previous_count != 0:
                possible = 0

            # If a previous solution was found for this Box,
            # then eliminate this solution by adding the first
            # solution to the start list.

            elif found:
                box.start = box.solution
                possible = 0

            found = True

        # Restore the game state.
            
        for i in range(81):
            b = box_list[i]
            b.state = b.hint = save_state[i]

    # Return success if a solution was found down the current path.

    return found

#### Finds a solution, if one exists.
#### If there are multiple solution, the start list is modified to
#### remove the extra solutions.

def find_solution():
    global solution_count
    solution_count = 0

    reset_all_states()

    search_for_solution()

    reset_all_states()

    return solution_count != 0

#### Solves all the puzzles in puzzle_list..

def solve_all_puzzles():

    clear_board()
    create_board()

    for n in range(len(puzzle_list)):
        print("Puzzle number: " + str(n))
        select_puzzle(n)
        find_solution()

        assert(solution_count >= 1)

        if solution_count > 1:
            count = solution_count
            find_solution()
            print("Solutions reduced from", count, "to", solution_count)
            assert(solution_count == 1)


#### Demo/Example routine to demonstrate the use of this module.

def demo():

    #### Read the puzzle file.

    if len(sys.argv) >= 2:
        read_puzzle_file(sys.argv[1])
    else:
        read_puzzle_file("puzzles.txt")

    #### Clear the board and select a puzzle.

    clear_board()
    create_board()

    if len(sys.argv) >= 3:
        n = select_puzzle(int(sys.argv[2]))
    else:
        n = select_puzzle()
    
    print("Puzzle Number", str(n))

    print_puzzle("Freshly loaded puzzle")

    #### Find the solution.

    find_solution()

    print_puzzle("Solution now filled in.")

    #### Show a simple hint.

    update_all_hints(1)

    print_puzzle("Hints level 1")

    #### Try a power hint.  Note this rarely makes a difference from
    #### the starting position.  It makes more of a difference when more
    #### boxes are chosen.

    update_all_hints(4)

    print_puzzle("Hints level 8")

    #### You can do a more powerful hint by using update all steps.  This
    #### propagates the hints into the states, so subsequent hints can
    #### use the results of earlier hints.

    update_all_hints(8)

    for n in range(2):
        update_all_states()
        update_all_hints(8)

    print_puzzle("Really advanced hint")

#### Run the demo and the solver only if running as Main.

if __name__ == '__main__':
    demo()
    #solve_all_puzzles()
