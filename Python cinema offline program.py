from gurobipy import *
import sys

"""
Example of input format:

5
5
11101
11101
11101
00000
11111
1 2 4 2 1 0 1 3

In the last line (group size), each number is separated by a space!
"""

def get_input_from_file():

    file_name = input("Insert input file directory: ")
    f = open(file_name, "r")

    # store m and n:
    n = int(f.readline())
    m = int(f.readline())
    cinema = {}
    people = []

    # store the layout of the cinema in a dictionary:
    for i in range(1,n+1):
        l = f.readline()
        for j in range(1, m+1):
            cinema[(i, j)] = int(l[j-1])

    # store the group size in an array:
    last_line = f.readline()
    people = last_line.split()
    for i in range(0,8):
        people[i] = int(people[i])

    f.close()

    print('\n')

    return n, m, cinema, people


def get_input_from_keyboard():

    print('Insert input and press CTRL-D or CMD-D:')
    lines = sys.stdin.read().splitlines()

    # store m and n:
    n = int(lines[0])
    m = int(lines[1])
    cinema = {}
    people = []

    # store the layout of the cinema in a dictionary:
    for i in range(2, n+2):
        line = lines[i]
        for j in range(1, m+1):
            cinema[(i-1, j)] = int(line[j-1])

    # store the group size in an array:
    people = lines[-1].split()
    for i in range(0,8):
        people[i] = int(people[i])

    print('\n')

    return n, m, cinema, people


def choose_input_source():
    
    print("Input from a file or a keyboard?: ")
    print('1-file')
    print('2-keyboard')
    choice = int(input('Choice: '))

    if choice == 1:
        n, m, layout_cinema, group_size = get_input_from_file()

    elif choice == 2:
        n, m, layout_cinema, group_size = get_input_from_keyboard()
    else:
        print('Invalid choice\n')
        exit(1)

    return n, m, layout_cinema, group_size


def print_solution(active_seats, layout_cinema, group_size, n, m, runtime, raw_active_seats, gap):

    # logic: if there's a 0 in the original layout than print a '0', if there's a 1 than check
    # whether there is seated a person or not. Is yes, print a 'x', if no print a '1'

    available_seats = 0
    total_people = 0
    print('\nCinema solution: ')
    for i in range(1, n+1):
        print('\n', end='')
        for j in range(1, m+1):
            if layout_cinema[(i, j)] == 0:
                print('0', end='')
            elif (i, j) in active_seats:
                print('x', end='')
                available_seats += 1
            else:
                print('1', end='')
                available_seats += 1

    # count for total people in input:
    for i in range(1,9):
        total_people += i * group_size[i-1]

    print('\n\nNumber of people seated:', len(active_seats))
    print('Runtime for the optimization:', round(runtime, 5), 'seconds')
    print('Gap from optimal solution:', round(gap, 6)*100, '%')

    print('\n\nDetailed solution:\n')
    print('Number of seats available:', available_seats)
    print('Number of total people in input:', total_people)
    print('Theoretical cinema saturation (with no 1.5 rule):', round(total_people/available_seats, 4)*100, '%')
    print('Actual cinema saturation:', round(len(active_seats)/available_seats, 4)*100, '%')
    print('\n')

    for i in range(1,9):
        number_seated = 0
        # computing the number of people seated for each size group of people:
        for j in range(0, len(raw_active_seats)):
            if (raw_active_seats[j])[2] == i:
                number_seated += 1
        print('Number of groups of', i, 'in input:', group_size[i-1], '->', group_size[i-1]*i, 'people  ---->  seated:', number_seated, 'people (' + str(int(number_seated/i)), 'groups)')


def presentation():

    print('\n--------------------------------------------------------------------------')
    print('Gurobi optimizer based on Python to solve the offline cinema problem')
    print('Software developed by the group "I Grandi", composed by: ')
    print('-Daniele Di Grandi')
    print('-Edo Mangelaars')
    print('-Matthijs Wolters')
    print('-Tijmen van den Pol')
    print('-Bernd van den Hoek')
    print('--------------------------------------------------------------------------\n')
    input('Press enter to continue.. ')


