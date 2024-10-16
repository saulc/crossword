import sys

from crossword import *

'''
    Cs4660 Ai. Fall 2024
    Saul Castro 10/12/24
    
    structure 1 and word set 2 work well.
    python generate.py data/structure1.txt data/words2.txt output.png
'''

class CrosswordCreator():

    def __init__(self, crossword):
        """
        Create new CSP crossword generate.
        """
        self.crossword = crossword
        self.domains = {
            var: self.crossword.words.copy()
            for var in self.crossword.variables
        }
        # to return order_domain_values
        self.odv = {}


    def letter_grid(self, assignment):
        """
        Return 2D array representing a given assignment.
        """
        letters = [
            [None for _ in range(self.crossword.width)]
            for _ in range(self.crossword.height)
        ]
        for variable, word in assignment.items():
            direction = variable.direction
            for k in range(len(word)):
                i = variable.i + (k if direction == Variable.DOWN else 0)
                j = variable.j + (k if direction == Variable.ACROSS else 0)
                letters[i][j] = word[k]
        return letters

    def print(self, assignment):
        """
        Print crossword assignment to the terminal.
        """
        letters = self.letter_grid(assignment)
        for i in range(self.crossword.height):
            for j in range(self.crossword.width):
                if self.crossword.structure[i][j]:
                    print(letters[i][j] or " ", end="")
                else:
                    print("█", end="")
            print()

    def save(self, assignment, filename):
        """
        Save crossword assignment to an image file.
        """
        from PIL import Image, ImageDraw, ImageFont
        cell_size = 100
        cell_border = 2
        interior_size = cell_size - 2 * cell_border
        letters = self.letter_grid(assignment)

        # Create a blank canvas
        img = Image.new(
            "RGBA",
            (self.crossword.width * cell_size,
             self.crossword.height * cell_size),
            "black"
        )
        font = ImageFont.truetype("assets/fonts/OpenSans-Regular.ttf", 80)
        draw = ImageDraw.Draw(img)

        for i in range(self.crossword.height):
            for j in range(self.crossword.width):

                rect = [
                    (j * cell_size + cell_border,
                     i * cell_size + cell_border),
                    ((j + 1) * cell_size - cell_border,
                     (i + 1) * cell_size - cell_border)
                ]
                if self.crossword.structure[i][j]:
                    draw.rectangle(rect, fill="white")
                    if letters[i][j]:
                        _, _, w, h = draw.textbbox((0, 0), letters[i][j], font=font)
                        draw.text(
                            (rect[0][0] + ((interior_size - w) / 2),
                             rect[0][1] + ((interior_size - h) / 2) - 10),
                            letters[i][j], fill="black", font=font
                        )

        img.save(filename)

    def solve(self):
        """
        Enforce node and arc consistency, and then solve the CSP.
        """
        self.enforce_node_consistency()
        self.ac3()
        return self.backtrack(dict())

    def enforce_node_consistency(self):
        """
        Update `self.domains` such that each variable is node-consistent.
        (Remove any values that are inconsistent with a variable's unary
         constraints; in this case, the length of the word.)
        """
        # print(self.domains)
        k = self.domains.keys()
        for i in k:
            # print(i)
            # l = type(i)
            l = i.length
            # print(l)
            words = self.domains.get(i)
            for w in self.domains.get(i).copy():
                if len(w) != l: words.remove(w)
            # print(self.domains.get(i))


    # check if value var overlaps with domain of y at point c
    def checkfit(self, var, y, c):
        # print('checkfit')
        # print('var: ' + var)
        r = False
        for w in self.domains[y]:
            # print(var, w, str(var[c[0]]) + ' ' + str(w[c[1]]))
            if var[c[0]] == w[c[1]]: 
                r = True
                return r
                    
        return r


    def findcross(self, a, b):
        # find the intersection between 2 variables
        # print('cross', a, b)
        if a == b : return None

        # if a.direction == b.direction: return None
        # use variable cells to find overlap if any and convert to indexes.
        for i in range(len(a.cells)):
            if a.cells[i] in b.cells:
                k = b.cells.index(a.cells[i])
                # print('cross at: ', a.cells[i], i, k)
                return (i, k)

        return  None


    def revise(self, x, y):
        """
        Make variable `x` arc consistent with variable `y`.
        To do so, remove values from `self.domains[x]` for which there is no
        possible corresponding value for `y` in `self.domains[y]`.

        Return True if a revision was made to the domain of `x`; return
        False if no revision was made.
        """
        # print('revise method starting!')
        # print(x)
        # print(y)
        n = self.crossword.neighbors(x)
        # print(n)
        # if y not in n: return False

        c = self.findcross(x, y)
        if c == None: return False 
        r = 0
        startd = len(self.domains[x])
        for i in self.domains[x].copy():
            if not self.checkfit(i, y, c):
                # print('found conflict')
                self.domains[x].remove(i)
            r = i
        endd = len(self.domains[x])
        dd = startd - endd
        if r != 0:
            self.odv[(x, r)] = dd
        else: self.odv[(x, r)] = 0
        # print('Changed domain of x by : ' + str(dd) + ' items')
        
        return dd > 0


    '''
    ac3 and revise psudo code from page 187 of the textbook.
    function AC-3(csp) 
    returns false if an inconsistency is found 
    and true otherwise queue←a queue of arcs, initially all the arcs in csp
    while queue is not empty do 
        (Xi, Xj)←POP(queue)
        if REVISE(csp, Xi, Xj) then
            if size of Di = 0 then return false
                for each Xk in Xi.NEIGHBORS - {Xj} do
                    add (Xk, Xi) to queue return true

    function REVISE(csp, Xi, Xj) 
    returns true iff we revise the domain of Xi revised ← false
    for each x in Di do
        if no value y in Dj allows (x,y) to satisfy the 
        constraint between Xi and Xj then delete x from Di
        revised ← true
    return revised
    '''

    def ac3(self, arcs=None):
        """
        Update `self.domains` such that each variable is arc consistent.
        If `arcs` is None, begin with initial list of all arcs in the problem.
        Otherwise, use `arcs` as the initial list of arcs to make consistent.

        Return True if arc consistency is enforced and no domains are empty;
        return False if one or more domains end up empty.
        """
        # print('ac3 starting.')
        q = []
        if arcs == None: 
            # print('no initial list')
            q = list(self.crossword.overlaps)
        else: q = arcs  

        # for i in q:
        #         print(i) 
        while len(q) > 0:
            c = q.pop(0)
            # print(c)
            if self.revise(c[0], c[1]):
                if len(self.domains[c[0]]) == 0: return False
                for n in self.crossword.neighbors(c[0]):
                    q.append((c[0], n))
                
        return True



    def assignment_complete(self, assignment):
        """
        Return True if `assignment` is complete (i.e., assigns a value to each
        crossword variable); return False otherwise.
        """
        k = self.domains.keys()
        for i in k:
            # print(i)
            if i not in assignment.keys():
                return False
        return True

    def consistent(self, assignment):
        """
        Return True if `assignment` is consistent (i.e., words fit in crossword
        puzzle without conflicting characters); return False otherwise.
        """
        a = len(assignment.values())
        s = len(set(assignment.values()))
        if a != s: 
            print('Assigment not unique.')
            return False

        # implicet check if the assignment conflits with its neighbors
        # structure1 words1 works without this check?
        for i in assignment.keys():
            # print(i)
            for n in self.crossword.neighbors(i):
                if n in assignment.keys():
                    # print('checking neighbors fit')
                    c = self.findcross(i,n)
                    # print('found cross',c)
                    if c != None:
                        a = assignment[i][c[0]]
                        b = assignment[n][c[1]]
                        # print(a, b)
                        if a != b: return False
        # print('consistent check: ', a, s)
        # no conflicts were found, assignment is consistent.
        return True

    def order_domain_values(self, var, assignment):
        """
        Return a list of values in the domain of `var`, in order by
        the number of values they rule out for neighboring variables.
        The first value in the list, for example, should be the one
        that rules out the fewest values among the neighbors of `var`.
        """
        # working without this fully implemented? #fails structure2
        # print("order_domain_values")
        # //just return some values for now
        # n = self.crossword.neighbors(var)
        # print(n)
        o = self.odv
        s = {}
        # print(var)
        # print(o)
        r = self.domains[var].copy()
        for i in r:
            if((var,i)) in o.keys():
                # print( i, o[ (var, i ) ] )
                s[(var, i)] = o[ (var, i) ]
            else: s[(var,i)] = 0
        s = sorted(s.items(), key= lambda item: item[1])
        # print(s)
        t = [ i[0][1] for i in s]

        # print(t)
        return t

    def select_unassigned_variable(self, assignment):
        """
        Return an unassigned variable not already part of `assignment`.
        Choose the variable with the minimum number of remaining values
        in its domain. If there is a tie, choose the variable with the highest
        degree. If there is a tie, any of the tied variables are acceptable
        return values.
        """
        # print("select_unassigned_variable")
        k = self.domains.keys()
        u = {}
        for i in k:
            if i not in assignment.keys():
                u[i] = len(self.domains[i])
        if len(u) < 1: return None
        # print(u)
        su = sorted(u.items(), key=lambda item: item[1])
        # print(su)
        return su[0][0]

    def backtrack(self, assignment):
        """
        Using Backtracking Search, take as input a partial assignment for the
        crossword and return a complete assignment if possible to do so.

        `assignment` is a mapping from variables (keys) to words (values).

        If no assignment is possible, return None.
        """
        print('backtrack starting...')
        ac = self.assignment_complete(assignment)
        acc = self.consistent(assignment)
        print('Assigment complete: ' + str(ac))
        print('Assigment consistent:', acc)
        if ac and acc: 
            print('Final Assigment.')
            for k in assignment.keys():
                print(k, assignment[k])
            return assignment

        v = self.select_unassigned_variable(assignment)
        # print(v) 
        for i in self.order_domain_values(v, assignment):
            print('Assigning value: ', i)
            
            assignment[v] = i
            d = {}
            if self.consistent(assignment):
                # n = self.crossword.neighbors(v)
                # nn = []
                # for k in n:
                #     nn.append( (k, v) )
                nn = [ (k,v) for k in self.crossword.neighbors(v) ]
                d = self.domains.copy()
                if self.ac3( nn ):
                    print('ac3 passed.')
                    res = self.backtrack(assignment)
                    if res != None: return res
                else:
                    print('ac3 failed: revert domain')
                    self.domains = d
            else: print('assignment not consistent')
            print('reverting assignment.')
            assignment.pop(v, None)
           

        return None

    '''
    backtacking psudocode from textbook p192.

    function BACKTRACKING-SEARCH(csp) 
    returns a solution or failure return BACKTRACK(csp,{})

    function BACKTRACK(csp, assignment) returns a solution or failure
    if assignment is complete then return assignment
    var ← SELECT-UNASSIGNED-VARIABLE(csp, assignment)
    for each value in ORDER-DOMAIN-VALUES(csp, var, assignment) do
        if value is consistent with assignment then
            add {var = value} to assignment 
            inferences←INFERENCE(csp,var,assignment) 
            if inferences ̸= failure then
                add inferences to csp
                result←BACKTRACK(csp,assignment) 
                if result ̸= failure then return result 
                remove inferences from csp
            remove {var = value} from assignment 
        return failure
    '''

def main():

    # Check usage
    if len(sys.argv) not in [3, 4]:
        sys.exit("Usage: python generate.py structure words [output]")

    # Parse command-line arguments
    structure = sys.argv[1]
    words = sys.argv[2]
    output = sys.argv[3] if len(sys.argv) == 4 else None

    # Generate crossword
    crossword = Crossword(structure, words)
    creator = CrosswordCreator(crossword)
    assignment = creator.solve()

    # Print result
    if assignment is None:
        print("No solution.")
    else:
        creator.print(assignment)
        if output:
            creator.save(assignment, output)


if __name__ == "__main__":
    main()
