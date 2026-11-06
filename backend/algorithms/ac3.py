from collections import deque


def ac3(variables, neighbors, constraints):
    queue = deque()
    for var in variables:
        for neighbor in neighbors.get(var, []):
            queue.append((var, neighbor))

    removed = 0
    while queue:
        xi, xj = queue.popleft()
        if revise(xi, xj, constraints, neighbors):
            domain_xi = constraints.get(xi, [])
            if not domain_xi:
                return constraints, removed, True
            for xk in neighbors.get(xi, []):
                if xk != xj:
                    queue.append((xk, xi))
        removed += 1
    return constraints, removed, False


def revise(xi, xj, constraints, neighbors):
    revised = False
    for value in list(constraints.get(xi, [])):
        if not any(
            compatible(value, candidate)
            for candidate in constraints.get(xj, [])
        ):
            constraints[xi].remove(value)
            revised = True
    return revised


def compatible(value, candidate):
    return value == candidate