def print_message():

    print('\n--------------------------------------------------------------------------')
    print('Notice: you can stop the program whenever you want, and by doing so')
    print('the program will provide the best solution found until that moment.')
    print('If you wait until the end, the program will provide the optimal solution.')
    print('--------------------------------------------------------------------------\n')
    input('Press enter to continue.. ')


def interrupted_solution():

    time = float(input(('How much time (in seconds) do you want to wait for the solution?: ')))
    gap = float(input('What is the maximum gap accepted? (eg for 1% insert 0.01): '))

    return time, gap


def clean_variables(raw_active_seats):

    # this function remove the k index from all the active variables in format (i, j, k) leaving only (i, j)
    active_seats = []

    for (i, j, k) in raw_active_seats:
        active_seats.append((i, j))

    return active_seats


def run_model(n, m, layout_cinema, group_size, choice, time, gap):

    print('\n')
    N = [i for i in range (1,n+1)]
    M = [i for i in range (1, m+1)]
    K = [i for i in range (1,9)]

    # create the model:
    mdl = Model('CinemaOffline')

    # add the variables to the model:
    y = mdl.addVars(N, M, K, vtype=GRB.BINARY, name='y')
    x = mdl.addVars(N, M, K, vtype=GRB.BINARY, name='x')

    # set the objective of the model:
    mdl.setObjective(quicksum(k*x[i, j, k] for i in N for j in M for k in K), GRB.MAXIMIZE)

    # add all the constraints to the model:
    mdl.addConstrs(quicksum(y[i, j, k] for k in K) == 0 for i in N for j in M if layout_cinema.get((i, j)) == 0)  # A constraint
    mdl.addConstrs(x[i, j, k] <= y[i, j, k] for i in N for j in M for k in K)  # B constraint
    mdl.addConstrs(quicksum(y[i, j, k] for i in N for j in M) <= k * group_size[k - 1] for k in K)  # C constraint
    mdl.addConstrs(quicksum(x[i, j, k] for k in K) <= 1 for i in N for j in M)  # D1 constraint
    mdl.addConstrs(quicksum(y[i, j, k] for k in K) <= 1 for i in N for j in M)  # D2 constraint
    mdl.addConstrs(48 * (1 - quicksum(y[i, j, k] for k in K)) >= quicksum(y[i + 1, j, k] for k in K) + quicksum(y[i + 1, j + 1, k] for k in K) for i in range(1, 2) for j in range(1, 2))  # E1 constraint
    mdl.addConstrs(48 * (1 - quicksum(y[i, j, k] for k in K)) >= quicksum(y[i + 1, j, k] for k in K) + quicksum(y[i + 1, j - 1, k] for k in K) for i in range(1, 2) for j in range(m, m + 1))  # E2 constraint
    mdl.addConstrs(48 * (1 - quicksum(y[i, j, k] for k in K)) >= quicksum(y[i - 1, j, k] for k in K) + quicksum(y[i - 1, j + 1, k] for k in K) for i in range(n, n + 1) for j in range(1, 2))  # E3 constraint
    mdl.addConstrs(48 * (1 - quicksum(y[i, j, k] for k in K)) >= quicksum(y[i - 1, j, k] for k in K) + quicksum(y[i - 1, j - 1, k] for k in K) for i in range(n, n + 1) for j in range(m, m + 1))  # E4 constraint
    mdl.addConstrs(48 * (1 - quicksum(y[i, j, k] for k in K)) >= quicksum(y[i + 1, j, k] for k in K) + quicksum(y[i - 1, j, k] for k in K) + quicksum(y[i + 1, j + 1, k] for k in K) + quicksum(y[i - 1, j + 1, k] for k in K) for i in range(2, n) for j in range(1, 2))  # E5 constraint
    mdl.addConstrs(48 * (1 - quicksum(y[i, j, k] for k in K)) >= quicksum(y[i + 1, j, k] for k in K) + quicksum(y[i - 1, j, k] for k in K) + quicksum(y[i - 1, j - 1, k] for k in K) + quicksum(y[i + 1, j - 1, k] for k in K) for i in range(2, n) for j in range(m, m + 1))  # E6 constraint
    mdl.addConstrs(48 * (1 - quicksum(y[i, j, k] for k in K)) >= quicksum(y[i + 1, j, k] for k in K) + quicksum(y[i + 1, j + 1, k] for k in K) + quicksum(y[i + 1, j - 1, k] for k in K) for i in range(1, 2) for j in range(2, m))  # E7 constraint
    mdl.addConstrs(48 * (1 - quicksum(y[i, j, k] for k in K)) >= quicksum(y[i - 1, j, k] for k in K) + quicksum(y[i - 1, j - 1, k] for k in K) + quicksum(y[i - 1, j + 1, k] for k in K) for i in range(n, n + 1) for j in range(2, m))  # E8 constraint
    mdl.addConstrs(48 * (1 - quicksum(y[i, j, k] for k in K)) >= quicksum(y[i + 1, j, k] for k in K) + quicksum(y[i - 1, j, k] for k in K) + quicksum(y[i - 1, j - 1, k] for k in K) + quicksum(y[i + 1, j + 1, k] for k in K) + quicksum(y[i - 1, j + 1, k] for k in K) + quicksum(y[i + 1, j - 1, k] for k in K) for i in range(2, n) for j in range(2, m))  # E9 constraint

    # E10 constraint:
    for i in N:
        for k in K:
            for j in range(1, m - k + 1):
                if m - j - k > 0:
                    mdl.addConstr(16 * (1 - x[i, j, k]) >= quicksum(y[i, j + k, s] for s in K) + quicksum(y[i, j + k + 1, s] for s in K))
                else:
                    mdl.addConstr(16 * (1 - x[i, j, k]) >= quicksum(y[i, j + k, s] for s in K))

    mdl.addConstrs((k - 1) * x[i, j, k] <= quicksum(y[i, j + L, k] for L in range(1, k)) for i in N for j in range(1, m) for k in range(2, min(m + 2 - j, 9)))  # F constraint
    mdl.addConstrs(quicksum(x[i, j, k] for k in range(m - j + 2, 9)) == 0 for i in N for j in M)  # G constraint
    mdl.addConstrs((k - 1) * (1 - x[i, j, k]) >= quicksum(x[i, j + L, k] for L in range(1, k)) for i in N for j in range(1, m) for k in range(2, min(m + 2 - j, 9))) # H constraint

    # set time and gap parameters:
    if choice == 1:
        mdl.Params.TimeLimit = time
        mdl.Params.MIPGap = gap

    # start the optimization process:
    mdl.optimize()

    # see the results:
    variables = tuplelist([(i, j, k) for i in N for j in M for k in K])  # list of all the variables available, in format (i, j, k)
    raw_active_seats = [i for i in variables if y[i].X == 1]  # list with only the variables with value of 1, in format (i, j, k)
    active_seats = clean_variables(raw_active_seats)  # seats with people seated in format (i, j)

    return active_seats, raw_active_seats, mdl.Runtime, mdl.MIPGap


if __name__ == '__main__':

    presentation()

    print_message()

    choice = int(input('Do you want to set parameters like time limit or maximum gap? (1 = yes / 0 = no): '))

    if choice == 1:
        time, gap = interrupted_solution()
    else:
        time = 0
        gap = 0

    input('Press enter to begin the optimization.. ')
    print('\n')

    n, m, layout_cinema, group_size = choose_input_source()

    active_seats, raw_active_seats, runtime, true_gap = run_model(n, m, layout_cinema, group_size, choice, time, gap)

    print_solution(active_seats, layout_cinema, group_size, n, m, runtime, raw_active_seats, true_gap)
