class MatrixOperations:

    def determinant(root_matrix):
        # node is array of [determinant, root node, child_index, parent]
        node = [0, root_matrix, 0, None]

        while True:
            matrix = node[1]
            parent = node[3]
            sign = 1 if parent is None or parent[2] % 2 == 0 else -1

            # If we've reached max recursion depth
            if len(node[1]) == 1:
                parent[0] += sign * parent[1][0][parent[2]] * matrix[0][0]
                parent[2] += 1
                node = parent
                continue

            size = len(matrix)
            # If we've already visited all children for this node
            if node[2] == size:
                if parent is None:
                    break
                parent[0] += sign * parent[1][0][parent[2]] * node[0]
                parent[2] += 1

            if node[2] == size:
                node = node[3]
                continue

            # If we haven't already visited all children for this node
            smaller_matrix = [m[:node[2]] + m[node[2]+1:] for m in matrix[1:]]
            node = [0, smaller_matrix, 0, node]

        return node[0]
