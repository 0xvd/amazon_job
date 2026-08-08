import ast

query = input("Enter your GraphQL Query: ")
query = ast.literal_eval(query)

print(query)