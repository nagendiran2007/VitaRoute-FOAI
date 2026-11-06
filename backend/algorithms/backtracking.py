
def backtracking_solve(variables, domains, constraints):
    assignment = {}
    steps = 0

    def is_consistent(var, value, assignment):
        for other_var, other_value in assignment.items():
            if other_var == var:
                continue
            if not constraints.get((var, other_var), lambda a, b: True)(value, other_value):
                return False
        return True

    def select_unassigned_variable():
        unassigned = [v for v in variables if v not in assignment]
        if not unassigned:
            return None
        return min(unassigned, key=lambda v: len(domains[v]))

    def backtrack():
        nonlocal steps
        if len(assignment) == len(variables):
            return True
        var = select_unassigned_variable()
        if var is None:
            return True
        for value in list(domains[var]):
            steps += 1
            if is_consistent(var, value, assignment):
                assignment[var] = value
                if backtrack():
                    return True
                del assignment[var]
        return False

    solved = backtrack()
    return assignment, steps, solved
